# Validation record

Authoring date: 15 September 2026. All inputs and provider responses were synthetic.

## Automated

- 59 pytest cases passed locally on Python 3.12, including the optional model adapter contract tests.
- JavaScript syntax check passed with `node --check web/app.js`.
- Actual text PDF, XLSX, CSV and MIME email attachments were parsed in tests.
- SQLite concurrent duplicate intake produced one order identity across eight concurrent requests.
- An interrupted transaction rolled back; committed state remained readable after database reinitialization.
- Two deprecation warnings originate from the FastAPI/Starlette/httpx test stack. They do not indicate failed workflow assertions.

## Browser acceptance

- LedgerFlow: opened an actual partial-payment review, recorded evidence and posted USD 300 to INV-1002; remaining balance USD 540. Dashboard and audit changed to resolved.
- FieldFlow: created Jamie Taylor's synthetic move-out inquiry, generated a USD 295 quote, approved it, rejected an occupied slot and booked an available slot. Calendar and email receipts were recorded locally.
- StayOps: inspected EN/ES/TR source-based answers and emergency routing. Answered an unknown luggage question, approved a separate knowledge entry and verified a subsequent exact question was automatically answered within the same property scope.
- TradeFlow: supplier failed three times, reached escalation, was released by the approver, dispatched on attempt four and completed invoicing/payment reconciliation under finance role. The original source key was retained.
- Actual app screenshots were saved in each `projects/*/assets` directory. Videos are captioned sequences of these real app captures, not continuous screen recordings.

## Not claimed

- No live LLM inference, live mailbox, external calendar, CRM, bank, supplier or guest-messaging acceptance test.
- No paid hosting or production backend deployment.
- Docker CLI was unavailable locally; container build is not reported as tested.
- No production authentication, durable job runner, tamper-evident ledger, load testing or SLA guarantee.
- No n8n, Make, Zapier, Lodgify or GoHighLevel deployment is claimed by these projects.
- Synthetic cohort results are demonstrations of rules and scenarios, not measured customer outcomes or estimates of real-world automation rates.
