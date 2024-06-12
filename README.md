# TG-Photos

TG-Photos is a bot that allows you to use Telegram as an alternative to Google Photos. With this bot, you'll be able to easily store and organize your photos and browse through them directly on Telegram.

## Features

- Unlimited photo storage
- Easy organization with tags
- Search for photos
- Direct access to your photos on Telegram

## How to use

### Requirements

docker & docker-compose

### Setup

1. clone this repository
2. copy ```.env.sample``` as ```.env```
3. create a bot in [@botFather](https://t.me/botFather) and take note of it Bot API Token
4. (optional) while in dialog with @botFather, add commands from ```commands.txt``` to your bot
5. create a telegram channel and take note of it's ID
6. fill ```botToken, chatId``` and ```username``` in ```.env``` respectfully
7. run ```docker build -t tgphotos:latest .``` and wait
8. run ```docker-compose up -d``` to start the container
9. go to your bot username and send ```/start``` (or press start) to see if it's working. If bot responds, it's running successfully

## Commands

The Telegram Google Photo Bot comes with a set of commands to help you organize and manage your photos. Here are the available commands:

- `/search` - search for photos by tags or dates
- `/searchlist` - same as search, but in list view
- `/upload` - upload a media
- `/taglist` - list all tags
- and other commands in commands.txt...

## Technical details

The TG-Photos is built using Python and the Telegram Bot API.
It uses an Telegram API and SQL database to store and retrieve photos from your specified channel.

## License

This project is licensed under the MIT License - [see the LICENSE for details.](https://radiquum.mit-license.org/)

## Contributing

Contributions are welcome! If you have any suggestions or improvements, feel free to create an issue or submit a pull request.
