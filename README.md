# Algoritmo di Brandes per la betweenness centrality

Implementazione in C++ dell'algoritmo di Brandes per il calcolo della
*betweenness centrality* su grafi non orientati, nelle due varianti **non
pesata** (BFS) e **pesata** (Dijkstra), con confronto rispetto all'approccio
classico $O(n^3)$. Il progetto include la generazione di grafi casuali connessi,
la misura sperimentale dei tempi, gli script per i grafici e una **UI
interattiva** per visualizzare l'algoritmo passo-passo.

La documentazione completa (problema, pseudocodice, dimostrazione della relazione
ricorsiva, analisi di complessità, risultati sperimentali) è nella cartella
[`tesina/`](tesina/) — file `main.pdf`.

## Struttura del repository

```
src/
  brandes.cpp            grafi NON pesati  (BFS)        -> binario "b"
  brandes_weighted.cpp   grafi pesati      (Dijkstra)   -> binario "bw"
  standard.cpp           approccio classico O(n^3)      -> binario "standard"
gui/
  brandes_ui.py          UI interattiva (costruzione grafo + animazione)
ui.sh                    avvia la UI con il Python corretto
plot.py                  grafico tempo-vs-n dell'algoritmo di Brandes
confronto.py             grafico standard vs Brandes
confronto_densita.py     grafico standard vs Brandes, un pannello per densità
risultati.csv            output sperimentale (Brandes non pesato)
risultati_w.csv          output sperimentale (Brandes pesato)
risultati_standard.csv   output sperimentale (approccio classico)
grafo*.dot / grafo*.png  grafi di esempio (nodi-ponte in rosso)
tesina/                  elaborato LaTeX + PDF + immagini/
```

I grafi **non** vengono letti da file: sono generati internamente da
`genera_grafo(n, m, seed)`, che costruisce prima uno spanning tree casuale
(garantisce la connessione) e poi aggiunge archi fino a `m`. Nella variante
pesata ogni arco riceve un peso intero casuale in `[1, 10]`.

## Dipendenze

| Strumento | Serve per | Installazione (macOS) |
|-----------|-----------|------------------------|
| Compilatore C++17 (`g++`/`clang++`) | compilare i sorgenti | — |
| Graphviz (`neato`) | rendere i `.dot` in `.png` | `brew install graphviz` |
| Python 3 + `matplotlib` | grafici dei tempi | `pip install matplotlib` |
| Python 3 con Tk ≥ 8.6 | UI interattiva | `brew install python-tk@3.14` |

Se `neato` non è installato la generazione del `.png` fallisce silenziosamente,
ma i file `.dot` e i CSV vengono comunque prodotti.

## Compilazione

```sh
g++ -O2 -std=c++17 -o src/b        src/brandes.cpp
g++ -O2 -std=c++17 -o src/bw       src/brandes_weighted.cpp
g++ -O2 -std=c++17 -o src/standard src/standard.cpp
```

L'opzione `-O2` è quella con cui sono misurati i tempi della tesina. Per la
massima velocità su questa macchina si può usare
`-O3 -march=native -funroll-loops`.

## Esecuzione

Nessun programma richiede argomenti:

```sh
./src/b          # Brandes non pesato
./src/bw         # Brandes pesato
./src/standard   # approccio classico O(n^3)
```

Ogni esecuzione:

1. esegue un breve **warm-up** (gira a vuoto per stabilizzare la frequenza CPU);
2. fa lo sweep sperimentale — densità dal 10% al 90%, `n` da 100 a 2000 —
   cronometrando la sola chiamata all'algoritmo e scrivendo i tempi nel CSV;
3. (solo `b` e `bw`) genera un grafo di esempio (`n=20`), stampa i nodi-ponte
   (top 20% per betweenness) e ne scrive il `.dot` + `.png`.

| Programma | CSV prodotto | Grafo di esempio |
|-----------|--------------|------------------|
| `b`        | `risultati.csv`          | `grafo.dot`, `grafo.png` |
| `bw`       | `risultati_w.csv`        | `grafo_w.dot`, `grafo_w.png` |
| `standard` | `risultati_standard.csv` | — |

Colonne dei CSV: `n,m,densita,tempo_us` (tempo = minimo su più ripetizioni, in
microsecondi). Lo sweep fino a `n=2000` può richiedere parecchi minuti (le
densità alte sono le più lente): ridurre il limite di `n` nel `main` per prove
rapide.

## Grafici dei tempi (Python)

Da eseguire **dopo** aver prodotto i CSV con gli eseguibili:

```sh
python3 plot.py                  # brandes_plot.png  <- risultati.csv
python3 confronto.py             # tesina/immagini/confronto.png
python3 confronto_densita.py     # tesina/immagini/confronto_densita.png
```

- `plot.py` riproduce la Figura 3 di Brandes (tempo vs `n`, una curva per
  densità). Accetta argomenti opzionali: `plot.py [input.csv] [output.png] [titolo]`.
- `confronto.py` e `confronto_densita.py` sovrappongono l'approccio standard
  $O(n^3)$ (richiedono `risultati_standard.csv`) all'algoritmo di Brandes.

## UI interattiva

Costruisci un grafo a mano e osserva l'esecuzione di Brandes passo-passo
(BFS + accumulo all'indietro delle dipendenze).

```sh
./ui.sh
```

`ui.sh` avvia la UI con il Python di Homebrew (Tk 9). **Non** usare il `python3`
di sistema su macOS: monta Tk 8.5, che non consegna bene i click sul canvas. Se
manca il supporto Tk: `brew install python-tk@3.14`.

### Comandi

- **○ Nodo** — clic su area vuota: crea un nodo; clic su un nodo esistente: apre
  un riquadro con i suoi dati (grado, $C_B$ e, durante l'esecuzione, $d$,
  $\sigma$, $\delta$, predecessori nel DAG).
- **╱ Arco** — clic su due nodi: crea l'arco.
- **Esporta** — menù: 1) immagine via `neato`; 2) file `.dot`; entrambi con il
  dialog di salvataggio del sistema.
- **Pulisci** — svuota il grafo.
- **▶ Play / ⏸ Pausa** — avvia/ferma l'animazione; la pausa congela il passo
  corrente, Play riprende da lì.
- **Velocità** — operazioni al secondo (default 0.5).
- **Passi dell'algoritmo** (in basso a sinistra) — elenco di tutti i passi; un
  clic mostra quel passo senza avviare l'animazione.

Codice colori: cammini minimi = **verde**, pila $S$ = **rosso**, coda $Q$ =
**viola**. Il grafo viene salvato a ogni modifica in `grafo_ui.dot`.

## Tesina

```sh
cd tesina
latexmk -pdf main.tex     # produce main.pdf
```

## Verifica di correttezza

I valori di betweenness sono stati validati contro
`networkx.betweenness_centrality` (`normalized=False`, e `weight=...` per il caso
pesato): coincidono a meno del rumore in virgola mobile (~`1e-11`). Vedi il
Capitolo 3 della tesina per i dettagli.
