# Initial related-work audit

Checked 2026-09-21. This is a targeted initial search, not a systematic review or
evidence that the proposed contribution has not been published elsewhere.

| Primary source | Established contribution | Consequence for this project |
| --- | --- | --- |
| [McCrory & Thomas, 2024](https://arxiv.org/abs/2402.12008) ([full text](https://arxiv.org/html/2402.12008v1)) | Examines K-means metrics under added uniform/Gaussian irrelevant variables and scaling, using Dimsets datasets. | Closest overlap. We cannot claim that studying noise, scaling or metric sensitivity is new. Proposed extension: matched population variance, paired signal/noise streams, explicit k-selection regret and a reusable experiment package. Novelty still needs checking. |
| [Shand et al., HAWKS](https://doi.org/10.1109/TEVC.2021.3137369) ([preprint](https://arxiv.org/abs/2102.06940)) | Evolutionary generation of clustering benchmarks with controlled properties and algorithm challenges. | A more general generator already exists. Our candidate niche is a small interpretable paired design, not greater generality. No empirical HAWKS comparison has been run. |
| [scikit-learn sample generators](https://scikit-learn.org/stable/datasets/sample_generators.html) | Gaussian clusters (`make_blobs`), and redundant/irrelevant features (`make_classification`). | Our marginal Gaussian model can largely be reproduced with existing tools. Practical reproducibility and experimental controls must carry the contribution. |
| [Morris, White & Crowther, 2019](https://doi.org/10.1002/sim.8086) | ADEMP structure and guidance on simulation study planning/reporting. | Define endpoints, mechanisms, replication units and Monte Carlo uncertainty before analyzing results. |
| [Van Mechelen et al., 2023](https://doi.org/10.1002/widm.1511) | Research practices for clustering benchmarks, including evaluation and comparison design. | Distinguish oracle-k recovery from unsupervised selection, and constrain claims to the benchmark's geometry. |

Next literature tasks: verify publication versions and bibliographic metadata;
trace references/citations of the closest study; inspect other generator families
(including overlap-controlled mixtures); compare released code and experimental
controls. Do not describe this initial list as exhaustive.

## Publication positioning

Working direction: research software with a paired, transparent benchmark case
study. [SoftwareX / Software Impacts](https://www-prod.elsevier.com/researcher/author/tools-and-resources/research-elements-journals)
are thematic candidates, not an acceptance prediction. A software description
must establish usefulness beyond assembly of standard generators. JOSS has
[explicit scope, research impact and development-history requirements](https://joss.readthedocs.io/en/latest/submitting.html).
No quartile, cost, or acceptance claim is made here.

