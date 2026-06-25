// Algoritmo "standard" O(n^3) per la betweenness centrality: calcolo esplicito
// di tutte le distanze e di tutti i conteggi di cammini minimi (all-pairs),
// seguito dalla somma esplicita delle pair-dependency. E' la soluzione che
// Brandes confronta con la propria (Figura 3 del paper). Costo: O(n^3) tempo,
// O(n^2) spazio (le matrici dist e sigma).
#include <algorithm>
#include <chrono>
#include <fstream>
#include <iostream>
#include <queue>
#include <random>
#include <set>
#include <vector>

struct Grafo {
  int n;
  int m;
  std::vector<int> U, V;             // estremi degli archi
  std::vector<std::vector<int>> adj; // liste di adiacenza
};

// Identica a quella di brandes.cpp: spanning tree casuale + archi fino a m.
Grafo genera_grafo(int n, int m, unsigned int seed) {
  Grafo g;
  g.n = n;
  g.m = m;
  g.adj.assign(n, {});

  std::mt19937 gen(seed);
  std::set<std::pair<int, int>> archi_esistenti;

  auto aggiungi = [&](int u, int v) -> bool {
    if (u == v)
      return false;
    if (v < u)
      std::swap(u, v);
    if (archi_esistenti.count({u, v}))
      return false;
    archi_esistenti.insert({u, v});
    g.U.push_back(u);
    g.V.push_back(v);
    g.adj[u].push_back(v);
    g.adj[v].push_back(u);
    return true;
  };

  for (int i = 1; i < n; i++) {
    std::uniform_int_distribution<int> prec(0, i - 1);
    aggiungi(i, prec(gen));
  }
  std::uniform_int_distribution<int> dist(0, n - 1);
  while ((int)g.U.size() < m) {
    aggiungi(dist(gen), dist(gen));
  }
  return g;
}

std::vector<double> betweenness_standard(const Grafo &g) {
  int n = g.n;

  // --- Fase 1: all-pairs shortest paths + conteggio dei cammini minimi ---
  // dist[s][t] = distanza, sigma[s][t] = numero di cammini minimi.
  // Una BFS da ogni sorgente: costo O(n * (n + m)), spazio O(n^2).
  std::vector<std::vector<int>> dist(n, std::vector<int>(n, -1));
  std::vector<std::vector<long long>> sigma(n, std::vector<long long>(n, 0));

  for (int s = 0; s < n; s++) {
    dist[s][s] = 0;
    sigma[s][s] = 1;
    std::queue<int> coda;
    coda.push(s);
    while (!coda.empty()) {
      int u = coda.front();
      coda.pop();
      for (int w : g.adj[u]) {
        if (dist[s][w] == -1) {
          dist[s][w] = dist[s][u] + 1;
          coda.push(w);
        }
        if (dist[s][w] == dist[s][u] + 1)
          sigma[s][w] += sigma[s][u];
      }
    }
  }

  // --- Fase 2: somma esplicita delle pair-dependency ---
  // Per ogni vertice intermedio v e ogni coppia (s,t): se v sta su un cammino
  // minimo s->t (criterio di Bellman), aggiunge sigma_sv * sigma_vt / sigma_st.
  // Tre cicli annidati su V: costo O(n^3).
  std::vector<double> CB(n, 0.0);
  for (int v = 0; v < n; v++) {
    for (int s = 0; s < n; s++) {
      if (s == v || dist[s][v] < 0)
        continue;
      for (int t = 0; t < n; t++) {
        if (t == v || t == s || dist[v][t] < 0 || sigma[s][t] == 0)
          continue;
        if (dist[s][t] == dist[s][v] + dist[v][t]) // v e' su un cammino minimo
          CB[v] += (double)sigma[s][v] * sigma[v][t] / sigma[s][t];
      }
    }
  }
  // grafo non orientato: ogni coppia e' contata due volte
  for (int v = 0; v < n; v++)
    CB[v] /= 2.0;
  return CB;
}

int main() {
  const int REP = 5; // misure ripetute per punto: si prende il minimo

  // Verifica rapida su un grafo piccolo (confrontabile con brandes.cpp).
  Grafo gv = genera_grafo(15, 20, 0);
  std::vector<double> CBv = betweenness_standard(gv);
  std::cout << "Verifica (n=15, m=20): CB =";
  for (double x : CBv)
    std::cout << " " << x;
  std::cout << "\n\n";

  // Warm-up per stabilizzare la frequenza della CPU.
  for (int w = 0; w < 3; w++) {
    Grafo gw = genera_grafo(300, 3000, w);
    std::vector<double> tmp = betweenness_standard(gw);
    volatile double sink = tmp.empty() ? 0.0 : tmp[0];
    (void)sink;
  }

  std::ofstream csv("risultati_standard.csv");
  csv << "n,m,densita,tempo_us\n";

  // Stesso schema di brandes.cpp ma con n piu' contenuto: l'O(n^3) rende
  // proibitivo arrivare a 2000. Sweep n = 100..1000, densita 10%..90%.
  for (int dens = 10; dens <= 90; dens += 10) {
    for (int i = 100; i <= 1000; i += 100) {
      long max_archi = (long)i * (i - 1) / 2;
      int m = (int)(dens / 100.0 * max_archi);
      if (m < i - 1)
        continue;

      Grafo g = genera_grafo(i, m, 0);
      long min_us = -1;
      for (int r = 0; r < REP; r++) {
        auto inizio = std::chrono::high_resolution_clock::now();
        std::vector<double> CB = betweenness_standard(g);
        auto fine = std::chrono::high_resolution_clock::now();
        long us =
            std::chrono::duration_cast<std::chrono::microseconds>(fine - inizio)
                .count();
        if (min_us < 0 || us < min_us)
          min_us = us; // la corsa piu' veloce: meno disturbata dal sistema
      }
      csv << i << "," << m << "," << dens << "," << min_us << "\n";
      std::cout << "dens=" << dens << "% n=" << i << " m=" << m << ": " << min_us
                << " us" << std::endl;
    }
  }
  std::cout << "scritto risultati_standard.csv" << std::endl;
}
