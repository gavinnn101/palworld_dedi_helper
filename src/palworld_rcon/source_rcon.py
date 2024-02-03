"""Utility for server administration via source rcon."""

import argparse
import os
import socket
import struct
import sys

from dataclasses import dataclass

from loguru import logger


from enum import Enum


class RCONPacketType(Enum):
    SERVERDATA_AUTH = 3
    SERVERDATA_AUTH_RESPONSE = 2
    SERVERDATA_EXECCOMMAND = 2
    SERVERDATA_RESPONSE_VALUE = 0


@dataclass
class RconPacket:
    # https://developer.valvesoftware.com/wiki/Source_RCON_Protocol#Basic_Packet_Structure
    size: int = None
    id: int = None
    type: RCONPacketType = None
    body: str = None
    terminator: bytes = b"\x00"
    RCON_PACKET_HEADER_LENGTH: int = 12
    RCON_PACKET_TERMINATOR_LENGTH: int = 2

    def pack(self):
        body_encoded = (
            self.body.encode("ascii") + self.terminator
        )  # The packet body field is a null-terminated string encoded in ASCII
        self.size = (
            len(body_encoded) + 10
        )  # Only value that can change is the length of the body, so do len(body) + 10.
        return (
            struct.pack("<iii", self.size, self.id, self.type.value)
            + body_encoded
            + self.terminator
        )

    @staticmethod
    def unpack(packet: bytes):
        if len(packet) < RconPacket.RCON_PACKET_HEADER_LENGTH:
            return RconPacket(size=None, id=None, type=None, body="Invalid packet")

        size, request_id, type = struct.unpack(
            "<iii", packet[: RconPacket.RCON_PACKET_HEADER_LENGTH]
        )
        body = packet[
            RconPacket.RCON_PACKET_HEADER_LENGTH : -RconPacket.RCON_PACKET_TERMINATOR_LENGTH
        ].decode("utf-8", errors="replace")
        return RconPacket(size=size, id=request_id, type=type, body=body)


class SourceRcon:
    def __init__(self, server_ip: str, rcon_port: int, rcon_password: str) -> None:
        self.SERVER_IP = server_ip
        self.RCON_PORT = rcon_port
        self.RCON_PASSWORD = rcon_password

        self.AUTH_FAILED_RESPONSE = -1

    def create_packet(
        self,
        command: str,
        request_id: int = 1,
        type: RCONPacketType = RCONPacketType.SERVERDATA_EXECCOMMAND,
    ) -> RconPacket:
        packet = RconPacket(id=request_id, type=type, body=command)
        final_packet = packet.pack()

        logger.debug(f"Final packet: {final_packet}")
        return final_packet

    def receive_all(self, sock: socket.socket, bytes_in: int = 4096) -> bytes:
        response = b""
        while True:
            try:
                part = sock.recv(bytes_in)
                if not part:
                    break
                response += part
                if len(part) < bytes_in:
                    break
            except socket.error as e:
                logger.error(f"Error receiving data: {e}")
                break
        return response

    def check_auth_response(self, auth_response_packet: bytes) -> bool:
        unpacked_packet = RconPacket.unpack(auth_response_packet)

        if (
            unpacked_packet.size is None
            or unpacked_packet.type != RCONPacketType.SERVERDATA_AUTH_RESPONSE.value
        ):
            logger.error("Invalid response or wrong packet type.")
            return False

        return unpacked_packet.id != self.AUTH_FAILED_RESPONSE

    def auth_to_rcon(self, socket: socket.socket) -> bool:
        # Create and send rcon authentication packer
        logger.debug("Authenticating to server rcon before sending command.")
        auth_packet = self.create_packet(
            self.RCON_PASSWORD, type=RCONPacketType.SERVERDATA_AUTH
        )
        socket.sendall(auth_packet)

        # Get and parse rcon authentication response
        auth_response = self.receive_all(socket)
        if self.check_auth_response(auth_response):
            logger.debug("rcon authentication successful.")
            return True
        else:
            logger.error("rcon authentication failed.")
            return False

    def establish_connection(self, socket: socket.socket) -> bool:
        try:
            socket.connect((self.SERVER_IP, self.RCON_PORT))
            logger.debug("Socket connection successful.")
            return True
        except socket.error as e:
            logger.error(f"Failed to connect to socket. Error: {e}")
            return False

    def execute_command(self, socket: socket.socket, command: str) -> str:
        command_packet = self.create_packet(command)
        socket.sendall(command_packet)

        response = self.receive_all(socket)
        unpacked_packet = RconPacket.unpack(response)
        logger.debug(f"Command response: {unpacked_packet.body}")
        return unpacked_packet.body

    def send_command(self, command: str, args: list = []) -> str:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if not self.establish_connection(s):
                return "Failed to establish connection."

            if not self.auth_to_rcon(s):
                return "Authentication failed. not running command."

            # if command == "broadcast", replace spaces with \x1F in args[0](broadcast message string expected) to create fake spaces.
            if command.lower() == "broadcast":
                command = command + " " + args[0].replace(" ", "\x1F")
            else:
                command = command + " " + " ".join(args)

            logger.debug(f"Sending command: {command}")
            return self.execute_command(s, command)


def main():
    # Default values from environment variables
    default_ip = os.environ.get("palworld_server_ip")
    default_port = os.environ.get("palworld_rcon_port")
    default_password = os.environ.get("palworld_rcon_password")

    parser = argparse.ArgumentParser(description="Palworld RCON Command Line Interface")
    parser.add_argument(
        "-ip",
        "--server_ip",
        type=str,
        default=default_ip,
        required=not default_ip,
        help="IP address of the RCON server",
    )
    parser.add_argument(
        "-port",
        "--rcon_port",
        type=int,
        default=default_port,
        required=not default_port,
        help="Port of the RCON server",
    )
    parser.add_argument(
        "-pwd",
        "--rcon_password",
        type=str,
        default=default_password,
        required=not default_password,
        help="RCON password",
    )
    parser.add_argument(
        "-cmd", "--command", required=True, help="RCON command to execute"
    )
    parser.add_argument(
        "-args",
        "--arguments",
        nargs="*",
        default=[],
        help="Arguments for the RCON command",
    )
    parser.add_argument(
        "-ll", "--log_level", type=str, default="INFO", help="Log level to output at."
    )

    args = parser.parse_args()

    # Set log level
    logger.remove()
    logger.add(sys.stderr, level=args.log_level)

    rcon = SourceRcon(args.server_ip, args.rcon_port, args.rcon_password)
    response = rcon.send_command(args.command, args.arguments)
    print(response)


if __name__ == "__main__":
    main()
