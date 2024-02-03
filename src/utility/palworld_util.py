from palworld_rcon.source_rcon import SourceRcon
from utility.util import check_for_process, kill_process

import datetime
import os
import shutil
import subprocess
import time

from pathlib import Path

from loguru import logger


class PalworldUtil:
    def __init__(
        self,
        steamcmd_dir: str,
        server_name: str,
        server_ip: str,
        rcon_port: int,
        rcon_password: str,
        palword_server_dir: str = None, # Path to Palworld server root directory. Tries to find if not provided.
        palworld_server_proc_name: str = "PalServer-Win64-Test-Cmd.exe",  # Name of the palworld dedicated server process. Used for monitoring, restarting, etc.
        wait_before_restart_seconds: int = 30,
        steam_app_id: str = "2394010",  # Palworld dedicated server.
        server_port: int = 8211,
        max_players: int = 32,  # 32 players is max.
        rcon: SourceRcon = None,
        backup_dir: str = None,
        rotate_backups: bool = True,
        rotate_after_x_backups: int = 5,
        operating_system: str = "windows",
    ) -> None:
        self.steamcmd_dir = Path(steamcmd_dir)  # Path to steamcmd.exe directory.
        self.palworld_server_save_dir = Path(self.palworld_server_dir / "Pal" / "Saved")
        self.server_name = server_name  # What you want the server name to be.
        self.operating_system = operating_system.lower()  # "windows" or "linux".

        # rcon variables
        self.server_ip = server_ip
        self.rcon_port = rcon_port
        self.rcon_password = rcon_password

        self.wait_before_restart_seconds = wait_before_restart_seconds  # Seconds to wait after warning the server before starting the server restart process.
        self.steam_app_id = steam_app_id
        self.server_port = server_port
        self.max_players = max_players

        self.server_launch_args = []

        if self.operating_system == "windows":
            self.palworld_server_proc_name = palworld_server_proc_name
            self.steamcmd_executable = "steamcmd.exe"
            self.palserver_executable = "PalServer.exe"
            self.palworld_server_dir = Path(self.steamcmd_dir / "steamapps" / "common" / "PalServer")
            self.server_launch_args.append("start")
        elif self.operating_system == "linux":
            self.palworld_server_proc_name = "./PalServer.sh"
            self.steamcmd_executable = "steamcmd"
            self.palserver_executable = "./PalServer.sh"
            self.palworld_server_dir = Path("/home/steam/Steam/steamapps/common/PalServer")
        
        # Overwrite palworld_server_dir if set by user
        if palword_server_dir:
            self.palworld_server_dir = palword_server_dir

        # Common server launch args
        self.server_launch_args.append(self.palserver_executable)
        self.server_launch_args.append(f"-ServerName={self.server_name}")
        self.server_launch_args.append(f"-port={self.server_port}")
        self.server_launch_args.append(f"-players={self.max_players}")
        self.server_launch_args.append("-log")
        self.server_launch_args.append("-nosteam")
        self.server_launch_args.append("-useperfthreads")
        self.server_launch_args.append("-NoAsyncLoadingThread")
        self.server_launch_args.append("-UseMultithreadForDS")

        if rcon:
            self.rcon = rcon
        else:
            self.rcon = SourceRcon(self.server_ip, self.rcon_port, self.rcon_password)

        # Create and use "$script_root/backups" dir if backups_dir isn't provided.
        if backup_dir is None:
            self.backups_dir = Path(os.getcwd()) / "backups"
            if not os.path.exists(self.backups_dir):
                self.backups_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.backups_dir = Path(backup_dir)

        self.rotate_backups = rotate_backups
        self.rotate_after_x_backups = rotate_after_x_backups

    def log_and_broadcast(self, message: str, log_level: str = "info"):
        match log_level.lower():
            case "info":
                logger.info(message)
            case "debug":
                logger.debug(message)
            case "warning":
                logger.warning(message)
            case "error":
                logger.error(message)
            case "exception":
                logger.exception(message)
            case "success":
                logger.success(message)
        try:
            self.rcon.send_command("Broadcast", [message])
        except OSError as e:
            logger.warning(
                f"Not able to send broadcast via log_and_broadcast(). Server online?"
            )
            logger.debug(f"log_and_broadcast() error: {e}")

    def save_server_state(self) -> bool:
        """Tries to send an rcon command to save the server / game state.

        Returns: True if sucess, False otherwise.
        """
        SAVE_FINISHED_RESPONSE = "Complete Save"

        self.log_and_broadcast("Saving game state.")
        response = self.rcon.send_command("Save")
        if response.strip() == SAVE_FINISHED_RESPONSE:
            self.log_and_broadcast("Save game state finished.")
            return True
        else:
            self.log_and_broadcast("Save game state failed!")
            return False

    def update_game_server(self):
        """Calls steamcmd process on steam_app_id to get game / server updates."""
        # Change to steamcmd directory if needed.
        if os.getcwd() != self.steamcmd_dir:
            logger.info(f"Changing to steamcmd dir: {self.steamcmd_dir}")
            os.chdir(self.steamcmd_dir)

        logger.info("Checking for game server updates...")
        subprocess.call(
            [
                self.steamcmd_executable,
                "+login",
                "anonymous",
                "+app_update",
                self.steam_app_id,
                "validate",
                "+quit",
            ]
        )

    def launch_server(self, update_server: bool = True):
        """Launches Palserver with specified parameters."""
        # Check for server updates before launching.
        if update_server:
            self.update_game_server()
        else:
            logger.info("Skipping game server updates.")

        # Change to Palserver.exe directory if needed.
        if os.getcwd() != self.palworld_server_dir:
            logger.info(f"Changing to palworld server dir: {self.palworld_server_dir}")
            os.chdir(self.palworld_server_dir)

        logger.info(f"Launching {self.palserver_executable}...")
        subprocess.Popen(self.server_launch_args, shell=True)

    def take_server_backup(self, timestamp_format: str = "%Y%m%d_%H%M%S"):
        timestamp = datetime.datetime.now().strftime(timestamp_format)
        destination_folder = os.path.join(
            self.backups_dir,
            os.path.basename(self.palworld_server_save_dir) + "_" + timestamp,
        )

        logger.info(f"Copying: {self.palworld_server_save_dir} -> {destination_folder}")
        shutil.copytree(self.palworld_server_save_dir, destination_folder)

        if self.rotate_backups:
            self._rotate_backups()

    def _rotate_backups(self):
        """Delete oldest backups if over `self.rotate_after_x_backups`."""
        backups = sorted(self.backups_dir.iterdir(), key=os.path.getmtime)

        # Keep only the newest backups
        backups_to_delete = backups[: -self.rotate_after_x_backups]
        for backup in backups_to_delete:
            if backup.is_dir():
                shutil.rmtree(backup)
                logger.info(f"Deleted old backup: {backup}")

    def restart_server(
        self,
        save_game: bool = True,
        check_for_server_updates: bool = True,
        backup_server: bool = True,
    ):
        """Restart Palword server with extra maintenance options."""
        # Sleep before starting server restart process.
        restart_warning_msg = f"Waiting {self.wait_before_restart_seconds} seconds before starting restart process."
        self.log_and_broadcast(restart_warning_msg)
        time.sleep(self.wait_before_restart_seconds)

        self.log_and_broadcast("Server restart process started.")

        # Save game state if needed.
        if save_game:
            self.save_server_state()

        self.log_and_broadcast("Restarting server now.")

        # Find and end server process.
        if check_for_process(self.palworld_server_proc_name):
            logger.info("Ending palworld server process.")
            kill_process(self.palworld_server_proc_name)
        else:
            logger.error(
                f"Couldn't find palworld server process: ({self.palworld_server_proc_name})"
            )

        # Take backup of server if needed.
        if backup_server:
            self.take_server_backup()
        else:
            logger.info("Skipping server backup.")

        # Launch server.
        self.launch_server(update_server=check_for_server_updates)
