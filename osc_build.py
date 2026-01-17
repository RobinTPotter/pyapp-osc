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

def send_osc_int(ip, port, address, value):
    msg = osc_pad(address.encode())
    msg += osc_pad(b",i")
    msg += struct.pack(">i", int(value))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(msg, (ip, port))
    sock.close()


def send_osc_blank(ip, port, address): #, args=None):
    print(f"send to {port} {ip}")
    data = osc_blank_message(address) #, args)
    print(f"data to send is {data}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(data, (ip, port))
    sock.close()



def build_osc(address, args):
    msg = osc_pad(address.encode())

    tags = ","
    payload = b""

    for a in args:
        if isinstance(a, int):
            tags += "i"
            payload += struct.pack(">i", a)

        elif isinstance(a, float):
            tags += "f"
            payload += struct.pack(">f", a)

        elif isinstance(a, str):
            tags += "s"
            payload += osc_pad(a.encode())

        else:
            raise TypeError(f"Unsupported OSC arg: {a}")

    msg += osc_pad(tags.encode())
    msg += payload
    return msg


def send_osc(ip, port, address, args=None):
    if args is None:
        args = []

    msg = build_osc(address, args)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.sendto(msg, (ip, port))
    s.close()
