# SoftwareX submission preparation

Requirements checked on **29 September 2026** against the current official
[Guide for Authors](https://www.sciencedirect.com/journal/softwarex/publish/guide-for-authors)
and [Original Software Publication LaTeX template](https://legacyfileshare.elsevier.com/promis_misc/softwarex-osp-template.tex).
This is a software/release checklist, not a manuscript. All manuscript prose,
supplementary prose, highlights and editorial checkpoints remain in Overleaf.

## Article and file requirements

| Requirement | Preparation / final check |
| --- | --- |
| Article type | Original Software Publication; there is no previous SoftwareX article to update |
| Mandatory template | `elsarticle`, `preprint,12pt,a4paper`; retain document typography and margins |
| Length | Maximum **4,000 words**, excluding title, authors, affiliations, references and metadata tables; include abstract, running text, captions and footnotes |
| Pages | Official template specifies **six pages of main text**, excluding metadata, tables, figures and references, with priority given to the word limit; do not infer submission length from typeset journal PDFs |
| Structure | Motivation and significance; Software description; Illustrative examples; Impact; Conclusions |
| Metadata | Preserve C1–C8 descriptions and complete the right column, including a version-specific GitHub link and support email |
| Abstract / keywords | Guide: abstract at most 250 words; template suggests approximately 100. One to seven English keywords |
| Figures | At most six; two vector figures prepared with source, data fingerprints and PDF/PNG outputs in `paper/softwarex/` |
| References | Numbered square brackets, first-citation order; abbreviated journal names; first six authors then et al. where necessary; DOI when available |
| Highlights | Encouraged; separate editable file, three to five bullets, at most 85 characters each including spaces |
| Graphical abstract | Encouraged, not mandatory; a main-text architecture figure does not itself count as a submitted graphical abstract |
| Main files | Manuscript PDF plus editable LaTeX source ZIP with bibliography and figure files |
| Supplement | Separate, cited supplementary PDF containing full experimental methods/results; supplied material is normally published as received |
| Review model | Single anonymized; keep authors and affiliations on the title page |

The general guide recommends simple tables without vertical rules; the mandatory
software metadata template itself uses a grid. Preserve the required metadata
fields, with table columns fitted to the existing text width. Do not compress
the document font or change margins to meet limits.

## Software and evidence

| Requirement | Repository artifact |
| --- | --- |
| Public GitHub repository | **Release gate:** repository was private at the requirements audit; visibility must be explicitly authorized and changed before submission |
| README.md | Installation, parameters, actual inputs/outputs, Python API, replay and limitations in English; Spanish guide also available |
| LICENSE.txt | Exact copy of the existing MIT license; both license files ship in the package |
| Source under src/ | `src/random_clusters/` |
| Identifiable version | Package 1.0.0; create and verify immutable `v1.0.0` tag after merging the submission-preparation changes |
| Software citation | `CITATION.cff`; cite software separately from any future article |
| Research data | Configurations, manifests, raw fit/selection records, representative datasets and partition archives in `research/results/`; cite/link the versioned evidence collection |
| Reproduction | `REPRODUCIBILITY.md` distinguishes archive checking, dataset regeneration and model refitting |
| Frozen provenance | Preserve the historical experimental commits and original output bytes; no refitting was needed for journal adaptation |
| Automated validation | Existing test suite, style/format checks, package build and all three evidence verifiers; require passing pull-request CI |

GitHub URLs are permissible when a persistent identifier is unavailable. An
archival data/software DOI can strengthen preservation but must not be invented
or described as minted before it exists. SoftwareX may archive accepted code in
its own GitHub organization; that is not already completed at preparation time.

## Author-controlled submission gates

- Author order, affiliation, correspondence address and absence of competing
  interests were supplied by the corresponding author. CRediT roles must reflect
  the confirmed contributions, not assumed seniority.
- Funding: the corresponding author will supply funders, grants and funder roles.
  Keep a visible placeholder until this is completed; do not replace it with a
  claim that no funding was received.
- All authors must review and approve the manuscript, AI-assisted material,
  originality/exclusive-submission statements and final submission declarations.
- Use the [Elsevier declarations tool](https://declarations.elsevier.com) and
  upload its generated Word declaration file. A manuscript conflict statement
  does not replace that separate submission item.
- Research data deposit/citation/linking and an availability statement are
  required. Verify that anonymous readers can open the software and evidence links.
- Confirm any University of Seville publishing agreement/APC coverage in the
  submission workflow. Institutional reading access does not establish APC
  coverage. Do not purchase open access or submit the article as part of this
  preparation task.

## Recent publication models inspected

These are examples of published presentation, not permission to exceed the
current submission limits. All were listed among the latest publications at
the journal home page; the December 2026 issue date differs from online dates.

| Article | Online date | Presentation relevant to this project |
| --- | --- | --- |
| [xslope](https://doi.org/10.1016/j.softx.2026.103018) | 11 September 2026 | Five template sections; code metadata; reproducible validation suite; worked software use cases and scoped limitations |
| [NV4GP](https://doi.org/10.1016/j.softx.2026.103021) | 11 September 2026 | Original Software Publication; C1–C8; six figures; separate supplementary examples; ten-page typeset PDF inspected |
| [QEGuard](https://doi.org/10.1016/j.softx.2026.103017) | 12 September 2026 | C1–C8; two architecture/workflow figures; inspectable decisions, controlled examples and supplementary material |

The prepared article follows the shared software-first organization while
retaining detailed methodological and inferential evidence in its supplement.
