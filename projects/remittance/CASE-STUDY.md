# LedgerFlow — Remittance Matching & Review Automation

**Value:** Turn payment documents into validated ledger entries while keeping exceptions visible.

## Problem
Payment advice arrives in different formats. Missing references, partial payments and duplicate attachments make manual matching slow and error-prone.

## Solution
A document intake and reconciliation workspace that parses real text PDFs, spreadsheets and emails, extracts structured fields, matches customers and invoices, and holds uncertain items for review.

## Workflow
Upload/email → parse → extract → match → validate reference, currency and balance → post or review → reviewer correction → ledger receipt and audit history.

## Key technical components
Python, FastAPI, pypdf, openpyxl, MIME parsing, integer-cent arithmetic and transactional SQLite. An optional OpenAI-compatible extraction-draft adapter is supplied; the demonstrated default uses deterministic extraction.

## Reliability / safety
Document fingerprints and payment references prevent repeat postings. Overpayments, missing references and customer/invoice mismatches cannot auto-post. Reviewers must provide evidence before correcting a posting. Unsupported or scanned documents enter review; OCR is not claimed.

## Demo outcome
In the deliberately exception-heavy **10-document synthetic fixture**, 2 documents auto-posted, 7 entered review and 1 duplicate was blocked. A browser demonstration resolved a USD 300 partial payment and left USD 540 outstanding. These are fixture results, not a real-world automation-rate estimate.

## Stack
Python · FastAPI · SQLite · PDF/XLSX/CSV/EML parsers · JavaScript dashboard · optional JSON LLM drafts.

## Limits
Self-initiated demo, not client work. Mailbox transport, accounting and notifications are local simulated providers. One payment per attachment; text PDFs only. Live LLM and accounting integrations are not validated.
