import socket
import struct


def osc_pad(s: bytes) -> bytes:
    """Pad OSC strings to 4-byte boundary"""
    s += b'\x00'
    while len(s) % 4 != 0:
        s += b'\x00'
    return s


def osc_blank_message(address: str) -> bytes:
    print(f"creating message {address}") 
    msg = osc_pad(address.encode("utf-8"))
    msg += osc_pad(b",")
    return msg

def send_osc_float(ip, port, address, value):
    msg = osc_pad(address.encode())
    msg += osc_pad(b",f")
    msg += struct.pack(">f", float(value))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(msg, (ip, port))
    sock.close()

def send_osc_blank(ip, port, address): #, args=None):
    print(f"send to {port} {ip}")
    data = osc_message(address) #, args)
    print(f"data to send is {data}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(data, (ip, port))
    sock.close()
