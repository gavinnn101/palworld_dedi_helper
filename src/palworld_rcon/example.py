from main import PalworldRcon

import os


SERVER_IP = os.getenv("palworld_server_ip")
RCON_PORT = int(os.getenv("palworld_rcon_port"))
RCON_PASSWORD = os.getenv("palworld_rcon_password")


def main():
    rcon = PalworldRcon(SERVER_IP, RCON_PORT, RCON_PASSWORD)

    # Get server info
    rcon.run_command("Info")

    # Get players
    rcon.run_command("ShowPlayers")

    # # Broadcast message
    # rcon.run_command("Broadcast", ['"Test message"'])


main()
