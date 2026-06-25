#!/usr/bin/env python3
"""Riproduce la Figura 3 di Brandes: tempo vs n, una curva per densita.
Legge risultati.csv (colonne: n,m,densita,tempo_us)."""
import csv
import sys
import matplotlib.pyplot as plt

path = sys.argv[1] if len(sys.argv) > 1 else "risultati.csv"
out = sys.argv[2] if len(sys.argv) > 2 else \
    "/Users/sebastianobecchetti/dev/Algoritmi/brandes/brandes_plot.png"
titolo = sys.argv[3] if len(sys.argv) > 3 else \
    "Brandes: tempo betweenness vs n, per densita"
rows = []
with open(path) as f:
    for r in csv.DictReader(f):
        rows.append((int(r["n"]), int(r["densita"]), float(r["tempo_us"])))

densita = sorted({d for _, d, _ in rows})

plt.figure(figsize=(9, 6))
for d in densita:
    pts = sorted((n, t) for n, dd, t in rows if dd == d)
    if pts:
        xs = [p[0] for p in pts]
        ys = [p[1] / 1e6 for p in pts]  # us -> secondi
        plt.plot(xs, ys, "s-", markersize=4, label=f"{d}%")

plt.xlabel("number of vertices (n)")
plt.ylabel("seconds")
plt.title(titolo)
plt.legend(title="densita", fontsize=8)
plt.grid(True, alpha=0.3)
plt.tight_layout()

plt.savefig(out, dpi=130)
print("salvato:", out)
