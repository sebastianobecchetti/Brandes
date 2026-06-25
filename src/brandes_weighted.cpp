#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <queue>
#include <random>
#include <set>
#include <stack>
#include <utility>
#include <vector>

struct Grafo {
  int n; // numero vertici
  int m;
  std::vector<int> U, V, W;                          // estremi degli archi
  std::vector<std::vector<std::pair<int, int>>> adj; // liste di adiacenza
                                                     //
};

Grafo genera_grafo(int n, int m, unsigned int seed) {

  Grafo g;
  g.n = n;
  g.m = m;
  g.adj.assign(n, {});

  std::mt19937 gen(seed);
  std::set<std::pair<int, int>> archi_esistenti;
  std::uniform_int_distribution<int> peso(1, 10);

  // aggiunge l'arco {u,v} con peso casuale: scarta cappi e duplicati
  auto aggiungi = [&](int u, int v) -> bool {
    if (u == v)
      return false;
    if (v < u)
      std::swap(u, v);
    if (archi_esistenti.count({u, v}))
      return false;
    int w = peso(gen);
    archi_esistenti.insert({u, v});
    g.U.push_back(u);
    g.V.push_back(v);
    g.W.push_back(w);
    g.adj[u].push_back({v, w});
    g.adj[v].push_back({u, w});
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

// Scrive il .dot: i nodi nell'insieme 'ponte' sono colorati di rosso,
// gli altri grigi. Etichetta di ogni nodo = "id\nCB=valore".
void scrivi_dot(const Grafo &g, const std::vector<double> &CB,
                const std::set<int> &ponte) {
  std::ofstream f("grafo_w.dot");

  f << "graph G {\n";
  f << "  graph [overlap=false];\n";
  f << "  node [shape=circle, style=filled, fillcolor=lightgray];\n";
  // nodi: rossi se ponte, con la betweenness in etichetta
  for (int i = 0; i < g.n; i++) {
    f << "  " << i << " [label=\"" << i << "\\nCB=" << (int)(CB[i] + 0.5)
      << "\"";
    if (ponte.count(i))
      f << ", fillcolor=red, fontcolor=white";
    f << "];\n";
  }
  // archi: etichetta = peso dell'arco
  for (size_t i = 0; i < g.U.size(); i++) {
    f << "  " << g.U[i] << " -- " << g.V[i] << " [label=\"" << g.W[i]
      << "\"];\n";
  }
  f << "}\n";
}

// Stampa di debug: distanza, sigma e predecessori di ogni nodo.
// I predecessori sono ricalcolati da dist (vicini un livello piu' vicini).
// void stampa_bfs(const Grafo &g, const std::vector<int> &dist,
//                 const std::vector<long long> &sigma) {
//   std::cout << std::setw(6) << "nodo" << std::setw(6) << "dist" <<
//   std::setw(7)
//             << "sigma" << "   pred" << std::endl;
//   for (int i = 0; i < g.n; i++) {
//     std::cout << std::setw(6) << i << std::setw(6) << dist[i] << std::setw(7)
//               << sigma[i] << "   ";
//     for (int v : g.adj[i])
//       if (dist[v] == dist[i] - 1)
//         std::cout << v << " ";
//     std::cout << std::endl;
//   }
// }

std::vector<double> brandes(const Grafo &g) {
  int n = g.n;
  const long long INF = std::numeric_limits<long long>::max();
  std::vector<double> CB(g.n, 0.0);

  std::vector<long long> dist(n);
  std::vector<long long> sigma(n);
  std::vector<double> delta(n);
  std::vector<char> nodi_completati(n);
  // stack: pila dei vertici nell'ordine di finalizzazione (distanza non
  // decrescente), estratti all'indietro per l'accumulo delle dipendenze. NON e'
  // la lista delle sorgenti: si riferisce a una singola sorgente s alla volta.
  std::stack<int> stack;

  using v_alias = std::pair<long long, int>;
  std::priority_queue<v_alias, std::vector<v_alias>, std::greater<v_alias>>
      queue; // costo basso -> in cima alla coda a priorita'
  for (int s = 0; s < n; s++) {
    std::fill(dist.begin(), dist.end(), INF);
    std::fill(sigma.begin(), sigma.end(), 0);
    std::fill(delta.begin(), delta.end(), 0.0);
    std::fill(nodi_completati.begin(), nodi_completati.end(), 0);
    // stack e' gia' vuoto: l'accumulo della sorgente precedente lo svuota del tutto
    dist[s] = 0;
    sigma[s] = 1;
    queue.push({0, s});

    while (!queue.empty()) {
      auto [d, nodo] = queue.top();
      queue.pop();
      if (nodi_completati[nodo])
        continue;
      nodi_completati[nodo] = 1;
      stack.push(nodo);

      for (auto [vicino, w] : g.adj[nodo]) {
        long long nd = dist[nodo] + w;
        if (nd < dist[vicino]) {
          dist[vicino] = nd;
          sigma[vicino] = 0;
          queue.push({nd, vicino});
        }
        if (nd == dist[vicino])
          sigma[vicino] += sigma[nodo];
      }
    }
    while (!stack.empty()) {
      int w = stack.top();
      stack.pop();
      for (auto [v, peso] : g.adj[w]) {
        if (dist[v] + peso == dist[w])
          delta[v] += (double)sigma[v] / sigma[w] * (1 + delta[w]);
      }
      if (w != s) {
        CB[w] += delta[w];
      }
    }
  }
  for (int i = 0; i < n; i++)
    CB[i] /= 2.0;
  return CB;
}

int main() {
  const int REP = 5; // misure ripetute per punto: si prende il minimo

  // Warm-up: gira brandes a vuoto su un grafo medio per far salire la
  // frequenza CPU (turbo) e scaldare le cache prima di cronometrare.
  // I risultati sono scartati apposta (volatile evita che il
  // compilatore ottimizzi via la chiamata).
  for (int w = 0; w < 3; w++) {
    Grafo gw = genera_grafo(500, 5000, w);
    std::vector<double> CBw = brandes(gw);
    volatile double sink = CBw.empty() ? 0.0 : CBw[0];
    (void)sink;
  }

  std::ofstream csv("risultati_w.csv");
  csv << "n,m,densita,tempo_us\n"; // intestazione

  // Riproduce la Figura 3 di Brandes: una curva per densita (10%..90%),
  // sweep su n. Per ogni densita, m = densita * archi_massimi(n).
  for (int dens = 10; dens <= 90; dens += 10) {
    for (int i = 100; i <= 2000; i += 100) {
      long max_archi = (long)i * (i - 1) / 2;
      int m = (int)(dens / 100.0 * max_archi); // archi a quella densita
      if (m < i - 1)
        continue; // troppo pochi per essere connesso

      Grafo g = genera_grafo(i, m, 0);
      long min_us = -1;
      for (int r = 0; r < REP; r++) {
        auto inizio = std::chrono::high_resolution_clock::now();
        std::vector<double> CB = brandes(g);
        auto fine = std::chrono::high_resolution_clock::now();

        long us =
            std::chrono::duration_cast<std::chrono::microseconds>(fine - inizio)
                .count();
        if (min_us < 0 || us < min_us)
          min_us = us; // la corsa piu' veloce: meno disturbata dal sistema
      }
      csv << i << "," << m << "," << dens << "," << min_us << "\n";
      std::cout << "dens=" << dens << "% n=" << i << " m=" << m << ": "
                << min_us << " us" << std::endl;
    }
  }
  std::cout << "scritto risultati_w.csv" << std::endl;

  int nv = 20, mv = 20; // coppia da visualizzare
  Grafo gv = genera_grafo(nv, mv, 0);
  std::vector<double> CB = brandes(gv);

  // top 20% dei nodi per betweenness = nodi "ponte"
  int k = std::max(1, (int)(0.20 * nv + 0.5)); // 20% di 15 -> 3
  std::vector<int> idx(nv);
  std::iota(idx.begin(), idx.end(), 0); // idx = {0,1,...,nv-1}
  std::sort(idx.begin(), idx.end(),
            [&](int a, int b) { return CB[a] > CB[b]; }); // ordina per CB desc
  std::set<int> ponte(idx.begin(), idx.begin() + k);      // primi k nodi

  std::cout << "\nNodi ponte (top " << k << " per betweenness):" << std::endl;
  for (int v : idx) {
    std::cout << "  nodo " << v << "  CB=" << CB[v]
              << (ponte.count(v) ? "   <-- PONTE" : "") << std::endl;
  }
  scrivi_dot(gv, CB, ponte);
  std::cout << "scritto grafo_w.dot" << std::endl;
  std::system("neato -Tpng grafo_w.dot -o grafo_w.png");
}
