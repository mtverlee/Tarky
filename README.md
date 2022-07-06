# Tarky

![Bot](https://github.com/mtverlee/Tarky/blob/master/img/icon.png?raw=true)

A simple bot to automatically post Escape from Tarkov patch notes in a Discord server.

## Installation

### Easy (Invite)

- [Invite](https://discord.com/api/oauth2/authorize?client_id=992125091204837398&permissions=326417770496&scope=bot)
- Run `/tarkychannel <channelID>` to add your channel or thread to the bot. This channel will get updates as patch notes become available.

### Hard (Self-host)

- Set up a Heroku project and set the `DISCORD_TOKEN` environment variable for your server.
- Add a Heroku Postgres resource to the project you just created and set your `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DATABASE` environment variables accordingly.
- Run `python3 setup.py` using the same local environment variables to set up the database tables.
- Run `/tarkychannel <channelID>` to add your channel or thread to the bot. This channel will get updates as patch notes become available.
- Deploy the project!

## Usage

- `/tarkyadd <channelID>` to add a channel to post patch notes to.
- `/tarkyremove <channelID>` to remove a channel that is recieving patch notes.
- `/tarkynews` to get a link to Escape from Tarkov news.
- `/tarkylast` to get a link to the most recent patch note.
