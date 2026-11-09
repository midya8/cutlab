# CutLab

**A cut, with the whole proof.** Exact finite binary submodular energy minimization, every graph-reduction entry and flow/cut certificate, plus the full family of tied optima.

[Live inspector](https://midya8.github.io/cutlab/) · [Method and sources](METHOD.md) · [Example input](examples/demo.json)

CutLab implements established graph cuts with dependency-free Python rational arithmetic and independent browser BigInt arithmetic. It is not a learned model, a new algorithm or a vision benchmark.

## What is inspectable

- Every signed pair-table decomposition, nonnegative edge capacity and retained constant offset.
- Every shortest augmenting path, bottleneck, reverse cancellation and complete after-flow.
- Every tiny assignment, crossing edge, original energy, cut capacity and dual slack.
- All residual SCCs, closure constraints, optimum ties and genuinely forced labels.
- Complete strict single-flip trajectories and a labeled unary-only contrast.
- Editable browser input, exact rational inference, current JSON export and explicit refusals.

## Two choices can beat every single flip

For two variables with unary `[1,0]` each and agreement pair `[0,2,2,0]`, mask 0 has energy 2. Both single flips cost 3, so strict best single-flip search stops. Mask 3 has energy 0. The graph certificate gives flow 1 plus offset -1 = minimum 0. Neither a local stop nor flow without its offset is the energy optimum.

Another control has unary `[0,3]`, `[3,0]` and agreement cost 5. Unary-only picks energy 5; the exact two tied minima have energy 3. The asymmetric implication has three ties; the zero six-variable graph has all 64 labelings tied. A six-variable control requires a backward residual arc to undo earlier routing. A non-submodular table is refused, not clipped.

## Run offline

```sh
python -m pip install .
cutlab examples/demo.json --output /tmp/cutlab.json
python -m cutlab examples/demo.json
python -m unittest discover -s tests -v
npm test
sh tools/wheel_smoke.sh
python -m http.server 8000 --directory docs
```

Python 3.10+. No runtime dependencies. Node 22+ and Chrome are needed only for browser verification. Rebuild checked-in witnesses with `PYTHONPATH=. python tools/build_audits.py`.

```python
from cutlab import audit
r = audit({"unary": [["1", "0"], ["1", "0"]],
           "pairs": [{"i": 0, "j": 1, "values": ["0", "2", "2", "0"]}]})
assert r["minimum"] == "0"
assert r["optimal_masks"] == [3]
assert r["reference"]["single_flip"]["gap"] == "2"
```

## Checks

21 Python tests on 3.10-3.13: 250 independent dense energy oracles, 160 all-cut slack audits, every augmentation/conservation/capacity witness, independent reachability/SCC checks, complete optimum-family checks, 100 scaling/offset controls and 80 relabelings. Original controls remain visible, including local search failure and explicit refusal.

24 Python/independent BigInt reports match **24,624 exact leaves**. Actual Chrome checks **570 cut records, 56 flow states, 73 pair records, 180 residual records and 50 local states**, 87 terminal rows, 449 edge geometry/color/label records and 4,166 node colors. Three Node/Chrome tests also cover summaries/tables, JSON export, invalid/stale state and 320/390/1280 containment. Installed-wheel reproduction verifies all reports, both CLI routes and four module origins outside checkout. See [METHOD.md](METHOD.md) for exact scope and distinctions.

## Limits

Six binary variables, distinct pair scopes, signed rational costs. Pair values are `[00,01,10,11]`; assignment masks instead use bit i for variable i. Source side means label 0. Every pair must have nonnegative submodularity slack under the supplied coding. No search over label flips, roof duality, multilabel or higher-order construction. Reference/family enumeration is exponential; operation counts are not runtime or memory benchmarks. Supplied costs are not learned probabilities, calibrated uncertainty or causal effects. Certificates are mathematical witnesses, not machine-checked formal proofs. Native/browser JSON parser differences are documented.

Established theory is credited to Kolmogorov-Zabih, standard maxflow/mincut and shortest-augmentation references, and Picard-Queyranne residual cut-family structure. No external source code, figures or datasets copied. Implementation and original synthetic controls by Midya Rahmani. MIT license.
