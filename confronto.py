#!/usr/bin/env python3
"""Confronto standard O(n^3) vs Brandes O(nm): tempo vs n, una curva per densita.
Sovrappone risultati_standard.csv (rosso) e risultati.csv (blu), sul range di n
comune."""
import csv
import sys

import matplotlib.pyplot as plt


def leggi(path):
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            rows.append((int(r["n"]), int(r["densita"]), float(r["tempo_us"])))
    return rows


standard = leggi("risultati_standard.csv")
brandes = leggi("risultati.csv")
nmax = max(n for n, _, _ in standard)  # range comune: fin dove arriva lo standard

plt.figure(figsize=(9, 6))


def disegna(rows, colore, etichetta):
    densita = sorted({d for _, d, _ in rows})
    primo = True
    for d in densita:
        pts = sorted((n, t) for n, dd, t in rows if dd == d and n <= nmax)
        if not pts:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] / 1e6 for p in pts]
        plt.plot(xs, ys, "-", color=colore, alpha=0.6,
                 label=etichetta if primo else None)
        primo = False


disegna(standard, "tab:red", "standard $O(n^3)$")
disegna(brandes, "tab:blue", "Brandes $O(nm)$")

plt.xlabel("number of vertices (n)")
plt.ylabel("seconds")
plt.title("Standard $O(n^3)$ vs Brandes $O(nm)$ (una curva per densita)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()

out = "tesina/immagini/confronto.png"
plt.savefig(out, dpi=130)
print("salvato:", out)
