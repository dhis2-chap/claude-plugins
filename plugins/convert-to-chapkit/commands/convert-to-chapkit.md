---
description: Convert an existing CHAP MLproject model repo into a chapkit 2.x service, with a numeric parity gate.
---

Invoke the `convert-to-chapkit` skill and begin its workflow now, starting at
step 0 (Orient).

If the user already mentioned any of these, pass them along to the skill:

- the **repo** to convert (a local folder path or a GitHub URL);
- a preferred **runner** (`ShellModelRunner`, `FunctionalModelRunner`, or
  `chapkit mlproject migrate`);
- **example data** to use for the baseline and the parity fixtures (CSV paths,
  or another chap-models repo to borrow from);
- a **base commit or branch** to convert from, or an open PR that should be
  merged first.

Otherwise the skill will ask for them. Do not start editing before the skill's
step 0 is complete - the pre-conversion baseline has to be captured before any
service code exists, or the parity gate is worthless.

Do not reimplement the workflow here - the skill is the single source of truth.
