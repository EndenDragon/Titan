# Titan
**Visit our website! [https://titanembeds.com/](https://titanembeds.com/) And get started *right away*!**

There was a time when Discord doesn't support embedding the chat on a webpage. But with Titan, you can! It is as simple as 1, 2, 3!
1. Invite the bot to your server (You must have "Manage Server" permissions)
2. Configure the embed to your liking (toggling guest users, etc)
3. Copy the iframe code and paste the line in your webpage!

## Features
- Guest users (a quick way to invite users who do not have a Discord account)
- Moderation Features (Kick & ban users by IP addresses, toggling guest users)
- Discord OAuth support. (Allows those who have a discord account to access the embed)
- Responsive material design! (Thanks materializecss!!)

## Installation
Would you like to run your own copy of Titan Embeds? There are two parts that integrate nicely together. The webapp (website) handles the frontend and communication with the database to retrieve server messages, etc. The discordbot (bot) handles the communcation
between Discord's websockets and pushing out the data to the database for the webapp. Check out the respective folder for their installation instructions. Titan is written in Python and requires **Python 3.6.8** at minimum to run.

Once you cloned the project, install the Python depends with `pip install -r requirements.txt`. Ensure that you are utilizing Python 3.6's pip.

If you happen to have a copy of Ubuntu on your server, you may head onto our [Ansible Playbooks](https://github.com/TitanEmbeds/ansible-playbooks) repository and perform a **near-to-automatic** installation of TitanEmbeds.

## Storage installation
### Database
To set up the database for it to work with the webapp and the discordbot, one must use **alembic** to *migrate* their databases to the current database state. To do so, please follow these instructions.
**PostgreSQL supports proper indexing and suitable for Titan needs. For this reason, Titan only supports using a PostgreSQL database.**
1. Install alembic with **Python 3.6's pip** `pip install alembic`
2. Change your directory to the webapp where the alembic files are located `cd webapp`
3. Clone `alembic.example.ini` into your own `alembic.ini` file to find and edit the following line `sqlalchemy.url` to equal your database uri. [See here](http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls) if you need help understanding how database uri works in SQLalchemy.
4. In your terminal, run `alembic upgrade head` to upgrade your database tables to the current version on git. As long as there are only *INFO* messages and no errors, you should be fine.
5. Check your database tables to see if they are created. If so, you have finished migrating your database! **Remember to run *Step 4* every now and then just in case if there are database updates.** (Presumably on every `git pull`).

### Redis
Titan also requires a Redis instance in order to function. There is no specific prerequisites before utilizing Titan with redis. Follow the official Redis [installation instructions](https://redis.io/topics/quickstart) to install and start redis.

## Join us!
Come and talk with us at our very own [Discord server](https://discord.gg/z4pdtuV)! We offer support too!

## Translate for us!
Visit us over at our [CrowdIn project](http://translate.titanembeds.com/) and teach Titan how to speak your language!

## Disclaimer
This project is never to be used as a replacement for Discord app. It is used in conjunction for a quick and dirty Discord embed for websites. Some uses are via shoutboxes, etc.

## Badges
### Upvote us on TOP.GG
[![DiscordBots.org](https://top.gg/api/widget/299403260031139840.png "Upvote us on TOP.GG!")](https://top.gg/bot/299403260031139840)
### We proudly test our embeds to ensure a cross browser compatibility
[![BrowserStack](https://i.imgur.com/nlMHPwl.png)](https://www.browserstack.com/)
