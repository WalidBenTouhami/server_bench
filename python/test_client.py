#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import struct


def main():
    host = "127.0.0.1"
    port = 5050
    number = 7

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(struct.pack("!i", number))
        result_raw = s.recv(4)
        ts_raw = s.recv(8)
        result = struct.unpack("!i", result_raw)[0]
        ts = struct.unpack("!q", ts_raw)[0]
        print(f"Nombre envoyé : {number}")
        print(f"Résultat reçu : {result}")
        print(f"Timestamp serveur (µs) : {ts}")


if __name__ == "__main__":
    main()

