"""Utility for server administration via source rcon."""
import socket
import struct

from dataclasses import dataclass

from loguru import logger


@dataclass
class RconPacket:
    # https://developer.valvesoftware.com/wiki/Source_RCON_Protocol#Basic_Packet_Structure
    size: int = None
    id: int = None
    type: int = None
    body: str = None
    terminator: bytes = b"\x00"

    def pack(self):
        body_encoded = (
            self.body.encode("ascii") + self.terminator
        )  # The packet body field is a null-terminated string encoded in ASCII
        self.size = (
            len(body_encoded) + 10
        )  # Only value that can change is the length of the body, so do len(body) + 10.
        return (
            struct.pack("<iii", self.size, self.id, self.type)
            + body_encoded
            + self.terminator
        )


@dataclass
class RCONPacketType:
    SERVERDATA_AUTH: int = 3
    SERVERDATA_AUTH_RESPONSE: int = 2
    SERVERDATA_EXECCOMMAND: int = 2
    SERVERDATA_RESPONSE_VALUE: int = 0


class SourceRcon:
    def __init__(self, server_ip: str, rcon_port: int, rcon_password: str) -> None:
        self.SERVER_IP = server_ip
        self.RCON_PORT = rcon_port
        self.RCON_PASSWORD = rcon_password

    def create_packet(
        self, command, request_id=1, type=RCONPacketType.SERVERDATA_EXECCOMMAND
    ):
        packet = RconPacket(id=request_id, type=type, body=command)
        final_packet = packet.pack()

        logger.debug(f"Final packet: {final_packet}")
        return final_packet

    def receive_all(self, sock, bytes_in: int = 4096):
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

    def decode_response(self, response):
        if len(response) < 12:
            return "Invalid response"
        size, request_id, type = struct.unpack("<iii", response[:12])
        if size <= 10:
            return "No response body or empty response."
        try:
            # Decode response with UTF-8
            body = response[12:-2].decode("utf-8")
        except UnicodeDecodeError as e:
            # If UTF-8 decoding fails, use "replace" error handling
            logger.warning(f"UnicodeDecodeError: {e}")
            body = response[12:-2].decode("utf-8", errors="replace")
        return body

    def get_auth_response(self, auth_response_packet):
        if len(auth_response_packet) < 12:
            return "Invalid response"
        size, request_id, type = struct.unpack("<iii", auth_response_packet[:12])

        if type == RCONPacketType.SERVERDATA_AUTH_RESPONSE:
            # If request_id is -1, authentication failed
            if request_id == -1:
                return False
            else:
                return True
        else:
            logger.error("get_auth_response was given a packet of wrong type.")

    def send_command(self, command):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((self.SERVER_IP, self.RCON_PORT))
            except socket.error as e:
                logger.error(f"Failed to connect to socket. Error: {e}")
            else:
                logger.debug("Connection successful.")

            # Authenticate to server rcon before sending command
            logger.info("Authenticating to server rcon before sending command.")
            auth_packet = self.create_packet(
                self.RCON_PASSWORD, type=RCONPacketType.SERVERDATA_AUTH
            )
            s.sendall(auth_packet)

            # Get and parse authentication response
            auth_response = self.receive_all(s)
            if self.get_auth_response(auth_response):
                logger.debug("Authentication successful.")
            else:
                logger.error("Authentication failed. Not running command.")
                return ""

            # Send command
            command_packet = self.create_packet(command)
            s.sendall(command_packet)

            # Get command response
            response = self.receive_all(s)
            decoded_response = self.decode_response(response)
            logger.debug(decoded_response)
            return decoded_response
