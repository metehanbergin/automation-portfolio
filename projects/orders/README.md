# TradeFlow

Run the repository root setup, then open `/orders`. Source: `app/orders.py`.

## 90-second demonstration

1. Open DEMO-002: the supplier's first attempt has failed.
2. Advance to the next retry twice; attempt three opens a critical exception.
3. Close the detail, choose `approver` in the role control, reopen the order and enter recovery evidence.
4. Resolve; change to `operator`; send the fulfillment request. Attempt four dispatches once.
5. Check shipment and create/validate the invoice.
6. Change to `finance`; receive the sandbox payment and reconcile.
7. Inspect completion, the same source key, matching USD 2,240 invoice/payment and the entire failure/recovery history.

Other seeded orders demonstrate stock shortage, delayed shipping, payment mismatch and manual fulfillment. Creating new orders can also demonstrate invoice mismatch; API tests cover missing customer and source-price mismatch. Roles illustrate authorization decisions but are freely selectable in this synthetic sandbox.

See [CASE-STUDY.md](CASE-STUDY.md), [architecture.mmd](architecture.mmd) and `assets/`.
