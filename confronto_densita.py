#!/usr/bin/env python3
"""Confronto standard O(n^3) vs Brandes O(nm) a parita' di densita'.

Per ciascuna densita' (10%..90%) traccia un pannello con il tempo in funzione di n,
sovrapponendo l'approccio standard (rosso) e l'algoritmo di Brandes (blu) sul range
di n comune. Mette in evidenza come il vantaggio di Brandes dipenda dalla densita'."""
import csv

import matplotlib.pyplot as plt


def leggi(path):
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            rows.append((int(r["n"]), int(r["densita"]), float(r["tempo_us"])))
    return rows


standard = leggi("risultati_standard.csv")
brandes = leggi("risultati.csv")
# range comune: fin dove arriva lo standard (O(n^3) e' limitato a n piccoli)
nmax = max(n for n, _, _ in standard)

densita = sorted({d for _, d, _ in standard})

fig, axes = plt.subplots(3, 3, figsize=(12, 9), sharex=True)
axes = axes.ravel()


def curva(rows, d):
    pts = sorted((n, t) for n, dd, t in rows if dd == d and n <= nmax)
    xs = [p[0] for p in pts]
    ys = [p[1] / 1e6 for p in pts]  # us -> secondi
    return xs, ys


for ax, d in zip(axes, densita):
    xs, ys = curva(standard, d)
    ax.plot(xs, ys, "s-", color="tab:red", markersize=3, label="standard $O(n^3)$")
    xs, ys = curva(brandes, d)
    ax.plot(xs, ys, "o-", color="tab:blue", markersize=3, label="Brandes $O(nm)$")
    ax.set_title(f"densita {d}%", fontsize=10)
    ax.grid(True, alpha=0.3)

# etichette solo sui bordi per non affollare
for i, ax in enumerate(axes):
    if i % 3 == 0:
        ax.set_ylabel("secondi")
    if i >= 6:
        ax.set_xlabel("vertici (n)")

axes[0].legend(fontsize=8)
fig.suptitle("Standard $O(n^3)$ vs Brandes $O(nm)$ per densita crescente", fontsize=13)
fig.tight_layout(rect=[0, 0, 1, 0.97])

out = "tesina/immagini/confronto_densita.png"
fig.savefig(out, dpi=120)
print("salvato:", out)
