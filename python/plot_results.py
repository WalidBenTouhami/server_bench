#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import matplotlib.pyplot as plt
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "figures"
OUTPUT.mkdir(exist_ok=True)


def load_results():
    df = pd.read_excel(ROOT / "results.xlsx")
    mono = df[df.server == "mono"]
    multi = df[df.server == "multi"]
    return mono, multi


def save_figure(name: str):
    png_path = OUTPUT / f"{name}.png"
    svg_path = OUTPUT / f"{name}.svg"
    plt.tight_layout()
    plt.savefig(png_path, dpi=160)
    plt.savefig(svg_path)
    plt.close()
    print(f"[PLOT] {png_path} + {svg_path}")


def graph_throughput(mono, multi):
    plt.figure(figsize=(8, 5))
    plt.plot(mono.clients, mono.throughput_rps, marker="o", label="Mono-thread")
    plt.plot(multi.clients, multi.throughput_rps, marker="o", label="Multi-thread")
    plt.xlabel("Clients")
    plt.ylabel("Débit (req/s)")
    plt.title("Débit VS nombre de clients")
    plt.legend()
    save_figure("1-throughput")


def graph_latency_p99(mono, multi):
    plt.figure(figsize=(8, 5))
    plt.plot(mono.clients, mono.p99, marker="o", label="Mono-thread")
    plt.plot(multi.clients, multi.p99, marker="o", label="Multi-thread")
    plt.xlabel("Clients")
    plt.ylabel("Latence P99 (ms)")
    plt.title("Latence P99 VS nombre de clients")
    plt.legend()
    save_figure("2-latency_p99")


def graph_cpu(mono, multi):
    plt.figure(figsize=(8, 5))
    plt.plot(mono.clients, mono.cpu_mean, marker="o", label="Mono-thread")
    plt.plot(multi.clients, multi.cpu_mean, marker="o", label="Multi-thread")
    plt.xlabel("Clients")
    plt.ylabel("CPU moyen (%)")
    plt.title("CPU moyen")
    plt.legend()
    save_figure("3-cpu")


def graph_memory(mono, multi):
    plt.figure(figsize=(8, 5))
    plt.plot(mono.clients, mono.mem_mean, marker="o", label="Mono-thread")
    plt.plot(multi.clients, multi.mem_mean, marker="o", label="Multi-thread")
    plt.xlabel("Clients")
    plt.ylabel("Mémoire (MB)")
    plt.title("Mémoire RSS")
    plt.legend()
    save_figure("4-memory")


def graph_speedup(mono, multi):
    plt.figure(figsize=(8, 5))
    speedup = multi.throughput_rps.values / mono.throughput_rps.values
    plt.plot(mono.clients, speedup, marker="o")
    plt.axhline(1.0)
    plt.xlabel("Clients")
    plt.ylabel("Speedup (multi/mono)")
    plt.title("Speedup multi-thread")
    save_figure("5-speedup")


def graph_saturation(mono, multi):
    plt.figure(figsize=(8, 5))
    plt.plot(mono.clients, mono.cpu_mean, marker="o", linestyle="--", label="Mono-thread")
    plt.plot(multi.clients, multi.cpu_mean, marker="o", linestyle="--", label="Multi-thread")
    plt.xlabel("Clients")
    plt.ylabel("CPU (%)")
    plt.title("Saturation CPU")
    plt.legend()
    save_figure("6-saturation")


def main():
    mono, multi = load_results()
    graph_throughput(mono, multi)
    graph_latency_p99(mono, multi)
    graph_cpu(mono, multi)
    graph_memory(mono, multi)
    graph_speedup(mono, multi)
    graph_saturation(mono, multi)
    print("[PLOT] Graphiques PNG + SVG générés dans python/figures/")


if __name__ == "__main__":
    main()

