"""Handles server uptime with auto restart, auto backup, etc."""
from utility.palworld_util import PalworldUtil
from utility.util import check_for_process

import os
import sys
import time

from loguru import logger


# User variables
AUTOMATIC_RESTART = True  # Automatically restart the server if the process isn't found.
AUTOMATIC_RESTART_EVERY_X_MINUTES = 720  # Set to `-1` if you want automatic restart watcher but no automatic restarts on a timer.
BACKUP_ON_RESTART = True  # Save a backup when the server restarts.
AUTOMATIC_BACKUPS = True  # Automatically backup on timer
ROTATE_AFTER_X_BACKUPS = 5  # Set to -1 if you don't want to rotate backups.
BACKUP_EVERY_X_MINUTES = 240
ROTATE_LOGS_EVERY_X_RUNS = 5    # Set to -1 if you don't want to log to file.


STEAMCMD_DIR = os.getenv("steamcmd_dir")
SERVER_NAME = os.getenv("palworld_server_name")
SERVER_IP = os.getenv("palworld_server_ip")
RCON_PASSWORD = os.getenv("palworld_rcon_password")
RCON_PORT = int(os.getenv("palworld_rcon_port"))

LOOP_SLEEP = 30


def watcher_loop(pal: PalworldUtil):
    last_restart = time.time()
    last_backup = time.time()
    while True:
        current_time = time.time()
        if BACKUP_EVERY_X_MINUTES > 0:
            minutes_since_last_backup = (current_time - last_backup) / 60
            if minutes_since_last_backup >= BACKUP_EVERY_X_MINUTES:
                pal.log_and_broadcast("Taking server backup...")
                pal.take_server_backup()
                last_backup = current_time

        if AUTOMATIC_RESTART:
            minutes_since_last_restart = (current_time - last_restart) / 60

            if not check_for_process(pal.palworld_server_proc_name):
                logger.info(
                    f"Couldn't find Palworld server process ({pal.palworld_server_proc_name}), restarting..."
                )
                pal.launch_server()
                last_restart = current_time

            elif AUTOMATIC_RESTART_EVERY_X_MINUTES > 0:
                if minutes_since_last_restart >= AUTOMATIC_RESTART_EVERY_X_MINUTES:
                    pal.log_and_broadcast(
                        f"It's been {minutes_since_last_restart} minutes since last restart, restarting server..."
                    )
                    pal.restart_server(backup_server=BACKUP_ON_RESTART)
                    last_restart = current_time

        # logger.info(f"Sleeping {LOOP_SLEEP} seconds before next loop...")
        time.sleep(LOOP_SLEEP)


def main():
    if ROTATE_LOGS_EVERY_X_RUNS > 0:
        # Add logging sink to file and rotate every ROTATE_LOGS_EVERY_X_RUNS runs/logs.
        logger.add(
            "log_{time}.txt",
            level="INFO",
            colorize=False,
            backtrace=True,
            diagnose=True,
            retention=ROTATE_LOGS_EVERY_X_RUNS
        )

    # Create PalworldUtil instance with required vars only.
    pal = PalworldUtil(STEAMCMD_DIR, SERVER_NAME, SERVER_IP, RCON_PORT, RCON_PASSWORD)

    if ROTATE_AFTER_X_BACKUPS > 0:
        pal.rotate_after_x_backups = ROTATE_AFTER_X_BACKUPS
    else:
        pal.rotate_backups = False

    try:
        watcher_loop(pal)
    except KeyboardInterrupt:
        logger.info("Caught keyboard interrupt, ending server_watcher...")
        sys.exit(0)

main()
