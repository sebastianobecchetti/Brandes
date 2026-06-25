# Algoritmo di Brandes per la betweenness centrality

Implementazione in C++ dell'algoritmo di Brandes per il calcolo della
*betweenness centrality* su grafi non orientati, nelle due varianti **non
pesata** (BFS) e **pesata** (Dijkstra). Il progetto include la generazione di
grafi casuali connessi, la misura sperimentale dei tempi di esecuzione e la
produzione dei grafici e delle visualizzazioni usate nella tesina.

La documentazione completa (problema, pseudocodice, analisi di complessità,
risultati sperimentali) è nella cartella [`tesina/`](tesina/) — file
`main.pdf`.

## Struttura del repository

```
src/
  brandes.cpp            grafi NON pesati  (BFS)        -> binario "b"
  brandes_weighted.cpp   grafi pesati      (Dijkstra)   -> binario "bw"
plot.py                  genera i grafici tempo-vs-n dai CSV
risultati.csv            output sperimentale (caso non pesato)
risultati_w.csv          output sperimentale (caso pesato)
grafo.dot / grafo.png    grafo di esempio non pesato (nodi-ponte in rosso)
grafo_w.dot / grafo_w.png   grafo di esempio pesato
tesina/                  elaborato LaTeX + PDF
```

I grafi **non** vengono letti da file: sono generati internamente dalla
funzione `genera_grafo(n, m, seed)`, che costruisce prima uno spanning tree
casuale (garantisce la connessione) e poi aggiunge archi fino a `m`. Nella
variante pesata ogni arco riceve un peso intero casuale in `[1, 10]`.

## Dipendenze

- **Compilatore C++17** (`g++` o `clang++`) — uso di structured bindings.
- **Graphviz** (comando `neato`) — i programmi lo invocano per rendere il
  `.dot` in `.png`. Su macOS: `brew install graphviz`.
- **Python 3** con **matplotlib** — solo per `plot.py`:
  `pip install matplotlib`.

Se `neato` non è installato la generazione del `.png` fallisce silenziosamente,
ma il file `.dot` e i CSV vengono comunque prodotti.

## Compilazione

```sh
# caso non pesato
g++ -O2 -std=c++17 -o src/b  src/brandes.cpp

# caso pesato
g++ -O2 -std=c++17 -o src/bw src/brandes_weighted.cpp
```

L'opzione `-O2` è consigliata: i tempi riportati nella tesina sono misurati con
le ottimizzazioni del compilatore attive.

## Esecuzione

Entrambi i programmi non richiedono argomenti:

```sh
./src/b      # non pesato
./src/bw     # pesato
```

Ogni esecuzione:

1. esegue un breve **warm-up** (gira a vuoto per stabilizzare la frequenza CPU);
2. fa lo sweep sperimentale — densità dal 10% al 90%, `n` da 100 a 2000 —
   cronometrando la sola chiamata a `brandes` e scrivendo i tempi nel CSV
   (`risultati.csv` per `b`, `risultati_w.csv` per `bw`);
3. genera un grafo di esempio (`n=20`), stampa i nodi-ponte (top 20% per
   betweenness) e scrive il `.dot` + il `.png` corrispondente.

Su CPU non recenti lo sweep fino a `n=2000` può richiedere alcuni minuti
(soprattutto la variante pesata): ridurre il limite superiore di `n` nel `main`
per prove più rapide.

## Generazione dei grafici

`plot.py` legge un CSV e produce il grafico tempo-vs-`n` (una curva per densità):

```sh
# usa i default: legge risultati.csv, salva brandes_plot.png
python3 plot.py

# oppure esplicito: CSV in input, PNG in output, titolo
python3 plot.py risultati_w.csv brandes_plot_w.png "Brandes pesato: tempo vs n"
```

Argomenti posizionali: `plot.py [input.csv] [output.png] [titolo]`.

## Verifica di correttezza

I valori di betweenness sono stati validati contro la funzione
`networkx.betweenness_centrality` (opzione `normalized=False`, e `weight=...`
per il caso pesato): coincidono a meno del rumore in virgola mobile
(~`1e-11`). Vedi Capitolo 3 della tesina per i dettagli.
