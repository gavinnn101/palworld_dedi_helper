"""Handles server uptime with auto restart, auto backup, etc."""
from utility.palworld_util import PalworldUtil
from utility.util import check_for_process

import os
import sys
import time

from pathlib import Path

from loguru import logger


# User variables
AUTOMATIC_RESTART = True  # Automatically restart the server if the process isn't found.
AUTOMATIC_RESTART_EVERY_X_MINUTES = 720  # Set to -1 if you don't want automatic restarts on a timer.
BACKUP_ON_RESTART = True  # Save a backup when the server restarts.
BACKUP_EVERY_X_MINUTES = 240  # Set to -1 if you don't want to backup on a timer.
ROTATE_AFTER_X_BACKUPS = 5  # Set to -1 if you don't want to rotate backups.
ROTATE_LOGS_EVERY_X_RUNS = 5  # Set to -1 if you don't want to log to file.
LOG_LEVEL = "INFO"
LOGS_DIR = "logs"


STEAMCMD_DIR = os.getenv("steamcmd_dir")
SERVER_NAME = os.getenv("palworld_server_name")
SERVER_IP = os.getenv("palworld_server_ip")
RCON_PASSWORD = os.getenv("palworld_rcon_password")
RCON_PORT = int(os.getenv("palworld_rcon_port"))

LOOP_SLEEP = 30


def calculate_minutes_elapsed(last_time):
    return (time.time() - last_time) / 60


def log_initial_timers():
    if AUTOMATIC_RESTART:
        logger.info(
            f"Next server restart in: {AUTOMATIC_RESTART_EVERY_X_MINUTES} minutes"
        )
    if BACKUP_EVERY_X_MINUTES > 0:
        logger.info(f"Next backup in: {BACKUP_EVERY_X_MINUTES} minutes")


def watcher_loop(pal: PalworldUtil):
    last_restart = last_backup = time.time()
    log_initial_timers()

    while True:
        if (
            BACKUP_EVERY_X_MINUTES > 0
            and calculate_minutes_elapsed(last_backup) >= BACKUP_EVERY_X_MINUTES
        ):
            pal.log_and_broadcast("Taking server backup...")
            pal.take_server_backup()
            last_backup = time.time()
            logger.info(f"Next backup in: {BACKUP_EVERY_X_MINUTES} minutes")

        if AUTOMATIC_RESTART:
            minutes_since_last_restart = calculate_minutes_elapsed(last_restart)

            if not check_for_process(pal.palworld_server_proc_name):
                logger.info(f"Server process not found, restarting...")
                pal.launch_server()
                last_restart = time.time()
                logger.info(
                    f"Next server restart in: {AUTOMATIC_RESTART_EVERY_X_MINUTES} minutes"
                )

            elif minutes_since_last_restart >= AUTOMATIC_RESTART_EVERY_X_MINUTES:
                logger.info(
                    f"Restarting server after {minutes_since_last_restart:.2f} minutes..."
                )
                pal.restart_server(backup_server=BACKUP_ON_RESTART)
                last_restart = time.time()
                logger.info(
                    f"Next server restart in: {AUTOMATIC_RESTART_EVERY_X_MINUTES} minutes"
                )

        time.sleep(LOOP_SLEEP)


def main():
    if ROTATE_LOGS_EVERY_X_RUNS > 0:
        logs_path = Path(LOGS_DIR)
        if not os.path.exists(logs_path):
            logger.info(f"Creating logs dir: {logs_path}")
            logs_path.mkdir(exist_ok=True)
        # Add logging sink to file and rotate every ROTATE_LOGS_EVERY_X_RUNS runs/logs.
        logger.add(
            logs_path / "log_{time}.txt",
            level=LOG_LEVEL,
            colorize=False,
            backtrace=True,
            diagnose=True,
            retention=ROTATE_LOGS_EVERY_X_RUNS,
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
