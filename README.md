# Paste Search Matrix Bot

A Matrix bot that allows users to search for terms on Pastebin.com, providing a quick and easy way to gather data from public pastes.

```
 __________                  __             __     ________             .___ 
 \______   \  ____    ____  |  | __  ____ _/  |_  /  _____/   ____    __| _/ 
  |       _/ /  _ \ _/ ___\ |  |/ /_/ __ \\   __\/   \  ___  /  _ \  / __ |  
  |    |   \(  <_> )\  \___ |    < \  ___/ |  |  \    \_\  \(  <_> )/ /_/ |  
  |____|_  / \____/  \___  >|__|_ \ \___  >|__|   \______  / \____/ \____ |  
         \/              \/      \/     \/               \/              \/
                                                          & NeedNotApply 🙃  
```

Created by [RocketGod](https://github.com/RocketGod-git)  
Modified for Matrix use by [NeedNotApply](https://github.com/neednotapply)  

## Installation

1. **Clone the Repository**

    ```bash
    git clone https://github.com/neednotapply/paste-search-matrix-bot.git
    cd paste-search-matrix-bot
    ```

2. **Install Required Libraries**

    ```bash
    pip install matrix-nio aiohttp
    ```

3. **Setup the Configuration**

    Edit the `config.json` file, replace `@your_bot_username:matrix.org` with your Matrix bot's username, replace `your_bot_password` with your Matrix bot's password and adjust the `homeserver_url` appropriately if the bot will not belong to the default `https://matrix.org` federation.

5. **Run the Bot**

    ```bashhttps://github.com/neednotapply
    python pastesearch.py
    ```

## Commands

- `!pastes [query]` - Search for a term on Pastebin.com and retrieve the top 20 results.

## Contributing

If you would like to contribute to the project, feel free to fork the repository and submit a pull request.

## License

This project is licensed under the [AGPL-3.0 license] See the [LICENSE](LICENSE) file for more details.

## Credits

- [RocketGod](https://github.com/RocketGod-git) for creating the bot.
- [Pastebin](https://pastebin.com/) for providing the data source.
- [psbdmp.ws](https://psbdmp.ws/) for the public API.

---

**Note**: Ensure you provide adequate documentation regarding the bot's permissions on Matrix and any rate limits or restrictions associated with the public API you're using. Users should be made aware of potential limitations.

![rocketgod_logo](https://github.com/RocketGod-git/shodanbot/assets/57732082/7929b554-0fba-4c2b-b22d-6772d23c4a18)
