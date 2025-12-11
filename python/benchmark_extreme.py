#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
benchmark_extreme.py
Lance une campagne de benchmarks:
- TCP mono (5050) / multi (5051)
- HTTP mono (8080) / multi (8081)
Pour plusieurs charges, génère:
- results_extreme.json
- results_extreme.xlsx
- figures_extreme/*.png
- dashboard_extreme.html (Plotly)
"""

from pathlib import Path
import json

import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

from client_stress_tcp import lancer_stress_test as tcp_stress
from client_stress_http import lancer_stress_http as http_stress

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "figures_extreme"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RESULTS_JSON = ROOT / "results_extreme.json"
RESULTS_XLSX = ROOT / "results_extreme.xlsx"
DASHBOARD_HTML = ROOT / "dashboard_extreme.html"


def run_campaign():
    scenarios = [
        ("tcp_monothread", "tcp", "127.0.0.1", 5050),
        ("tcp_multithread", "tcp", "127.0.0.1", 5051),
        ("http_monothread", "http", "127.0.0.1", 8080),
        ("http_multithread", "http", "127.0.0.1", 8081),
    ]
    loads = [10, 50, 100, 200, 300]

    rows = []
    for name, proto, host, port in scenarios:
        for c in loads:
            print(f"\n[SCENARIO] {name} – {c} clients")
            if proto == "tcp":
                stats = tcp_stress(host, port, clients=c)
            else:
                stats = http_stress(host, port, path="/hello", clients=c)

            stats["scenario"] = name
            stats["protocol"] = proto
            rows.append(stats)

    return rows


def build_reports(rows):
    # JSON
    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=4)
    print(f"[OK] JSON → {RESULTS_JSON}")

    # DataFrame
    df = pd.DataFrame(rows)
    df.to_excel(RESULTS_XLSX, index=False)
    print(f"[OK] XLSX → {RESULTS_XLSX}")

    # Quelques graphiques matplotlib
    for metric in ["throughput_req_s", "mean_ms", "p95_ms"]:
        plt.figure()
        for scenario in df["scenario"].unique():
            sub = df[df["scenario"] == scenario]
            plt.plot(sub["clients"], sub[metric], marker="o", label=scenario)
        plt.xlabel("Clients")
        plt.ylabel(metric)
        plt.title(f"{metric} vs clients")
        plt.legend()
        fig_path = OUT_DIR / f"{metric}.png"
        plt.savefig(fig_path, bbox_inches="tight")
        plt.close()
        print(f"[OK] Figure → {fig_path}")

    # Dashboard Plotly
    fig = px.line(
        df,
        x="clients",
        y="throughput_req_s",
        color="scenario",
        markers=True,
        title="Throughput req/s – Tous scénarios",
    )
    fig.write_html(str(DASHBOARD_HTML))
    print(f"[OK] Dashboard → {DASHBOARD_HTML}")


def main():
    rows = run_campaign()
    build_reports(rows)


if __name__ == "__main__":
    main()

