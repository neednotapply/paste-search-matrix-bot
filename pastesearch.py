import json
import logging
import os
import aiohttp
import asyncio
from nio import AsyncClient, RoomMessageText, InviteMemberEvent, SendRetryError, UploadResponse

logging.basicConfig(level=logging.DEBUG)

def load_config():
    try:
        with open('config.json', 'r') as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        return None

class MatrixBotClient:
    def __init__(self, homeserver, user_id, password):
        self.client = AsyncClient(homeserver, user_id)
        self.password = password
        self.message_limit = 2000  # Adjust if needed for Matrix

    async def login(self):
        try:
            response = await self.client.login(self.password)
            if response and response.get("errcode"):
                logging.error(f"Failed to login: {response.get('error')}")
                return False
            logging.info(f"Logged in as {self.client.user_id}")
            return True
        except Exception as e:
            logging.error(f"Exception during login: {e}")
            return False

    async def run(self):
        if not await self.login():
            return

        # Register event callbacks
        self.client.add_event_callback(self.message_callback, RoomMessageText)
        self.client.add_event_callback(self.invite_callback, InviteMemberEvent)

        # Start syncing
        await self.client.sync_forever(timeout=30000)

    async def invite_callback(self, room, event):
        """Automatically join rooms when invited."""
        logging.info(f"Received invite for room {room.room_id}")
        try:
            await self.client.join(room.room_id)
            logging.info(f"Joined room {room.room_id}")
        except Exception as e:
            logging.error(f"Failed to join room {room.room_id}: {e}")

    async def message_callback(self, room, event):
        """Handle incoming messages."""
        if event.sender == self.client.user_id:
            return  # Ignore messages from ourselves

        message_content = event.body.strip()

        if message_content.startswith("!pastes"):
            # Extract the query from the message
            parts = message_content.split(maxsplit=1)
            if len(parts) < 2:
                await self.send_message(room.room_id, "Please provide a search query.")
                return
            query = parts[1]
            logging.info(f"Received !pastes command with query: {query} in room {room.room_id} from {event.sender}")
            await self.handle_pastes_command(room, query)

    async def send_message(self, room_id, message):
        try:
            await self.client.room_send(
                room_id=room_id,
                message_type="m.room.message",
                content={"msgtype": "m.text", "body": message}
            )
        except SendRetryError as e:
            logging.error(f"Failed to send message to {room_id}: {e}")

    async def send_split_messages(self, room_id, message):
        if not message.strip():
            logging.warning("Attempted to send an empty message.")
            return

        lines = message.split("\n")
        chunks = []
        current_chunk = ""

        for line in lines:
            if len(current_chunk) + len(line) + 1 > self.message_limit:
                chunks.append(current_chunk)
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"

        if current_chunk:
            chunks.append(current_chunk)

        if not chunks:
            logging.warning("No chunks generated from the message.")
            return

        for chunk in chunks:
            await self.send_message(room_id, chunk)

    async def fetch_psbdmp_data(self, search_term):
        """Fetch data from the psbdmp API for the given search term."""
        URL = f"https://psbdmp.ws/api/v3/search/{search_term}"

        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as response:
                response_text = await response.text()
                logging.debug(f"API Raw Response: {response_text}")

                if response.status != 200:
                    logging.error(f"API returned non-200 status code: {response.status}. Response text: {response_text}")
                    return None

                try:
                    data = json.loads(response_text)
                    return data
                except json.JSONDecodeError:
                    logging.error(f"Failed to decode API response. Response text: {response_text}")
                    return None

    async def send_via_bot(self, room_id, content: str, raw_data: str):
        """Send a message with a file attachment."""
        # Create a temporary file to store the content
        temp_filename = "temp_paste.txt"
        with open(temp_filename, 'w', encoding='utf-8') as f:
            f.write(raw_data)

        # Upload the file to the Matrix content repository
        try:
            response, _ = await self.client.upload(
                temp_filename,
                content_type="text/plain"
            )

            if isinstance(response, UploadResponse):
                mxc_url = response.content_uri

                # Send a message with the file
                await self.client.room_send(
                    room_id=room_id,
                    message_type="m.room.message",
                    content={
                        "msgtype": "m.file",
                        "body": "results.txt",
                        "url": mxc_url
                    }
                )
            else:
                logging.error(f"Failed to upload file: {response}")
        except Exception as e:
            logging.error(f"Failed to send file: {e}")

        # Clean up the temporary file
        os.remove(temp_filename)

    async def handle_errors(self, room_id, error_message=None):
        """Handle errors by sending a user-friendly message."""
        user_friendly_message = "An error occurred while processing your request. Please try again later."
        logging.error(f"Error: {error_message if error_message else 'Unknown error'}")
        if error_message:
            user_friendly_message += f"\n\nDetails: {error_message}"

        await self.send_message(room_id, user_friendly_message)

    async def handle_pastes_command(self, room, query):
        """Process the !pastes command."""
        try:
            data = await self.fetch_psbdmp_data(query)

            if not data:
                await self.send_message(room.room_id, "No data found for the given query.")
                return

            message = ""
            full_message = ""

            for idx, entry in enumerate(data):
                text_sample = entry['text'].split("\n", 3)
                initial_text = "\n".join(text_sample[:3]) if len(text_sample) > 3 else "\n".join(text_sample)

                formatted_data = (
                    f"id     : {entry['id']}\n"
                    f"tags   : {entry.get('tags', 'none')}\n"
                    f"length : {entry['length']}\n"
                    f"time   : {entry['time']}\n"
                    f"text   :\n\n{initial_text}\n\n"
                    f"link   : https://pastebin.com/{entry['id']}\n\n"
                )

                full_message += formatted_data  # Add every entry to full_message

                # Only add the first 20 entries to the message that will be directly shown
                if idx < 20:
                    message += formatted_data

            if not message:
                message = "No data found for the given query."

            await self.send_split_messages(room.room_id, f"Here are the top 20 results for {query}:")
            await self.send_split_messages(room.room_id, message)

            # Now send the full_message as a .txt file
            if full_message:
                await self.send_via_bot(room.room_id, "Here's the full formatted response:", full_message)

        except Exception as e:
            await self.handle_errors(room.room_id, str(e))

def run_matrix_bot(homeserver, user_id, password):
    bot = MatrixBotClient(homeserver, user_id, password)
    asyncio.get_event_loop().run_until_complete(bot.run())

if __name__ == "__main__":
    config = load_config()
    if config:
        homeserver = config.get("homeserver_url")
        user_id = config.get("user_id")
        password = config.get("password")
        run_matrix_bot(homeserver, user_id, password)
