# Palworld dedicated server helper
Helper utilities for managing a Palworld dedicated server in python. Send rcon commands, backup server, etc.

* underlying rcon implementation should work fine on any OS if you want to use it directly.
* `PalworldUtil` has been tested and works on Windows (11) and linux (ubuntu 22.04) following [Windows - (steamcmd) / Linux - (steamcmd) guides](https://tech.palworldgame.com/dedicated-server-guide)
* * Some paths and executables are assumed but can be set by the user.

## Setup
* Install python: https://www.python.org/downloads/
* * Make sure to check the box `Add Python to PATH` when installing so you can call python from your terminal.
* Install required python libraries: `pip install -r requirements.txt`

## Usage
* See `./src/palworld_rcon/source_rcon.py` for direct rcon usage.
* * You can call rcon commands via library import or via cli:
* * * Looks for environment variables: `palworld_server_ip`, `palworld_rcon_port`, `palworld_rcon_password`, otherwise they are required cli args.
```bash
$.\palworld_dedi_helper\src\palworld_rcon> python source_rcon.py -cmd Info
Welcome to Pal Server[v0.1.3.0] My Palworld Server
```
* See `./src/example.py` for basic usage.
* See `./src/utility/palworld_util.py` for advanced params, etc.
* * If hosting on linux, make sure to pass `operating_system = "linux"`, otherwise defaults to windows.
* See `./src/server_watcher.py` for:
* * Automatic server restart when process goes down.
* * Automatic server restarts on a timer.
* * Automatic backups with rotation.

# Contributing
Feel free to open issues or pull requests as long as they're constructive / useful.
