# Gamma
A multipurpose Discord bot written in Python.

### Modules
Here's a list of currently running modules:

- Moderation
- Auto Moderation
- Information
- Miscellaneous
- Auto Response + Custom Responses
- Auto Role / Self Assignable Roles
- Logging
- Welcome Messages
- Music
- Economy
- Tags
- Custom Commands

You can view each of the modules below.

## Installation
If you wish to use Gamma as a personal bot without using
the official Gamma, you can download this Github repo and
install it yourself. Before running the `main.py` file,
make sure to download the `requirements.txt` by doing the
following:

> If Windows:
```
py -m pip install -r requirements.txt
```
> If Linux:
```
pip3 install -r requirements.txt
```
(Sorry Mac OS users I have no idea how to use it)

## Extra Links
Invite Gamma to your server:
[Here](https://discordapp.com/api/oauth2/authorize?client_id=478437101122224128&permissions=8&scope=bot)

Join Gamma's **official** support server: [Here](https://discordapp.com/invite/JBQ2BEa)

## Modules and Commands
Click a module name to view  detailed information about the
commands.

#### Moderation
- Kick
- Ban
- Soft ban
- Purge
- Warn
- Mute
- Unmute
- Unban
- Blacklist

#### Information
- Role Information
- Guild Information
- User Information
- All Roles
- User / Bot Count
- Bot Statistics
- Source Code

#### Miscellaneous
- Feedback
- Invite
- Support
- Ping
- Say / Echo
- Trello / To do
- Cat Fact

#### Auto Response
- Channel Blacklist
- User Blacklist (self)
- (Bot Owner) Guild Blacklist

#### Auto Role
- Create Auto Join Role
- Delete Auto Join role
- Ignore when bots join

#### Self Assignable Roles
- Create Role
- Delete Role
- Edit Role
- Add Role requirements
- Unique Role (remove roles of same group)
- Role Groups

#### Logging
- Set up channel for moderation logs
- Remove currently active moderation log
- Change log channel to another

#### Welcome Messages
- Set up channel for Welcome Messages
- Welcome Message formatting
- Edit currently active welcome message
- Delete active welcome mesasge channel

#### Music
- Connect
- Play
- Stop
- Skip
- Disconnect
- View currently playing song
- View current Queue

#### Economy
- Daily
- Balance
- Global Leaderboard
- Guild Leaderboard
- Spin (0.1 - 2.0)
- Bet (50/50 for double or nothing)
- Dice Roll (XdX)

#### Custom Responses
- Create new response
- View all responses
- Delete a response
- (Blacklisting applies to auto responses)

#### Tags
- Create new tag
- Delete a tag that you own
- Edit a tag that you own
- View information about a tag
- Create an alias of one tag to another
- View all guild tags
- View user specific tags

#### Custom Commands
- Create a new custom command
- Delete a custom command
- Edit an existing custom command
- View all custom commands

## Requirements
The following modules are required if you want to run
Gamma yourself. (Note you can install the
requirements.txt file instead of following each of
these modules.)
```
discord.py # Rewrite
asyncpg
aiohttp
psutil
lxml
psycopg2
youtube_dl
speedtest-cli
jishaku
GitPython
uvloop if linux
pympler
matplotlib
```

## Credits
Not much to say here, bug Xua#9307 created this bot and
any credit should go to him.
