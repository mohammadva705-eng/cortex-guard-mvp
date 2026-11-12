# Instructions for AI Contributors

Read the root `README.md` and the relevant module and tests before editing.

## Locked project boundaries

- Treat the CORTEX-GUARD MVP v1 decisions as authoritative.
- Analyze only the current page URL and visible text after a manual user action.
- Keep communication on `http://localhost:8000`; keep session data in memory.
- Do not access browser history, other tabs, local files, passwords, forms, keystrokes, or click activity.
- Do not add cloud services, databases, authentication, analytics, ML, or LLMs.
- Preserve schemas, labels, module order, and existing architecture unless the user explicitly changes the specification.
- Keep detection deterministic and limited to documented substring rules.
- Keep extension feedback within the badge, the single simple result popup, and Chrome notifications; do not add dashboards, overlays, or complex popup workflows.

## Change and verification practice

- Keep changes scoped to the requested module and preserve existing user changes.
- Add or update focused tests for behavior changes.
- Run `python -m pytest backend/app/tests -q` and `python backend/app/tests/demo_scenario.py` when Python dependencies are installed.
- Run `node --test tests/extension_popup.test.cjs` and Node syntax checks for changed extension scripts.
- Report checks that could not be run and any specification ambiguity instead of inventing behavior.
