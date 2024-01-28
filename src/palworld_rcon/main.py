"""Palworld RCON helper."""
from palworld_rcon.source_rcon import SourceRcon


class PalworldRcon:
    def __init__(self, server_ip: str, rcon_port: int, rcon_password: str):
        self.SERVER_IP = server_ip
        self.RCON_PORT = rcon_port
        self.RCON_PASSWORD = rcon_password

        self.rcon = SourceRcon(self.SERVER_IP, self.RCON_PORT, self.RCON_PASSWORD)

        self.COMMANDS = {
            "Shutdown": "Shutdown",  # /Shutdown {Seconds} {MessageText} - Gracefully shuts down server with an optional timer and/or message to notify players in your server.
            "DoExit": "DoExit",  # /DoExit - Forcefully shuts down the server immediately. It is not recommended to use this option unless you've got a technical problem or are okay with potentially losing data.
            "Broadcast": "Broadcast",  # /Broadcast {MessageText} - Broadcasts a message to all players in the server.
            "KickPlayer": "KickPlayer",  # /KickPlayer {PlayerUID or SteamID} - Kicks player from the server. Useful for getting a player's attention with moderation.
            "BanPlayer": "BanPlayer",  # /BanPlayer {PlayerUID or SteamID} - Bans player from the server. The Player will not be able to rejoin the server until they are unbanned.
            "TeleportToPlayer": "TeleportToPlayer",  # /TeleportToPlayer {PlayerUID or SteamID} - INGAME ONLY Immediately teleport to the target player
            "TeleportToMe": "TeleportToMe",  # /TeleportToMe {PlayerUID or SteamID} - INGAME ONLY Immediately teleports target player to you.
            "ShowPlayers": "ShowPlayers",  # /ShowPlayers - Shows information on all connected players
            "Info": "Info",  # /Info - Shows server information
            "Save": "Save",  # /Save - Save the world data to disk. Useful to ensure your Pal, player, and other data is saved before stopping the server or performing a risky gameplay option.
        }

    def run_command(self, command: str, args: list = []) -> str:
        packet = self.COMMANDS[command] + " " + " ".join(args)
        print(f"Packet: {packet}")
        response = self.rcon.send_command(packet)
        return response
