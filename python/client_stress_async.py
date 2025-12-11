#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
client_stress_async.py
Client de stress TCP asynchrone (asyncio) pour très forte concurrence (10k+).
Protocole: même format que serveur_mono / serveur_multi (int32 -> carré + ts).
"""

import asyncio
import struct
import time
import statistics
from typing import List, Dict


async def envoyer_requete_async(
    host: str,
    port: int,
    number: int,
    timeout: float = 5.0,
    semaphore: asyncio.Semaphore = None,
) -> float:
    """Une requête TCP asynchrone, retourne la latence en ms ou -1 en cas d'erreur."""
    if semaphore is None:
        semaphore = asyncio.Semaphore(100000)  # fallback

    async with semaphore:
        start = time.perf_counter()
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout,
            )

            writer.write(struct.pack("!i", number))
            await writer.drain()

            result_raw = await asyncio.wait_for(reader.readexactly(4), timeout=timeout)
            ts_raw = await asyncio.wait_for(reader.readexactly(8), timeout=timeout)

            if len(result_raw) < 4 or len(ts_raw) < 8:
                writer.close()
                await writer.wait_closed()
                return -1.0

            writer.close()
            await writer.wait_closed()
        except Exception:
            return -1.0

        end = time.perf_counter()
        return (end - start) * 1000.0


async def lancer_stress_async(
    host: str,
    port: int,
    clients: int,
    number: int = 42,
    max_inflight: int = 2000,
) -> Dict:
    """Lance un test asynchrone avec un nombre massif de clients."""
    semaphore = asyncio.Semaphore(max_inflight)

    t0 = time.perf_counter()

    tasks = [
        envoyer_requete_async(host, port, number, semaphore=semaphore)
        for _ in range(clients)
    ]

    latences: List[float] = []
    for coro in asyncio.as_completed(tasks):
        lat = await coro
        if lat >= 0:
            latences.append(lat)

    t1 = time.perf_counter()
    total_time = t1 - t0

    if not latences:
        return {
            "mode": "asyncio",
            "host": host,
            "port": port,
            "clients": clients,
            "success": 0,
            "fail": clients,
            "throughput_req_s": 0.0,
            "mean_ms": None,
            "median_ms": None,
            "p95_ms": None,
            "p99_ms": None,
            "max_ms": None,
        }

    lat_sorted = sorted(latences)
    n = len(lat_sorted)

    def pct(p: float) -> float:
        k = int(p * (n - 1))
        return lat_sorted[k]

    mean = statistics.mean(lat_sorted)
    median = statistics.median(lat_sorted)
    p95 = pct(0.95)
    p99 = pct(0.99)
    max_v = max(lat_sorted)
    throughput = len(lat_sorted) / total_time if total_time > 0 else 0.0

    return {
        "mode": "asyncio",
        "host": host,
        "port": port,
        "clients": clients,
        "success": len(lat_sorted),
        "fail": clients - len(lat_sorted),
        "throughput_req_s": round(throughput, 2),
        "mean_ms": round(mean, 3),
        "median_ms": round(median, 3),
        "p95_ms": round(p95, 3),
        "p99_ms": round(p99, 3),
        "max_ms": round(max_v, 3),
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Client de stress TCP asynchrone.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--clients", type=int, default=10000)
    parser.add_argument("--number", type=int, default=42)
    parser.add_argument("--max-inflight", type=int, default=2000)
    args = parser.parse_args()

    print(
        f"\n🚀 ASYNC TCP STRESS → {args.host}:{args.port} "
        f"({args.clients} clients, max_inflight={args.max_inflight})\n"
    )

    res = asyncio.run(
        lancer_stress_async(
            args.host,
            args.port,
            args.clients,
            number=args.number,
            max_inflight=args.max_inflight,
        )
    )

    for k, v in res.items():
        print(f"{k:18} : {v}")


if __name__ == "__main__":
    main()

