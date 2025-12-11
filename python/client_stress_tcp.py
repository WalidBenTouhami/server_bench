#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
client_stress_tcp.py
Client de stress TCP pour serveurs:
  - serveur_mono     (port 5050)
  - serveur_multi    (port 5051)

Fonctionnalités:
- Latences (mean, median, p95, p99, max)
- Throughput (req/s)
- Mode simple ou ramp-up (plusieurs niveaux de charge)
- Export JSON / CSV
"""

import socket
import struct
import time
import json
import csv
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List


def envoyer_requete(host: str, port: int, number: int, timeout: float = 5.0) -> float:
    """Envoie une requête TCP simple (int32 -> carré + timestamp) et retourne la latence en ms."""
    start = time.perf_counter()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((host, port))

            # Envoi int32 (network byte order)
            s.sendall(struct.pack("!i", number))

            # Réception résultat (4 octets) + timestamp (8 octets)
            result_raw = s.recv(4)
            ts_raw = s.recv(8)

            if len(result_raw) < 4 or len(ts_raw) < 8:
                return -1.0

    except Exception:
        return -1.0

    end = time.perf_counter()
    return (end - start) * 1000.0  # en ms


def _percentile(sorted_list: List[float], p: float) -> float:
    """Percentile basique (sans interpolation) sur une liste triée."""
    n = len(sorted_list)
    if n == 0:
        return 0.0
    k = int(p * (n - 1))
    return sorted_list[k]


def lancer_stress_test(host: str, port: int, clients: int, number: int = 42) -> Dict:
    """Lance un stress test sur N clients en parallèle (thread pool)."""
    latences: List[float] = []

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=clients) as executor:
        futures = [
            executor.submit(envoyer_requete, host, port, number)
            for _ in range(clients)
        ]
        for f in as_completed(futures):
            lat = f.result()
            if lat >= 0:
                latences.append(lat)
    t1 = time.perf_counter()

    total_time = t1 - t0

    if not latences:
        return {
            "mode": "single",
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

    latences_sorted = sorted(latences)
    n = len(latences_sorted)

    mean = statistics.mean(latences_sorted)
    median = statistics.median(latences_sorted)
    p95 = _percentile(latences_sorted, 0.95)
    p99 = _percentile(latences_sorted, 0.99)
    max_v = max(latences_sorted)
    throughput = len(latences_sorted) / total_time if total_time > 0 else 0.0

    return {
        "mode": "single",
        "host": host,
        "port": port,
        "clients": clients,
        "success": len(latences_sorted),
        "fail": clients - len(latences_sorted),
        "throughput_req_s": round(throughput, 2),
        "mean_ms": round(mean, 3),
        "median_ms": round(median, 3),
        "p95_ms": round(p95, 3),
        "p99_ms": round(p99, 3),
        "max_ms": round(max_v, 3),
    }


def lancer_ramp_up(
    host: str,
    port: int,
    steps: list,
    number: int = 42,
) -> List[Dict]:
    """Lance une série de stress tests avec un ramp-up de clients."""
    results = []
    for c in steps:
        print(f"\n[RAMPU TCP] {c} clients → {host}:{port}")
        stats = lancer_stress_test(host, port, c, number=number)
        stats["mode"] = "ramp"
        results.append(stats)
    return results


def export_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"[EXPORT] JSON → {path}")


def export_csv(path: str, rows: List[Dict]) -> None:
    if not rows:
        return
    fields = list(rows[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[EXPORT] CSV → {path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Client de stress TCP (mono/multi).")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--clients", type=int, default=50)
    parser.add_argument(
        "--ramp",
        type=str,
        help="Liste de charges, ex: 10,50,100,200 (active le mode ramp-up)",
    )
    parser.add_argument("--number", type=int, default=42, help="Nombre envoyé au serveur.")
    parser.add_argument("--json", type=str, help="Fichier JSON de sortie.")
    parser.add_argument("--csv", type=str, help="Fichier CSV de sortie (mode ramp).")

    args = parser.parse_args()

    print(f"\n🚀 TCP STRESS → {args.host}:{args.port}\n")

    if args.ramp:
        steps = [int(x) for x in args.ramp.split(",") if x.strip()]
        results = lancer_ramp_up(args.host, args.port, steps, number=args.number)
        for r in results:
            print(
                f"[{r['clients']} clients] "
                f"mean={r['mean_ms']} ms, p95={r['p95_ms']} ms, thr={r['throughput_req_s']} req/s"
            )
        if args.json:
            export_json(args.json, results)
        if args.csv:
            export_csv(args.csv, results)
    else:
        res = lancer_stress_test(args.host, args.port, args.clients, number=args.number)
        for k, v in res.items():
            print(f"{k:18} : {v}")
        if args.json:
            export_json(args.json, res)


if __name__ == "__main__":
    main()

