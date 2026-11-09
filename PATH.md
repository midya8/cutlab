# CutLab: the whole affine unary response

[Live response inspector](https://midya8.github.io/cutlab/path.html) · [Original flow/cut method](METHOD.md)

## Exact question and scope

Keep a supplied submodular binary pair energy fixed. Replace every unary entry by `base[i][label] + lambda * slopes[i][label]`. For every real lambda in a supplied closed rational interval, find every optimum assignment. At most six variables; all coefficients/domain endpoints follow the existing bounded rational-string syntax. Domain lower < upper. Negative unary slopes and negative domains are allowed. A fixed pair with negative submodularity slack is rejected, not clipped, transformed or relaxed.

This is exhaustive finite sensitivity analysis, not a new inference algorithm, scalable parametric maxflow, probabilistic calibration or learned response. There are 2^n assignment lines and (2^n)^2 pairwise inequalities. Bit growth is not benchmarked. All inputs are original synthetic costs.

## Every line's complete optimal region

For assignment m, sum original base costs into intercept b_m and original selected unary slopes into a_m. Its exact energy is `b_m + lambda*a_m`. For each competitor k, optimality requires:

```
(a_m - a_k) * lambda <= b_k - b_m.
```

Positive left coefficient gives an upper bound; negative gives a lower bound, with inequality direction reversed. Zero coefficient is always satisfied when the right side is nonnegative and impossible otherwise. Intersect every bound with the supplied domain. Empty means never optimal, a singleton means optimal only at that exact point, and a nonempty interval includes both boundaries. Every inequality, ratio and region is retained for every line. Parallel and identical lines are not silently collapsed.

Take all nonempty region endpoints plus the domain endpoints. These sorted exact knots partition the domain into points and open cells. Every line has constant optimal/nonoptimal status within an open cell because all its region endpoints are knots. Midpoint evaluation lists every optimum in that cell; point evaluation separately retains every boundary-only tie. A midpoint solve alone does not certify the whole interval: the complete inequality intersection does.

For each of the 55 retained boundary points and 37 open-cell midpoints across 18 controls, independently rebuild the exact original energy at that lambda and solve it through the base flow/cut engine. Keep the complete pair/terminal reduction, augmentation, cut/residual, original-energy reference and whole tied-family report. Check its minimum and full mask family against the affine-line result. Derived rational values can exceed the input coefficient limit, so only this validated affine transformation uses an internal exact-cost adapter. The original public parser and `audit` still enforce the original limits; unchanged original 24 reports remain exact.

The optimum value, a minimum of affine lines, is concave and piecewise affine; active slopes cannot increase left to right. This does not imply that each binary label moves in only one direction under arbitrary signed slopes.

## Retained failures and ties

Default three-variable control has unique open-cell masks 7, 0, 1, with exact interior breakpoints 1/4 and 2. Variable x0 is 1, 0, 1: it leaves and returns. It was generated with fixed seed 9281 (first trial), not selected from real data. The two-variable opposite-slope control has four ties at lambda=0; masks 0 and 3 are optimal only at that single point and would be lost by listing only cell winners. Other controls keep persistent free labels, all 64 assignments tied over a whole interval, a rational 2/3 breakpoint, an intersection outside the domain, a right-endpoint-only tie, common unary slopes that shift values without changing decisions, parallel lines, asymmetric rational coupling, disconnected agreement pairs, fixed negative offsets and six seeded signed graphs.

Source-sink-monotone algorithms assume source capacities nondecreasing, sink capacities nonincreasing and other capacities fixed, under a specified orientation. We allow arbitrary signed unary slopes and do not claim those nested-cut/linear-breakpoint guarantees. We do not implement HPF, PBFS, discrete Newton, Eisner-Severance, a hull algorithm or any cited code. All-line halfspace intersection is intentionally direct and tiny.

## Reproduction and checks

```sh
python -m pip install .
cutlab examples/path.json --path --output /tmp/path.json
python -m cutlab examples/path.json --path
python -m unittest discover -s tests -v
PYTHONPATH=. python tools/build_audits.py
PYTHONPATH=. python tools/build_paths.py
npm test
sh tools/wheel_smoke.sh
```

30 Python tests run on 3.10-3.13, retaining all original 21 tests. New controls include 120 independent all-pair-intersection/dense-energy path oracles; 50 full endpoint-inequality audits; 40 positive-objective transformations; 40 lambda reversals; 60 concave active-slope checks; exact point-only/persistent ties; nonmonotone, endpoint and validation controls; no input mutation; and CLI invalid-output preservation. Counts inside tests are controls, not test-function totals.

18 complete native and independent BigInt path reports match 90,732 exact scalar leaves, in addition to all original 24 reports / 24,624 leaves. Six Node/Chrome tests retain the original inspector checks and add actual rendered checks for every one of 214 line records, 6,084 inequality rows, 92 complete point/cell summaries and full flow reports, all region/line tables, every selected-line/envelope/knot geometry, invalid/stale clearing, JSON export and 320/390/1280 containment. Plot coordinates alone are approximate; no floating geometry is used to choose a region or optimum.

Installed wheel checks all 24 base reports and 18 path reports, console/module CLI equivalence for both workflows and five module origins outside the checkout. Native JSON bounds 32KiB UTF-8 and rejects duplicate keys; browser JSON.parse bounds 32,768 characters and keeps the last duplicate. Index-number parser differences remain as in METHOD.md.

## Sources, including assumptions we do not import

- Gallo, Grigoriadis and Tarjan, *A Fast Parametric Maximum Flow Algorithm and Applications*, SIAM J. Computing 18(1), 1989. Publisher abstract describes a special parametric class; the site lists online publication in 2006, not the original volume year: https://epubs.siam.org/doi/10.1137/0218003 . Abstract inspected, not a claim to have reproduced its algorithm or read paywalled full text.
- UC Berkeley, *HPF Simple Parametric Maximum Flow / Minimum Cut Solver*, versions 1/2. Explicit source/sink monotonicity and bounded-precision scaling caveats: https://riot.ieor.berkeley.edu/Applications/Pseudoflow/parametric.html . This documentation has an academic, not open-source, software license; no code was downloaded or copied.
- UC Berkeley, *Fully Parametric Cut HPF*, version 2 May 2025. Nested-cut assumptions, distinction between implementation and theoretical complexity, and warnings about rounding negative capacities: https://riot.ieor.berkeley.edu/Applications/full-para-HPF/pseudoflow-parametric-cut.html . We use no code and perform no capacity clipping.
- Goemans, Gupta and Jaillet, *Discrete Newton's Algorithm for Parametric Submodular Function Minimization*, IPCO 2017 manuscript. Introduction and conclusion distinguish nonnegative directions from arbitrary directions; bounds on Newton iterations are not automatically bounds on envelope breakpoints: https://www.mit.edu/~jaillet/general/ggj-ipco-17.pdf . We do not implement their line-search algorithm or import historical open-question wording as a current unresolved claim.
- Nemesch, Ruzika, Thielen and Wittmann, *A survey of exact and approximation algorithms for linear-parametric optimization problems*, June 28, 2025. Definitions of lower envelopes, critical regions and single-parameter breakpoints: https://link.springer.com/article/10.1007/s10898-025-01512-6 . Our output retains every tied solution, not only a minimum-cardinality representative solution set.
- David Eppstein, *The Parametric Closure Problem*, ACM TALG 14(1), December 2017, introduction and section 1.3. Affine solution values and envelope/convex-hull interpretation: https://dl.acm.org/doi/pdf/10.1145/3147212?download= . We implement neither its special-family algorithms nor closure constraints from that paper.
- Bonn Computational Analytics, *MonotoneParametricMinCut* project documentation, ALENEX 2025 context. Source-sink-monotone framework and breakpoint representation: https://github.com/jonas-sauer/MonotoneParametricMinCut . Documentation inspected, no implementation copied or benchmark comparison made.

Original implementation, independent checks and synthetic controls: Midya Rahmani.
