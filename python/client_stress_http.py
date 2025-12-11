#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
client_stress_http.py
Stress HTTP pour:
  - serveur_mono_http   (port 8080)
  - serveur_multi_http  (port 8081)

Envoie des requêtes GET et mesure la latence et le throughput.
"""

import socket
import time
import json
import csv
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List


def envoyer_requete_http(host: str, port: int, path: str, timeout: float = 5.0) -> float:
    """Envoie une requête HTTP GET et retourne la latence en ms."""
    start = time.perf_counter()
    try:
        req = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).encode("ascii")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((host, port))
            s.sendall(req)

            # Lecture simple jusqu'à fermeture
            while True:
                data = s.recv(4096)
                if not data:
                    break

    except Exception:
        return -1.0

    end = time.perf_counter()
    return (end - start) * 1000.0


def _percentile(sorted_list: List[float], p: float) -> float:
    n = len(sorted_list)
    if n == 0:
        return 0.0
    k = int(p * (n - 1))
    return sorted_list[k]


def lancer_stress_http(host: str, port: int, path: str, clients: int) -> Dict:
    latences: List[float] = []

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=clients) as executor:
        futures = [
            executor.submit(envoyer_requete_http, host, port, path)
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
            "path": path,
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
        "path": path,
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


def lancer_ramp_up_http(
    host: str,
    port: int,
    path: str,
    steps: List[int],
) -> List[Dict]:
    results = []
    for c in steps:
        print(f"\n[RAMPU HTTP] {c} clients → {host}:{port}{path}")
        stats = lancer_stress_http(host, port, path, c)
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

    parser = argparse.ArgumentParser(description="Client de stress HTTP (mono/multi).")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--path", default="/hello")
    parser.add_argument("--clients", type=int, default=50)
    parser.add_argument(
        "--ramp",
        type=str,
        help="Liste de charges, ex: 10,50,100,200 (mode ramp-up).",
    )
    parser.add_argument("--json", type=str, help="Export JSON.")
    parser.add_argument("--csv", type=str, help="Export CSV (mode ramp).")

    args = parser.parse_args()

    print(f"\n🚀 HTTP STRESS → {args.host}:{args.port}{args.path}\n")

    if args.ramp:
        steps = [int(x) for x in args.ramp.split(",") if x.strip()]
        results = lancer_ramp_up_http(args.host, args.port, args.path, steps)
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
        res = lancer_stress_http(args.host, args.port, args.path, args.clients)
        for k, v in res.items():
            print(f"{k:18} : {v}")
        if args.json:
            export_json(args.json, res)


if __name__ == "__main__":
    main()

