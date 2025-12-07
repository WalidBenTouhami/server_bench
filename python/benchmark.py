#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import time
import psutil
import json
import pandas as pd
import os
import threading
from pathlib import Path

from client_stress import lancer_stress_test

TEST_CLIENTS = [10, 50, 100, 200, 300]

ROOT = Path(__file__).resolve().parent.parent
BIN_MONO = ROOT / "bin" / "serveur_mono"
BIN_MULTI = ROOT / "bin" / "serveur_multi"

SERVERS = {
    "mono": {"bin": str(BIN_MONO), "port": 5050},
    "multi": {"bin": str(BIN_MULTI), "port": 5051},
}


def compiler():
    print("[BENCH] Compilation (make clean + make all)…")
    subprocess.run(["make", "clean"], cwd=ROOT, check=True)
    subprocess.run(["make", "all"], cwd=ROOT, check=True)


def lancer_serveur(type_srv: str) -> subprocess.Popen:
    bin_path = SERVERS[type_srv]["bin"]
    proc = subprocess.Popen(
        [bin_path],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1.0)
    return proc


def arreter_serveur(proc: subprocess.Popen):
    proc.terminate()
    try:
        proc.wait(timeout=2.0)
    except subprocess.TimeoutExpired:
        proc.kill()


def monitor_process(pid: int, stop_event: threading.Event, cpu_samples, mem_samples):
    try:
        p = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return
    while not stop_event.is_set():
        try:
            cpu = p.cpu_percent(interval=0.2)
            mem = p.memory_info().rss / (1024 * 1024)
            cpu_samples.append(cpu)
            mem_samples.append(mem)
        except psutil.NoSuchProcess:
            break


def benchmark_serveur(type_srv: str):
    port = SERVERS[type_srv]["port"]
    results = []

    for nclients in TEST_CLIENTS:
        print(f"[BENCH] {type_srv} - {nclients} clients")

        proc = lancer_serveur(type_srv)
        pid = proc.pid

        cpu_samples = []
        mem_samples = []

        stop_evt = threading.Event()
        mon_thread = threading.Thread(
            target=monitor_process,
            args=(pid, stop_evt, cpu_samples, mem_samples),
        )
        mon_thread.start()

        t_start = time.perf_counter()
        res = lancer_stress_test("127.0.0.1", port, nclients)
        t_end = time.perf_counter()

        stop_evt.set()
        mon_thread.join()
        arreter_serveur(proc)

        elapsed = t_end - t_start
        throughput = res["success"] / elapsed if elapsed > 0 else 0.0

        cpu_mean = sum(cpu_samples) / len(cpu_samples) if cpu_samples else None
        mem_mean = sum(mem_samples) / len(mem_samples) if mem_samples else None

        results.append({
            "server": type_srv,
            "clients": nclients,
            "success": res["success"],
            "fail": res["fail"],
            "mean": res["mean"],
            "median": res["median"],
            "p95": res["p95"],
            "p99": res["p99"],
            "max_latency": res["max"],
            "cpu_mean": cpu_mean,
            "mem_mean": mem_mean,
            "throughput_rps": throughput,
            "time_total": elapsed,
        })

    return results


def main():
    os.chdir(ROOT / "python")  # pour générer results.* ici
    compiler()
    final_results = []
    for srv_type in SERVERS.keys():
        r = benchmark_serveur(srv_type)
        final_results.extend(r)

    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(final_results, f, indent=4, ensure_ascii=False)

    df = pd.DataFrame(final_results)
    df.to_excel("results.xlsx", index=False)
    print("[BENCH] Résultats dans python/results.json / python/results.xlsx")


if __name__ == "__main__":
    main()

