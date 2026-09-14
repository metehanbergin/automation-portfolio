# FieldFlow — Lead-to-Booking Operations

**Value:** Keep service inquiries moving from first contact to an approved quote and a booked job.

## Problem
A small cleaning business can lose inquiries between its website, quotes, calendar and follow-ups. Staff need one view of what happens next.

## Solution
A complete synthetic sales workspace with normalized intake, duplicate suppression, service classification, transparent scoring, price calculation, quote approval, booking and customer lifecycle events.

## Workflow
Website inquiry → classify service/area/urgency → score → estimate → approval → quote → conflict-checked booking → confirmation/reminder → job completion → review request. A demo scheduler also handles no-response recovery and consent-based reactivation.

## Key technical components
FastAPI commands, Python business rules, SQLite CRM/calendar state and an idempotent communication outbox. An optional OpenAI-compatible qualification-draft adapter is available; default qualification is explicitly rule-based.

## Reliability / safety
Normalized email identifies duplicate contacts. Out-of-area leads enter an exception queue. Occupied slots cannot be double-booked. Dormant-lead outreach requires recorded consent. Repeated scheduler runs do not duplicate the same follow-up receipt.

## Demo outcome
A synthetic three-room move-out inquiry generated a USD 295 quote. The UI blocked an occupied appointment, accepted an alternative slot and recorded confirmation receipts. No actual quote was sent or customer booking created.

## Stack
Python · FastAPI · SQLite · JavaScript · lifecycle state machine · optional JSON LLM drafts.

## Limits
Fictional cleaning business and contacts. Prices are illustrative, not market pricing. Email, CRM and calendar providers are simulated. Clock advancement is operator-driven; real scheduling and provider authentication are deployment work.
