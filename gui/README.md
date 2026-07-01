# UI interattiva — Brandes passo-passo

`brandes_ui.py` è un'interfaccia grafica (Tkinter) per **costruire un grafo a
mano** e **visualizzare l'esecuzione dell'algoritmo di Brandes** su grafi non
pesati, un passo alla volta: prima la BFS (calcolo dei cammini minimi), poi
l'accumulo all'indietro delle dipendenze.

## Avvio

Dalla radice del progetto:

```sh
./ui.sh
```

`ui.sh` lancia la UI con il Python di Homebrew (Tk ≥ 8.6). In alternativa, a mano:

```sh
/opt/homebrew/bin/python3.14 gui/brandes_ui.py
```

> ⚠️ **Non** usare il `python3` di sistema su macOS: monta **Tk 8.5**, che non
> consegna correttamente i click sul canvas (sembra che il programma "non faccia
> nulla"). La UI mostra un avviso se gira su Tk < 8.6.

### Se manca il supporto Tk

```sh
brew install python-tk@3.14
```

## Requisiti

- Python 3 con **Tk ≥ 8.6** (`tkinter`, incluso in `python-tk`)
- **Graphviz** (`neato`) — solo per l'esportazione come immagine
  (`brew install graphviz`)

Nessuna dipendenza Python esterna (solo libreria standard).

## Uso

### Costruire il grafo

- **○ Nodo** (modalità attiva di default):
  - clic su area vuota → crea un nodo nel punto cliccato;
  - clic su un nodo esistente → apre il **riquadro informazioni** del nodo.
- **╱ Arco**: clic su un primo nodo, poi su un secondo → crea l'arco fra i due.
- **Pulisci**: svuota il grafo.

Il grafo viene salvato automaticamente a ogni modifica in `grafo_ui.dot`.

### Eseguire l'algoritmo

- **▶ Play** (verde): avvia l'animazione. Durante l'esecuzione diventa grigio.
- **⏸ Pausa**: congela il passo corrente; con Play l'esecuzione riprende da lì.
  A riposo è grigia.
- **Velocità**: cursore in operazioni al secondo (default **0.5**).

Il pannello di sinistra mostra in tempo reale: **sorgente** corrente, **fase**
(`bfs` / `accumulo`), i nodi correnti **v** e **w**, i vettori **Q** (coda),
**S** (pila), **σ** (numero di cammini minimi) e **δ** (dipendenze), oltre al
messaggio del passo (es. la formula di aggiornamento di δ con i numeri).

### Navigatore dei passi

In basso a sinistra, **Passi dell'algoritmo**: l'elenco completo di tutti i passi
dell'esecuzione. Un clic su un passo lo **mostra** (stato del grafo e dei vettori
a quel punto) **senza** avviare l'animazione; da lì Play riprende in avanti.

### Riquadro informazioni del nodo

Cliccando un nodo (in modalità ○ Nodo) compare in alto a sinistra sul grafo un
riquadro con i dati utili a rifare i conti a mano:

- grado e lista dei vicini;
- **betweenness** $C_B$ del nodo (calcolo completo);
- se l'algoritmo è in esecuzione/pausa: per la sorgente corrente, distanza $d$,
  numero di cammini minimi $\sigma$, dipendenza $\delta$ e predecessori nel DAG;
- la **BFS con il nodo come sorgente** (distanze e $\sigma$ verso tutti gli
  altri).

Si chiude con il **✕** in alto a destra del riquadro.

### Esportare

**Esporta** apre un menù testuale:

1. **Esporta come immagine** — rende il grafo con `neato` in PNG;
2. **Esporta il file `.dot`** — salva la descrizione Graphviz.

Entrambe chiedono il percorso tramite il dialog di salvataggio del sistema
operativo.

## Codice colori

| Elemento | Colore |
|----------|--------|
| Cammini minimi (albero/DAG) | **verde** |
| Pila `S` | **rosso** |
| Coda `Q` | **viola** |
| Nodo `v` corrente | bordo blu |
| Nodo `w` corrente / arco in accumulo | arancio |
| Sorgente | bordo nero |
