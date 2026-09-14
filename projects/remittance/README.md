# LedgerFlow

Run the repository root setup, then open `/remittance`. Source: `app/remittance.py`.

## 60-second demonstration

1. Inspect the seeded inbox: 2 posted, 7 review, 1 duplicate.
2. Open `partial-payment.txt`; compare USD 300 to INV-1002's USD 840 balance.
3. Enter evidence confirming the partial payment, then approve.
4. Inspect the resolved state and audit receipt; USD 540 remains outstanding.
5. Open Architecture to explain parsing, validation and the simulated ledger boundary.

For actual uploads, run `python scripts/generate_samples.py` after installing `requirements-dev.txt`. Upload one of `sample-data/remittance.pdf`, `.xlsx`, `.csv`, `.eml` or `.txt` in a fresh sandbox. The fixture pays INV-1004 in full; uploading a second format using the same reference should be blocked as a duplicate payment.

Assets are actual application captures. `walkthrough.mp4` is a captioned sequence of those captures, not a continuous screen recording. See [CASE-STUDY.md](CASE-STUDY.md) and [architecture.mmd](architecture.mmd).
