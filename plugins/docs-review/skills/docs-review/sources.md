# Documentation sources

The single list of what `docs-review` can check. `scripts/pick.py` parses the
tables below, so keep the column order. To add a source, add a row; to drop one,
delete it.

Columns:

- **repo**: `org/name` on GitHub.
- **team**: `modeling`, `climate` or `shared` (shared is included whenever either
  team is selected).
- **group**: the unit users can pick and the unit one reviewer subagent covers.
- **docs**: comma-separated paths (files or directories) holding the docs. Code
  outside these paths is what the docs are checked against.
- **nav**: how the published navigation is defined, so pages missing from it can be
  found. `mkdocs:<file>`, `myst:<file>`, `imports:<glob>` (pages imported from code),
  or `-` when there is no site.
- **published**: where readers see it.
- **audience**: who the docs are for.

## Sources

| repo | team | group | docs | nav | published | audience |
|------|------|-------|------|-----|-----------|----------|
| dhis2-chap/chap-core | modeling | core | docs, README.md | mkdocs:mkdocs.yml | https://dhis2-chap.github.io/chap-core/ (also imported into chap.dhis2.org) | DHIS2 implementers, newcomers, model developers, contributors |
| dhis2-chap/chap-site | modeling | core | docs, README.md | mkdocs:mkdocs.yml | https://chap.dhis2.org | everyone; landing page that imports chap-core docs and syncs the Modeling App user guides (see sync-config.json) |
| dhis2-chap/chap-frontend | modeling | core | apps/modeling-app/docs, README.md | imports:apps/modeling-app/docs/*.ts | in the Modeling App, and chap.dhis2.org | Modeling App users |
| dhis2-chap/chapkit | modeling | chapkit | docs, README.md | mkdocs:mkdocs.yml | https://dhis2-chap.github.io/chapkit | model developers |
| dhis2-chap/chapkit-images | modeling | chapkit | README.md | - | GitHub | model developers |
| dhis2-chap/chap-python-sdk | modeling | sdk | docs, README.md | mkdocs:mkdocs.yml | https://knutdrand.github.io/chap-python-sdk/ | model developers (Python) |
| dhis2-chap/chap_r_sdk | modeling | sdk | vignettes, README.md | - | https://dhis2-chap.github.io/chap_r_sdk/ (pkgdown) | model developers (R) |
| dhis2-chap/chap_model_template | modeling | examples | README.md | - | GitHub | model developers |
| dhis2-chap/chap_model_template_r | modeling | examples | README.md | - | GitHub | model developers |
| dhis2-chap/minimalist_example | modeling | examples | README.md | - | GitHub | newcomer model developers |
| dhis2-chap/minimalist_example_r | modeling | examples | README.md | - | GitHub | newcomer model developers |
| dhis2-chap/minimalist_example_uv | modeling | examples | README.md | - | GitHub | newcomer model developers |
| dhis2-chap/minimalist_example_renv | modeling | examples | README.md | - | GitHub | newcomer model developers |
| dhis2-chap/minimalist_multiregion | modeling | examples | README.md | - | GitHub | model developers |
| dhis2-chap/minimalist_multiregion_r | modeling | examples | README.md | - | GitHub | model developers |
| dhis2-chap/minimalist_example_lag | modeling | examples | README.md | - | GitHub | model developers |
| dhis2-chap/minimalist_example_lag_r | modeling | examples | README.md | - | GitHub | model developers |
| dhis2-chap/Minimalist_probabilistic_bayesian | modeling | examples | README.md | - | GitHub | model developers |
| dhis2-chap/Minimalist_probabilistic_non-bayesian | modeling | examples | README.md | - | GitHub | model developers |
| dhis2-chap/chapkit_minimalist_example | modeling | examples | README.md | - | GitHub | model developers |
| dhis2-chap/Assessment_example_chap_compatible | modeling | examples | README.md | - | GitHub | model developers |
| dhis2-chap/Assessment_example_singlepred | modeling | examples | README.md | - | GitHub | model developers |
| dhis2-chap/chap-workshop-python | modeling | examples | README.md | - | GitHub | workshop participants |
| dhis2-chap/chap-workshop-r | modeling | examples | README.md | - | GitHub | workshop participants |
| dhis2/open-climate-service | climate | ocs | docs, README.md | mkdocs:mkdocs.yml | https://dhis2.github.io/open-climate-service/ | OCS installers, operators and users |
| dhis2/climate-tools | climate | climate-tools | docs, README.md | myst:docs/myst.yml | https://climate-tools.dhis2.org | data engineers and data scientists working with climate data for DHIS2 |
| dhis2/climate-app | climate | climate-app | README.md | - | GitHub | DHIS2 users importing weather and climate data |
| dhis2-chap/climate-sre | shared | sre | . | - | GitHub (internal) | the team: server provisioning and operations |

## Journeys

Starting points for the journey check. Each is a reader with a goal; the reviewer
follows the docs the way that reader would. Edit freely.

| team | reader | goal | starts at |
|------|--------|------|-----------|
| modeling | newcomer model developer | get a first model running and evaluated with `chap eval` | chap-core `external_models/newcomer.md`, minimalist_example |
| modeling | experienced modeller | wrap an existing model and evaluate it | chap-core `external_models/experienced_modeller.md`, chapkit docs |
| modeling | DHIS2 implementer | install Chap next to DHIS2, keep it updated and add models | chap-core `modeling-app/index.md` |
| modeling | Modeling App user | create a dataset, an evaluation and a prediction | chap-frontend `apps/modeling-app/docs/user-guides` |
| modeling | chap-core contributor | set up a dev environment and open a first PR | chap-core `contributor/index.md` |
| climate | OCS installer | install OCS and get data into DHIS2 on a schedule | open-climate-service `docs/setup_guide.md` |
| climate | climate data scientist | fetch and aggregate climate data for DHIS2 org units | climate-tools `docs/getting-started/intro.md` |
| climate | DHIS2 user | import weather and climate data with the Climate app | climate-app `README.md` |
