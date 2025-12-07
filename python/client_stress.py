#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import struct
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed


def envoyer_requete(host: str, port: int, number: int) -> float:
    start = time.perf_counter()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0)
            s.connect((host, port))
            data = struct.pack("!i", number)
            s.sendall(data)
            result_raw = s.recv(4)
            ts_raw = s.recv(8)
            if len(result_raw) < 4 or len(ts_raw) < 8:
                return -1.0
            _ = struct.unpack("!i", result_raw)[0]
            _ = struct.unpack("!q", ts_raw)[0]
    except Exception:
        return -1.0
    end = time.perf_counter()
    return (end - start) * 1000.0


def lancer_stress_test(host: str, port: int, clients: int, number: int = 42):
    latences = []
    with ThreadPoolExecutor(max_workers=clients) as executor:
        futures = [executor.submit(envoyer_requete, host, port, number)
                   for _ in range(clients)]
        for f in as_completed(futures):
            lat = f.result()
            if lat >= 0:
                latences.append(lat)

    if not latences:
        return {
            "clients": clients, "success": 0, "fail": clients,
            "mean": None, "median": None, "p95": None, "p99": None,
            "max": None, "latences": [],
        }

    latences_sorted = sorted(latences)
    n = len(latences_sorted)

    def percentile(p):
        if n == 0:
            return None
        k = int(p * (n - 1))
        return latences_sorted[k]

    return {
        "clients": clients,
        "success": len(latences),
        "fail": clients - len(latences),
        "mean": statistics.mean(latences),
        "median": statistics.median(latences),
        "p95": percentile(0.95),
        "p99": percentile(0.99),
        "max": max(latences),
        "latences": latences,
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Client de stress TCP")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--clients", type=int, default=50)
    args = parser.parse_args()

    print(f"[CLIENT] {args.clients} connexions vers {args.host}:{args.port}")
    res = lancer_stress_test(args.host, args.port, args.clients)
    print(res)


if __name__ == "__main__":
    main()

