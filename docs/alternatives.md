# Positioning and alternatives

This is a scoped comparison of documented roles, not an exhaustive list of
features. It does not claim other tools cannot implement paired experiments.

| Tool | Documented role | Relationship to this package |
|---|---|---|
| [NumPy](https://numpy.org/doc/stable/reference/random/index.html) | General random sampling and numerical arrays | Sufficient to implement the same task. An independent reference implementation is included |
| [scikit-learn make_blobs](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.make_blobs.html) | Spherical Gaussian clusters with centers, sizes, spread and random state | A simple spherical dataset does not require this package |
| [MixSim](https://www.jstatsoft.org/article/view/v051i12) | Mixture simulation with overlap controls, noise and outliers | Prefer when overlap-targeted simulation is the requirement |
| HAWKS (Shand et al., DOI 10.1109/TEVC.2021.3137369) | Evolution of clustering datasets with prescribed properties | Different objective from archiving controlled paired perturbations |
| [deric/clustering-benchmark](https://github.com/deric/clustering-benchmark) | Collection of labelled artificial and real problems | Related work, not bundled code, a dependency or an imported dataset |
| [Clustering Benchmarks](https://clustering-benchmarks.gagolewski.com/) | Heterogeneous benchmark collections and reference partitions | Broader evaluation of algorithm behavior remains necessary |

The public paired API integrates specified invariants, separate feature/label
objects, provenance and candidate-level auditing. No universal algorithm
ranking, uniquely available statistical model, independent adoption or measured
researcher time saving is claimed.
