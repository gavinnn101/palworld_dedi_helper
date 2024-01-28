from utility.palworld_util import PalworldUtil

import os


STEAMCMD_DIR = os.getenv("steamcmd_dir")
SERVER_NAME = os.getenv("palworld_server_name")
SERVER_IP = os.getenv("palworld_server_ip")
RCON_PASSWORD = os.getenv("palworld_rcon_password")
RCON_PORT = int(os.getenv("palworld_rcon_port"))


# Create PalworldUtil instance with required vars only.
pal = PalworldUtil(STEAMCMD_DIR, SERVER_NAME, SERVER_IP, RCON_PORT, RCON_PASSWORD)

# Don't rotate backups.
pal.rotate_backups = False

# or do...
pal.rotate_backups = True
pal.rotate_after_x_backups = 3  # Delete oldest backup after 3 backups.

# Create a server backup.
pal.take_server_backup()

# Send a broadcast to the server.
pal.rcon.run_command(command="Broadcast", args=["test"])

# Restart the server.
# pal.restart_server(save_game=True, check_for_server_updates=True, backup_server=False)
