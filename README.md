# GitHub Push Notifications (Telegram Bot)

## Use it

Hosted by NIPE-SYSTEMS: https://t.me/nipe_systems_github_bot

Feel free to host your own instance.

## Installation & Usage

1. Install packages via `pip install -r requirements.txt` (you may want to use a virtual environment)
2. Register your instance at the [Telegram Bot API](https://core.telegram.org/bots#3-how-do-i-create-a-bot)
3. Setup your `config.yml` (see below)
4. Run the following command:

```bash
python bot.py config.yml
```

5. Run `/start` command in a chat with the bot. It will instruct you what to do.

Or use docker:

## Installation with Docker

### Build image

See https://github.com/NIPE-SYSTEMS/github-bot/blob/master/build.sh or:

```bash
docker build -t github-bot .
```

### Run container

See https://github.com/NIPE-SYSTEMS/github-bot/blob/master/enable.sh or for example:

```bash
docker run --detach --restart=always --name github-bot \
    -v /root/github-bot/config.yml:/app/config.yml \
    -p 8080:8080 github-bot
```

Adjust the path to the `config.yml`.

## `config.yml`

The file `config.yml` holds some settings for the bot. For example the bot token (via the [Telegram Bot API](https://core.telegram.org/bots#3-how-do-i-create-a-bot)) or the base URL. The base URL is used for the generation of links for webhooks.

The `config.yml` may be written automatically by the bot since it holds the registered chats (like a simple database). Therefore all comments or manual formatting may be broken if the bot writes the file.

Example YAML file:

```yaml
github-bot:
  baseurl: https://example.com/{uuid}
  token: 012345678:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi
  chats:
    12345678-1234-1234-1234-1234567890ab: 123456789
    12345678-1234-1234-1234-1234567890ab: 123456789
```

The `baseurl` field needs a `{uuid}` wildcard in the URL. To start with no chats you may want to set the `chats` field to `chats: {}`.
