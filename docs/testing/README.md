# GovConnectX testing hub

This folder is the permanent home for repeatable quality checks. Keep the checklists with the code so we can rerun them after future changes, before merges, and before releases.

## Documents

- [Manual regression checklist](MANUAL_REGRESSION_CHECKLIST.md) — repeatable browser/API checks across citizen, official, department and admin workflows.
- [Pull request and release gate](RELEASE_GATE.md) — the checks required before a PR is considered ready to merge or a release is considered ready.
- [Test evidence log](TEST_EVIDENCE.md) — dated record of automated results and manual runs. A test is not marked passed until it has actually been run.

## Local test commands

From the repository root:

Backend (Python unittest suite):
```bash
cd backend
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Frontend:
```bash
cd frontend
npm ci
npm run typecheck
npm run build
```

Run backend and frontend in separate terminals for browser checks. See the root README for environment setup.

## Rules for recording results

1. Record the branch and commit SHA tested.
2. Mark each check **PASS**, **FAIL**, or **NOT RUN**. Never infer a pass from code review or from a different commit's CI.
3. For failures, record the exact reproduction steps, expected result, actual result, and relevant log/error.
4. Re-run affected checks after a fix.
5. Keep test accounts and evidence fixtures non-production and free of real citizen personal data.
6. Do not commit secrets, access tokens, private evidence files, or real user data.

## Current baseline

See [TEST_EVIDENCE.md](TEST_EVIDENCE.md) for the exact Phase 6 CI run IDs and outstanding manual checks.
