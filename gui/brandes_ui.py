#!/usr/bin/env python3
"""UI interattiva per costruire un grafo e visualizzare passo-passo l'algoritmo
di Brandes (betweenness centrality) su grafi non pesati.

- Barra in alto: modalita' "nodo" (cerchio) e "arco" (segmento), Esporta, Pulisci.
- Colonna sinistra: Play/Pausa, velocita' (op/s), stato dei vettori (Q, S, sigma,
  delta), sorgente, fase e nodi correnti v e w; in basso il navigatore dei passi.
- Il grafo viene salvato a ogni modifica in un file .dot.
- Codice colori: cammini minimi = verde, pila S = rosso, coda Q = viola.
- Se NON si sta eseguendo l'algoritmo, cliccando un nodo si mostrano i cammini
  minimi (albero BFS) da quel nodo.
"""
import os
import subprocess
import tkinter as tk
from collections import deque
from tkinter import filedialog, messagebox

# ---- parametri grafici --------------------------------------------------------
R = 24                       # raggio dei nodi
DOT_FILE = "grafo_ui.dot"    # autosalvataggio a ogni modifica

BG = "white"           # sfondo uniforme della UI
FG = "#1a1a1a"         # colore testo (esplicito: in dark mode il default e' bianco)
COL_BASE = "#d9d9d9"   # nodo normale (grigio)
COL_QUEUE = "#9b59b6"  # coda Q (viola)
COL_STACK = "#e74c3c"  # pila S (rosso)
COL_PATH = "#27ae60"   # cammini minimi (verde)
COL_V = "#2980b9"      # bordo del nodo v corrente (blu)
COL_W = "#e67e22"      # bordo del nodo w corrente (arancio)
COL_SRC = "#000000"    # bordo della sorgente


class App:
    def __init__(self, root):
        self.root = root
        root.title("Brandes - costruzione e visualizzazione")

        # stato del grafo
        self.nodi = []          # lista di [x, y]; l'indice e' l'id del nodo
        self.adj = []           # adj[i] = set degli adiacenti di i
        self.modo = "nodo"      # "nodo" | "arco"
        self.arco_primo = None  # primo estremo selezionato in modalita' arco

        # stato dell'esecuzione
        self.passi = None       # lista dei passi precomputati (o None)
        self.idx = -1           # indice del passo corrente
        self.in_play = False
        self.after_id = None
        self.stato = None       # passo correntemente mostrato
        self.evidenzia_path = set()  # archi verdi quando non si esegue
        self.info_box = None    # righe del riquadro info nodo (o None)

        self._costruisci_ui()
        self._salva_dot()

    # ---- costruzione interfaccia ---------------------------------------------
    def _costruisci_ui(self):
        self.root.config(bg=BG)

        def lbl(parent, **kw):
            kw.setdefault("bg", BG)
            kw.setdefault("fg", FG)  # fg esplicito: in dark mode il default e' bianco
            return tk.Label(parent, **kw)

        # barra superiore
        top = tk.Frame(self.root, bg=BG, highlightbackground="#ccc",
                       highlightthickness=1)
        top.pack(side="top", fill="x")
        self.btn_nodo = tk.Button(top, text="○  Nodo", width=10,
                                  highlightbackground=BG,
                                  command=lambda: self._set_modo("nodo"))
        self.btn_nodo.pack(side="left", padx=4, pady=4)
        self.btn_arco = tk.Button(top, text="╱  Arco", width=10,
                                  highlightbackground=BG,
                                  command=lambda: self._set_modo("arco"))
        self.btn_arco.pack(side="left", padx=4, pady=4)
        tk.Button(top, text="Esporta", width=10, highlightbackground=BG,
                  command=self._menu_esporta).pack(side="left", padx=4, pady=4)
        tk.Button(top, text="Pulisci", width=10, highlightbackground=BG,
                  command=self._pulisci).pack(side="left", padx=4, pady=4)

        # colonna sinistra
        left = tk.Frame(self.root, bg=BG, width=280,
                        highlightbackground="#ccc", highlightthickness=1)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        # --- navigatore dei passi (in basso, stile Overleaf) ---
        nav = tk.Frame(left, bg=BG)
        nav.pack(side="bottom", fill="both", expand=True, padx=6, pady=(4, 8))
        lbl(nav, text="Passi dell'algoritmo", anchor="w",
            font=("TkDefaultFont", 10, "bold")).pack(fill="x")
        cont = tk.Frame(nav, bg=BG)
        cont.pack(fill="both", expand=True)
        sb = tk.Scrollbar(cont, orient="vertical")
        sb.pack(side="right", fill="y")
        self.lista = tk.Listbox(cont, bg="white", fg=FG, activestyle="none",
                                height=6, highlightthickness=1,
                                highlightbackground="#ccc",
                                selectbackground="#cfe8ff",
                                selectforeground="black",
                                yscrollcommand=sb.set, exportselection=False)
        self.lista.pack(side="left", fill="both", expand=True)
        sb.config(command=self.lista.yview)
        self.lista.bind("<<ListboxSelect>>", self._click_passo)

        # --- pannello superiore (controlli + stato) ---
        pan = tk.Frame(left, bg=BG)
        pan.pack(side="top", fill="x")

        # Play/Pausa come Label colorati: su macOS i tk.Button ignorano il
        # colore di sfondo, percio' si usano Label (che lo rispettano).
        barra = tk.Frame(pan, bg=BG)
        barra.pack(fill="x", padx=8, pady=(10, 4))
        self.btn_play = tk.Label(barra, text="▶  Play", fg="white",
                                 font=("TkDefaultFont", 12, "bold"),
                                 padx=10, pady=7, cursor="hand2")
        self.btn_play.pack(side="left", expand=True, fill="x", padx=(0, 3))
        self.btn_play.bind("<Button-1>",
                           lambda e: (None if self.in_play else self._play()))
        self.btn_pausa = tk.Label(barra, text="⏸  Pausa", fg="white",
                                  font=("TkDefaultFont", 12, "bold"),
                                  padx=10, pady=7, cursor="hand2")
        self.btn_pausa.pack(side="left", expand=True, fill="x", padx=(3, 0))
        self.btn_pausa.bind("<Button-1>",
                            lambda e: (self._pausa() if self.in_play else None))

        lbl(pan, text="Velocita' (operazioni/s)").pack(anchor="w", padx=8)
        self.speed = tk.Scale(pan, from_=0.5, to=10, resolution=0.5,
                              orient="horizontal", bg=BG, fg=FG,
                              highlightbackground=BG, troughcolor="#e6e6e6")
        self.speed.set(0.5)
        self.speed.pack(fill="x", padx=8)

        tk.Frame(pan, height=1, bg="#ddd").pack(fill="x", pady=8)

        self.lbl_sorgente = lbl(pan, text="sorgente: -", anchor="w",
                                font=("TkDefaultFont", 10, "bold"))
        self.lbl_sorgente.pack(fill="x", padx=8)
        self.lbl_fase = lbl(pan, text="fase: -", anchor="w")
        self.lbl_fase.pack(fill="x", padx=8)
        self.lbl_v = lbl(pan, text="v: -", anchor="w", fg=COL_V)
        self.lbl_v.pack(fill="x", padx=8)
        self.lbl_w = lbl(pan, text="w: -", anchor="w", fg=COL_W)
        self.lbl_w.pack(fill="x", padx=8)

        lbl(pan, text="Q (coda BFS)", anchor="w", fg=COL_QUEUE,
            font=("TkDefaultFont", 10, "bold")).pack(fill="x", padx=8,
                                                     pady=(6, 0))
        self.lbl_Q = lbl(pan, text="[]", anchor="w", wraplength=230,
                         justify="left")
        self.lbl_Q.pack(fill="x", padx=8)
        lbl(pan, text="S (pila)", anchor="w", fg=COL_STACK,
            font=("TkDefaultFont", 10, "bold")).pack(fill="x", padx=8,
                                                     pady=(6, 0))
        self.lbl_S = lbl(pan, text="[]", anchor="w", wraplength=230,
                         justify="left")
        self.lbl_S.pack(fill="x", padx=8)

        self.lbl_sigma = lbl(pan, text="σ: -", anchor="w", wraplength=230,
                             justify="left")
        self.lbl_sigma.pack(fill="x", padx=8, pady=(6, 0))
        self.lbl_delta = lbl(pan, text="δ: -", anchor="w", wraplength=230,
                             justify="left")
        self.lbl_delta.pack(fill="x", padx=8)

        self.lbl_info = lbl(pan, text="", anchor="w", wraplength=230,
                            justify="left", fg="#333")
        self.lbl_info.pack(fill="x", padx=8, pady=(8, 0))

        # area di disegno
        self.canvas = tk.Canvas(self.root, bg="white", width=760, height=560,
                                highlightthickness=0)
        self.canvas.pack(side="right", fill="both", expand=True)
        self.canvas.bind("<Button-1>", self._click_canvas)

        self._set_modo("nodo")
        self._set_controlli()
        self._aggiorna_pannello()

    # ---- gestione modalita' ---------------------------------------------------
    def _set_modo(self, modo):
        self.modo = modo
        self.arco_primo = None
        self.btn_nodo.config(relief="sunken" if modo == "nodo" else "raised")
        self.btn_arco.config(relief="sunken" if modo == "arco" else "raised")
        self._disegna()

    def _nodo_sotto(self, x, y):
        for i, (nx, ny) in enumerate(self.nodi):
            if (nx - x) ** 2 + (ny - y) ** 2 <= R * R:
                return i
        return None

    def _invalida(self):
        # il grafo e' cambiato: i passi precomputati non valgono piu'
        self._pausa()
        self.passi = None
        self.idx = -1
        self.stato = None
        self.info_box = None
        self.lista.delete(0, "end")

    # ---- interazione col canvas ----------------------------------------------
    def _click_canvas(self, ev):
        if self.in_play:
            return
        i = self._nodo_sotto(ev.x, ev.y)

        if self.modo == "nodo":
            if i is None:
                self.nodi.append([ev.x, ev.y])
                self.adj.append(set())
                self.evidenzia_path = set()
                self._invalida()
                self._salva_dot()
                self._disegna()
                self._aggiorna_pannello()
            else:
                self._info_nodo(i)
            return

        if self.modo == "arco":
            if i is None:
                self.arco_primo = None
                self._disegna()
                return
            if self.arco_primo is None:
                self.arco_primo = i
            elif self.arco_primo != i:
                a, b = self.arco_primo, i
                self.adj[a].add(b)
                self.adj[b].add(a)
                self.arco_primo = None
                self._invalida()
                self._salva_dot()
            else:
                self.arco_primo = None
            self._disegna()
            return

    def _bfs_sigma(self, s):
        # BFS da s: distanze d (None se irraggiungibile) e numero di cammini
        # minimi sigma da s a ciascun nodo.
        n = len(self.nodi)
        d = [None] * n
        sig = [0] * n
        d[s] = 0
        sig[s] = 1
        Q = deque([s])
        while Q:
            v = Q.popleft()
            for w in self.adj[v]:
                if d[w] is None:
                    d[w] = d[v] + 1
                    Q.append(w)
                if d[w] == d[v] + 1:
                    sig[w] += sig[v]
        return d, sig

    def _calcola_cb(self):
        # Betweenness centrality completa (algoritmo di Brandes, senza passi).
        n = len(self.nodi)
        CB = [0.0] * n
        for s in range(n):
            d = [-1] * n
            sig = [0] * n
            delta = [0.0] * n
            d[s] = 0
            sig[s] = 1
            Q = deque([s])
            S = []
            while Q:
                v = Q.popleft()
                S.append(v)
                for w in self.adj[v]:
                    if d[w] == -1:
                        d[w] = d[v] + 1
                        Q.append(w)
                    if d[w] == d[v] + 1:
                        sig[w] += sig[v]
            while S:
                w = S.pop()
                for v in self.adj[w]:
                    if d[v] == d[w] - 1:
                        delta[v] += sig[v] / sig[w] * (1 + delta[w])
                if w != s:
                    CB[w] += delta[w]
        return [c / 2.0 for c in CB]

    def _info_nodo(self, k):
        # evidenzia l'albero dei cammini minimi con k come sorgente
        d, sig = self._bfs_sigma(k)
        archi = set()
        for v in range(len(self.nodi)):
            for w in self.adj[v]:
                if d[v] is not None and d[w] is not None and d[w] == d[v] + 1:
                    archi.add((min(v, w), max(v, w)))
        self.evidenzia_path = archi

        cb = self._calcola_cb()
        R = []
        R.append("NODO %d" % k)
        R.append("grado %d   vicini %s" % (len(self.adj[k]),
                                           sorted(self.adj[k])))
        R.append("betweenness CB[%d] = %.3f" % (k, cb[k]))

        st = self.stato
        if st and st.get("fase") != "fine" and st.get("s") is not None:
            s = st["s"]
            dk = st["d"].get(k)
            sk = st["sigma"].get(k)
            dek = st["delta"].get(k, 0.0)
            pred = [v for v in sorted(self.adj[k])
                    if st["d"].get(v) is not None and dk is not None
                    and st["d"][v] == dk - 1]
            R.append("")
            R.append("stato corrente  (sorgente s=%d)" % s)
            R.append("  d[%d]=%s   sigma[%d]=%s   delta[%d]=%.2f" %
                     (k, "inf" if dk is None else dk, k, sk, k, dek))
            R.append("  predecessori nel DAG: %s" % pred)

        R.append("")
        R.append("BFS con %d come sorgente:" % k)
        for i in range(len(self.nodi)):
            R.append("  nodo %d:  d=%s   sigma=%d" %
                     (i, "inf" if d[i] is None else d[i], sig[i]))
        self.info_box = R
        self._disegna()

    # ---- disegno --------------------------------------------------------------
    def _disegna(self, distanze=None):
        c = self.canvas
        c.delete("all")
        st = self.stato

        in_Q = set(st["Q"]) if st else set()
        in_S = set(st["S"]) if st else set()
        archi_verdi = set(st["tree"]) if st else set(self.evidenzia_path)
        # arco evidenziato durante l'accumulo (w <- v)
        arco_acc = None
        if st and st.get("fase") == "accumulo" and st.get("v") is not None \
                and st.get("w") is not None:
            arco_acc = (min(st["v"], st["w"]), max(st["v"], st["w"]))

        for v in range(len(self.nodi)):
            for w in self.adj[v]:
                if v < w:
                    key = (v, w)
                    col, larg = "#888", 1
                    if key in archi_verdi:
                        col, larg = COL_PATH, 3
                    if key == arco_acc:
                        col, larg = COL_W, 4
                    x1, y1 = self.nodi[v]
                    x2, y2 = self.nodi[w]
                    c.create_line(x1, y1, x2, y2, fill=col, width=larg)

        if self.arco_primo is not None:
            x, y = self.nodi[self.arco_primo]
            c.create_oval(x - R - 4, y - R - 4, x + R + 4, y + R + 4,
                          outline=COL_V, width=2, dash=(3, 2))

        for i, (x, y) in enumerate(self.nodi):
            fill = COL_BASE
            if i in in_S:
                fill = COL_STACK
            elif i in in_Q:
                fill = COL_QUEUE

            bordo, sp = "#333", 1
            if st:
                if i == st.get("s"):
                    bordo, sp = COL_SRC, 3
                if i == st.get("w"):
                    bordo, sp = COL_W, 4
                if i == st.get("v"):
                    bordo, sp = COL_V, 4

            c.create_oval(x - R, y - R, x + R, y + R, fill=fill,
                          outline=bordo, width=sp)

            # etichetta: id + (durante BFS) distanza, (durante accumulo) delta
            riga2 = ""
            if distanze is not None and distanze[i] is not None:
                riga2 = "d=" + str(distanze[i])
            elif st:
                if st.get("fase") in ("accumulo", "fine"):
                    riga2 = "δ=" + format(st["delta"].get(i, 0.0), ".1f")
                elif st["d"].get(i) is not None:
                    riga2 = "d=" + str(st["d"][i])
            fg = "white" if fill in (COL_STACK, COL_QUEUE) else "black"
            c.create_text(x, y - 5, text=str(i), fill=fg,
                          font=("TkDefaultFont", 11, "bold"))
            if riga2:
                c.create_text(x, y + 9, text=riga2, fill=fg,
                              font=("TkDefaultFont", 8))

        # riquadro info nodo, in alto a sinistra sul canvas
        if self.info_box:
            txt = "\n".join(self.info_box)
            tid = c.create_text(22, 18, anchor="nw", text=txt, fill=FG,
                                font=("Menlo", 11))
            bb = c.bbox(tid)
            rid = c.create_rectangle(bb[0] - 8, bb[1] - 8, bb[2] + 10,
                                     bb[3] + 8, fill="#f6f8fa", outline="#bbb")
            c.tag_lower(rid, tid)
            # pulsante di chiusura "✕"
            cx, cy = bb[2] + 2, bb[1] - 6
            cid = c.create_text(cx, cy, text="✕", fill="#888",
                                font=("TkDefaultFont", 11, "bold"),
                                tags=("chiudi_info",))
            c.tag_raise(cid, rid)
            c.tag_bind("chiudi_info", "<Button-1>", self._chiudi_info)

    def _chiudi_info(self, _ev=None):
        self.info_box = None
        self.evidenzia_path = set()
        self._disegna()
        return "break"  # non propagare il click al canvas (evita nuovo nodo)

    # ---- pannello di stato ----------------------------------------------------
    def _aggiorna_pannello(self):
        st = self.stato
        if not st:
            for w, t in ((self.lbl_sorgente, "sorgente: -"),
                         (self.lbl_fase, "fase: -"), (self.lbl_v, "v: -"),
                         (self.lbl_w, "w: -"), (self.lbl_Q, "[]"),
                         (self.lbl_S, "[]"), (self.lbl_sigma, "σ: -"),
                         (self.lbl_delta, "δ: -")):
                w.config(text=t)
            return
        self.lbl_sorgente.config(text="sorgente: " + str(st.get("s")))
        self.lbl_fase.config(text="fase: " + st.get("fase", "-"))
        self.lbl_v.config(text="v: " + ("-" if st.get("v") is None
                                        else str(st["v"])))
        self.lbl_w.config(text="w: " + ("-" if st.get("w") is None
                                        else str(st["w"])))
        self.lbl_Q.config(text=str(list(st["Q"])))
        self.lbl_S.config(text=str(list(st["S"])))
        self.lbl_sigma.config(text="σ: " + self._fmt_vec(st["sigma"], 0))
        self.lbl_delta.config(text="δ: " + self._fmt_vec(st["delta"], 1))

    def _fmt_vec(self, vec, dec):
        return "[" + ", ".join(format(vec.get(i, 0), "." + str(dec) + "f")
                               for i in range(len(self.nodi))) + "]"

    # ---- esecuzione di Brandes come generatore di passi ----------------------
    def _genera_passi(self):
        n = len(self.nodi)
        CB = [0.0] * n
        for s in range(n):
            d = [-1] * n
            sigma = [0] * n
            delta = [0.0] * n
            d[s] = 0
            sigma[s] = 1
            Q = deque([s])
            S = []
            tree = set()
            yield self._snap("bfs", s, None, None, Q, S, d, sigma, delta, tree,
                             "Sorgente " + str(s) + ": inizio BFS, σ[" +
                             str(s) + "]=1")

            while Q:
                v = Q.popleft()
                S.append(v)
                yield self._snap("bfs", s, v, None, Q, S, d, sigma, delta, tree,
                                 "Estraggo v=" + str(v) + " da Q e lo impilo in S")
                for w in self.adj[v]:
                    nuovo = d[w] == -1
                    if nuovo:
                        d[w] = d[v] + 1
                        Q.append(w)
                    if d[w] == d[v] + 1:
                        sigma[w] += sigma[v]
                        tree.add((min(v, w), max(v, w)))
                        msg = ("w=" + str(w) + ": d=" + str(d[w]) +
                               ", σ[" + str(w) + "]+=σ[" + str(v) + "] -> " +
                               str(sigma[w]))
                    else:
                        msg = "w=" + str(w) + ": gia' visitato, nessun aggiornamento"
                    yield self._snap("bfs", s, v, w, Q, S, d, sigma, delta,
                                     tree, msg)

            # accumulo all'indietro: la dipendenza si propaga dai piu' lontani
            yield self._snap("accumulo", s, None, None, Q, S, d, sigma, delta,
                             tree, "Inizio accumulo: svuoto S dai nodi piu' "
                             "lontani verso la sorgente")
            while S:
                w = S.pop()
                yield self._snap("accumulo", s, None, w, Q, S, d, sigma, delta,
                                 tree, "Estraggo w=" + str(w) + " da S")
                for v in self.adj[w]:
                    if d[v] == d[w] - 1:
                        old = delta[v]
                        contrib = sigma[v] / sigma[w] * (1 + delta[w])
                        delta[v] += contrib
                        # prima riga: il contributo di QUESTO arco w->v
                        # seconda riga: somma con quanto gia' accumulato in δ[v]
                        msg = ("contributo da w=" + str(w) + ": σ[" + str(v) +
                               "]/σ[" + str(w) + "]·(1+δ[" + str(w) + "]) = " +
                               str(sigma[v]) + "/" + str(sigma[w]) + "·(1+" +
                               format(delta[w], ".1f") + ") = " +
                               format(contrib, ".2f") + "\n"
                               "δ[" + str(v) + "] = " + format(old, ".2f") +
                               " + " + format(contrib, ".2f") + " = " +
                               format(delta[v], ".2f"))
                        yield self._snap("accumulo", s, v, w, Q, S, d, sigma,
                                         delta, tree, msg)
                if w != s:
                    CB[w] += delta[w]
                    yield self._snap("accumulo", s, None, w, Q, S, d, sigma,
                                     delta, tree, "w=" + str(w) + " != s: CB[" +
                                     str(w) + "] += δ[" + str(w) + "] = " +
                                     format(CB[w], ".2f"))
        for i in range(n):
            CB[i] /= 2.0
        d0 = [-1] * n
        z = [0] * n
        yield self._snap("fine", None, None, None, deque(), [], d0, z,
                         {i: 0.0 for i in range(n)}, set(),
                         "Fine. CB (diviso 2) = " + ", ".join(
                             str(i) + ":" + format(CB[i], ".1f")
                             for i in range(n)))

    def _snap(self, fase, s, v, w, Q, S, d, sigma, delta, tree, msg):
        return {
            "fase": fase, "s": s, "v": v, "w": w,
            "Q": list(Q), "S": list(S),
            "d": {i: (None if d[i] == -1 else d[i]) for i in range(len(d))},
            "sigma": {i: sigma[i] for i in range(len(sigma))},
            "delta": (delta if isinstance(delta, dict)
                      else {i: delta[i] for i in range(len(delta))}),
            "tree": set(tree), "msg": msg,
        }

    # ---- navigatore dei passi -------------------------------------------------
    def _prepara_passi(self):
        if self.passi is not None:
            return len(self.passi) > 0
        if not self.nodi:
            return False
        self.passi = list(self._genera_passi())
        self.lista.delete(0, "end")
        for k, st in enumerate(self.passi):
            etich = "%3d  %s" % (k, self._titolo_passo(st))
            self.lista.insert("end", etich)
        return len(self.passi) > 0

    def _titolo_passo(self, st):
        f = st["fase"]
        if f == "fine":
            return "FINE"
        s = "s=" + str(st["s"])
        if st.get("v") is not None and st.get("w") is not None:
            return s + " " + f + " v" + str(st["v"]) + "→w" + str(st["w"])
        if st.get("w") is not None:
            return s + " " + f + " w=" + str(st["w"])
        if st.get("v") is not None:
            return s + " " + f + " v=" + str(st["v"])
        return s + " " + f

    def _mostra_passo(self, i):
        self.idx = i
        self.stato = self.passi[i]
        self.evidenzia_path = set()
        self._disegna()
        self._aggiorna_pannello()
        self.lbl_info.config(text=self.stato.get("msg", ""))
        self.lista.selection_clear(0, "end")
        self.lista.selection_set(i)
        self.lista.see(i)

    def _click_passo(self, _ev):
        sel = self.lista.curselection()
        if not sel:
            return
        i = sel[0]
        if not self._prepara_passi():
            return
        # mostra il passo selezionato senza avviare il play
        self._pausa()
        self._mostra_passo(i)

    # ---- play / pausa ---------------------------------------------------------
    def _set_controlli(self):
        # Play attivo (verde) quando fermo; Pausa attiva (ambra) quando in play.
        # Il pulsante non disponibile diventa grigio.
        if self.in_play:
            self.btn_play.config(bg="#aab7b8")    # play grigio
            self.btn_pausa.config(bg="#f39c12")   # pausa ambra
        else:
            self.btn_play.config(bg="#2ecc71")    # play verde
            self.btn_pausa.config(bg="#cccccc")   # pausa grigia

    def _play(self):
        if not self._prepara_passi():
            return
        # se siamo a fine o non iniziato, riparte dall'inizio
        start = self.idx + 1
        if start >= len(self.passi):
            start = 0
        self._play_da(start)

    def _play_da(self, start):
        if not self.passi:
            return
        if start >= len(self.passi):
            start = 0
        self.info_box = None
        self.idx = start - 1
        self.in_play = True
        self._set_controlli()
        self._tick()

    def _pausa(self):
        self.in_play = False
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self._set_controlli()

    def _tick(self):
        if not self.in_play:
            return
        nxt = self.idx + 1
        if nxt >= len(self.passi):
            self._pausa()
            return
        self._mostra_passo(nxt)
        ritardo = int(1000 / self.speed.get())
        self.after_id = self.root.after(ritardo, self._tick)

    # ---- salvataggio / esportazione ------------------------------------------
    def _testo_dot(self, con_pos=True):
        righe = ["graph G {",
                 "  node [shape=circle, style=filled, fillcolor=lightgray];"]
        h = self.canvas.winfo_height() or 560
        for i, (x, y) in enumerate(self.nodi):
            if con_pos:
                righe.append('  {0} [label="{0}", pos="{1},{2}!"];'
                             .format(i, x, h - y))
            else:
                righe.append('  {0} [label="{0}"];'.format(i))
        for v in range(len(self.nodi)):
            for w in self.adj[v]:
                if v < w:
                    righe.append("  {0} -- {1};".format(v, w))
        righe.append("}")
        return "\n".join(righe) + "\n"

    def _salva_dot(self, path=None, con_pos=True):
        try:
            with open(path or DOT_FILE, "w") as f:
                f.write(self._testo_dot(con_pos))
        except OSError as e:
            messagebox.showerror("Errore", str(e))

    def _menu_esporta(self):
        m = tk.Menu(self.root, tearoff=0)
        m.add_command(label="1) Esporta come immagine (neato)",
                      command=self._esporta_immagine)
        m.add_command(label="2) Esporta il file .dot",
                      command=self._esporta_dot)
        try:
            m.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())
        finally:
            m.grab_release()

    def _esporta_dot(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".dot",
            filetypes=[("Graphviz DOT", "*.dot"), ("Tutti", "*.*")],
            title="Salva il file .dot")
        if path:
            self._salva_dot(path)

    def _esporta_immagine(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("Immagine PNG", "*.png"), ("Tutti", "*.*")],
            title="Salva l'immagine")
        if not path:
            return
        tmp = os.path.join(os.path.dirname(path) or ".", ".__brandes_tmp.dot")
        self._salva_dot(tmp, con_pos=True)
        try:
            subprocess.run(["neato", "-n", "-Tpng", tmp, "-o", path],
                           check=True)
            messagebox.showinfo("Esportato", "Immagine salvata:\n" + path)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            messagebox.showerror("Errore neato", str(e))
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def _pulisci(self):
        self._invalida()
        self.nodi = []
        self.adj = []
        self.arco_primo = None
        self.evidenzia_path = set()
        self._salva_dot()
        self._disegna()
        self._aggiorna_pannello()
        self.lbl_info.config(text="")


def main():
    root = tk.Tk()
    root.geometry("1300x860")
    root.minsize(1040, 720)
    if root.tk.call("info", "patchlevel") < "8.6":
        messagebox.showwarning(
            "Versione di Tk obsoleta",
            "Questo Python usa Tk " + root.tk.call("info", "patchlevel") +
            ", che su macOS non gestisce bene i click.\n\n"
            "Avvia la UI con un Python con Tk >= 8.6, ad esempio:\n"
            "  ./ui.sh")
    root.lift()
    root.focus_force()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
