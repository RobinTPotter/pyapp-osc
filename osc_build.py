import socket
import struct


def osc_pad(s: bytes) -> bytes:
    """Pad OSC strings to 4-byte boundary"""
    s += b'\x00'
    while len(s) % 4 != 0:
        s += b'\x00'
    return s


def osc_message(address: str, args=None) -> bytes:
    if args is None:
        args = []

    msg = osc_pad(address.encode("utf-8"))

    # type tag string
    tags = "," + "".join("s" for _ in args)
    msg += osc_pad(tags.encode("utf-8"))

    for arg in args:
        msg += osc_pad(str(arg).encode("utf-8"))

    return msg


def send_osc(ip, port, address, args=None):
    data = osc_message(address, args)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(data, (ip, port))
    sock.close()
