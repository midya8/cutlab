# CutLab: exact binary energy, flow and cut witnesses

## Scope and conventions

CutLab minimizes a supplied sum of unary and pairwise costs over at most six binary variables. It implements established binary submodular graph reduction and shortest augmenting paths with exact rational arithmetic. It does not learn a model, introduce an inference algorithm, segment a real image, or claim performance/clinical/predictive validation. Mathematical certificates here are inspectable witnesses, not machine-checked formal verification.

The exact input keys are `unary` and `pairs`. There are 1-6 unary rows `[cost0,cost1]`. Each pair has exactly `i,j,values`, requires integer `0 <= i < j < n`, and uses `[A,B,C,D]=[E(0,0),E(0,1),E(1,0),E(1,1)]`. This is row-major table order, not little-endian mask order. Duplicate pair scopes are rejected, not silently accumulated. There are at most 15 pairs. Costs must be signed integer or fraction strings, length at most 12 characters, with reduced numerator magnitude and denominator at most 10,000. Finite costs only; there are no infinity-valued hard constraints.

Assignments use little-endian masks: bit i is x_i. Graph nodes 0..n-1 are variables, node n is s, and node n+1 is t. A variable on the source side has label 0; sink side has label 1. A directed edge charges its capacity only when its tail is source-side and its head is sink-side. Edges of capacity zero are retained in the capacity matrix but omitted from the positive-edge table and SVG.

## Reduction, including negative costs

For each pair, compute `w=B+C-A-D`. If w is negative, the graph solve is refused, without clipping or replacing the term. The exact original-energy enumeration and local-search control remain available, but no graph-cut certificate is returned. Refusal is under the supplied coding. We do not search variable label flips, use roof duality, or claim that every refused input is unrepresentable after transformations.

For a nonnegative slack, the four exact identities are:

```
E_ij(x_i,x_j) = A + (C-A)x_i + (D-C)x_j + w(1-x_i)x_j
```

The constant A is retained, the two linear coefficients are added to their variables, and a directed i->j edge has capacity w. Every original and reconstructed table entry is included. Original unary `[d0,d1]` contributes constant d0 and linear d1-d0.

After all terms have been summed, each linear coefficient l is represented by:

- l>=0: s->i with capacity l, no extra constant;
- l<0: i->t with capacity -l, and constant shift l.

Thus `original_energy(x) = offset + cut_capacity(x)` for every assignment. The offset can be negative. Maximum flow alone is not the minimum energy. The terminal table exposes each linear coefficient, edge and constant shift.

## Exact flow and lower/upper bound

We store a skew-symmetric net flow F. In this construction each original variable edge goes from smaller to larger index, and there are no opposite original arcs. Thus original positive-edge flow is nonnegative and at most capacity. Residual capacity is `R(u,v)=C(u,v)-F(u,v)`, including backward arcs that cancel previously routed flow.

A breadth-first search selects a shortest residual s->t path. Vertex indices are scanned in ascending order to make path ties deterministic. The bottleneck is the smallest exact residual along the path. Each augmentation records the path, every before-residual, which arcs reverse original flow, the exact delta, new value and complete positive-edge flows. It is not sufficient to show only forward residual edges. The retained reverse-routing control needs a backward variable arc in its sixth augmentation.

Every intermediate flow satisfies capacity bounds and zero net flow at variable nodes. The final source outflow equals sink inflow and has no positive residual s->t path. The reachable source set supplies a cut with equal capacity. For any source set S containing s and excluding t:

```
cut_capacity(S) - flow_value = sum_{u in S, v outside S} R(u,v) >= 0.
```

Every assignment row exposes original energy, source set, each crossing positive-capacity edge, cut capacity, offset-plus-cut, cut-minus-flow, outgoing residual sum and closure. Matching feasible flow and cut establish exact optimality. Exhaustive original-energy enumeration is an independent small reference; the flow is not chosen from those optimum energies.

## Every optimum and forced labels

At a maximum flow, S is a minimum source set exactly when no positive residual edge leaves it. Positive-residual strongly connected components must remain together. The condensation graph's directed edges impose **forward closure**: including a component includes all residual successors. Other sources may orient their partial order in reverse and call this downward closure; our direction is explicit.

The smallest source set is the set reachable from s. The largest source set is all nodes that cannot reach t. A variable is forced 0 if reachable from s, forced 1 if it can reach t, otherwise it takes both labels across optimal cuts. Free variables are not necessarily independently selectable. The tied-agreement control has two free variables but only masks 0 and 3, not all four masks. The asymmetric directed implication has three minimum assignments. The zero graph has all 64 assignments optimal. We enumerate all tiny source sets satisfying residual closure and compare that family against independent original-energy minima. Minima are closed under mask intersection and union.

## Failure controls

1. Unary-only selects the cheapest original unary independently, ties to zero, ignoring all pairs. In control 0 it has energy 5, while masks 0 and 3 have energy 3. Its gap is 2. This deliberately incomplete control is labeled as such, not presented as a strong solver benchmark.
2. Strict best single-flip search starts at mask 0. At each step all n one-flip neighbors are evaluated from the original energy; the lowest strictly improving one is taken, ties by variable index. It stops without equal-cost moves. In control 23, mask 0 has energy 2 and both one-flip neighbors energy 3, so it stops. The joint optimum is mask 3 with energy 0. This is a local-versus-global logical counterexample, not a runtime comparison.
3. Negative costs require offsets; dropping them changes every reported objective. Asymmetric and zero-slack tables keep the full reconstruction visible.
4. Non-submodular `[2,0,0,2]` has slack -4. Exact reference minima are masks 1 and 2. No network solve is asserted.
5. Reverse residual routing, disconnected tied components, forced/free mixtures, rational costs and ten seeded signed graphs remain inspectable.

## Verification and reproduction

The original fixed-cost workflow has 21 Python tests, retained in the current suite of 30. The CI matrix covers Python 3.10, 3.11, 3.12 and 3.13. The fixed-cost tests include 250 independently enumerated original-energy cases, 160 every-cut dual-slack checks, all augmentation paths/bottlenecks/conservation/capacity witnesses, separate graph-search reachability and SCC comparisons, full-family/forced-label/lattice checks, 100 offset/positive-scaling controls, 80 variable relabelings, every four-entry reconstruction, the reverse-arc control, local-search trajectories, malformed inputs, no mutation and CLI output preservation on invalid input. Counts inside tests are controls, not separate test functions.

Twenty-four native/independent BigInt reports match 24,624 exact scalar leaves. Three original Node/Chrome tests, retained in the current suite of six, check all fixed-cost reports and actual rendered content, including 570 full cut records, 56 flow-state records, 73 pair records, 180 positive residual records, 50 local-state records, 87 terminal rows, 449 SVG edge labels/coordinates/colors and 4,166 node-color checks. Tables, metrics, full-family fields, invalid/stale clearing, JSON export and 320/390/1280 containment are also checked. Graph and tables scroll horizontally on small screens to preserve legible labels. Actual SVG text bounds are checked against other labels, nodes and graph boundaries for every retained flow state. Moved labels have dotted leaders. Derived fractions longer than 24 characters use compact decorative edge IDs with exact values retained in tooltips and the full edge table; a valid input with long derived fractions checks this route.

The installed-wheel script checks all 24 fixed-cost reports and 18 response-path reports, console and module CLI equivalence for both workflows, and five imported module origins outside the checkout. The original fixed-cost check used four modules; the response-path check adds the fifth. The report builder is deterministic and uses original synthetic examples, including a fixed reverse-routing fixture found by seeded generation. No external dataset, model API, figure or source code is copied.

```sh
python -m unittest discover -s tests -v
PYTHONPATH=. python tools/build_audits.py
npm test
sh tools/wheel_smoke.sh
python -m cutlab examples/demo.json --output /tmp/witness.json
```

## Boundaries

All energy and flow arithmetic is rational and exact. SVG positions are floating geometry, not optimization arithmetic. Exhaustive verification/family output are exponential and bounded to 64 assignments. Augmentation counts do not establish wall-clock speed or process-memory savings, and rational bit growth is not benchmarked. No multilabel construction, higher-order term, non-submodular relaxation, stochastic sampler, learned probability, causal claim or uncertainty calibration is provided.

Native JSON rejects duplicate keys and bounds 32KiB UTF-8. Its index tokens must be actual integers, not booleans or floats. Browser JSON.parse keeps the last duplicate key, bounds 32,768 characters and accepts integer-valued index tokens such as 1.0. Both validate all other shapes and perform exact rational cost arithmetic. Export is enabled only for a current successfully computed witness, including an explicitly refused graph solve with a valid tiny reference.

## Established sources

- Vladimir Kolmogorov and Ramin Zabih, *What Energy Functions Can Be Minimized via Graph Cuts?*, IEEE TPAMI 2004. Binary graph representability, pairwise regularity and graph constructions: https://www.cs.cornell.edu/~rdz/Papers/KZ-PAMI04.pdf
- Oxford notes, *Submodularity in Energy Minimisation using Graph Cuts*, April 19, 2016. Binary-label/set-function correspondence: https://www.robots.ox.ac.uk/~pankaj/notes/submodularity_energy_min.pdf . The extracted equation 7 repeats the same diagonal term; CutLab uses the four-entry condition verified against Kolmogorov-Zabih and explicit algebra, not that typographic line.
- Michel X. Goemans, MIT 18.453, *Lecture notes on flows and cuts*, April 6, 2017. Feasible flow, conservation, residual augmentations and shortest augmenting paths: https://math.mit.edu/~goemans/18453S17/flowscuts.pdf
- Tim Roughgarden, CS261, *Lecture #2: Augmenting Path Algorithms for Maximum Flow*, 2016 course path. Residual-path correctness and Edmonds-Karp: https://timroughgarden.org/w16/l/l2.pdf
- CMU 15-451/651, *Lecture #10: Network Flows I*, February 18, 2020. Directed cuts, skew-symmetric flow, residual capacity and matching flow/cut optimality witnesses: https://www.cs.cmu.edu/~15451-s20/lectures/lec10-flow1.pdf
- Seth Pettie and Longhui Yin, *The Structure of Minimum Vertex Cuts*, arXiv:2102.06805v1, February 12, 2021. Its introduction specifically reviews the Picard-Queyranne minimum s-t cut partial-order representation, distinct from the paper's vertex-cut results: https://arxiv.org/pdf/2102.06805 . CutLab uses only that established s-t cut-family background, not the new vertex-cut algorithm.
- Jean-Claude Picard and Maurice Queyranne, *On the structure of all minimum cuts in a network and applications*, technical report EP-R-79-15, March 1979, Polytechnique Montreal archive: https://publications.polymtl.ca/5993/1/EP-R-79-15_Picard.pdf . Archive title/date/authors are verified; the historical scan's extracted body is corrupt, so substantive closure grounding above uses the readable sources and direct residual-slack identity. The Springer 1982 page https://link.springer.com/article/10.1007/BF01581031 is an erratum, not treated as the original theorem paper.

Implementation, independent checks and original synthetic controls: Midya Rahmani.
