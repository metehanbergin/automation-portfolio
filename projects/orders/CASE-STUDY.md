# TradeFlow — Order-to-Cash Control Tower

**Value:** Coordinate order fulfillment and cash reconciliation while making failures recoverable.

## Problem
An order crosses pricing, inventory, fulfillment, shipping, invoicing and payment systems. A failure in one step should neither disappear nor create duplicate downstream work.

## Solution
A durable workflow control tower for a fictional B2B product business, with warehouse, supplier, print-on-demand and manual fulfillment routes.

## Workflow
Source key → account pricing → quote approval → inventory/routing → fulfillment → shipment → invoice validation → payment → reconciliation. Exceptions carry severity, deadlines, resolution evidence and workflow history.

## Key technical components
FastAPI, transactional SQLite state, stable idempotency keys, bounded exponential retry delays, server-enforced demo roles and idempotent local provider receipts.

## Reliability / safety
Duplicate keys return the same order; conflicting payloads are rejected. Stock cannot reserve below zero. Quote approval and finance actions require the corresponding demo roles. Payment/invoice mismatches block completion. Recovery resumes the same order.

## Demo outcome
A synthetic supplier returned three failures. The workflow stopped, opened a critical exception, accepted an approver's recovery evidence, dispatched on attempt four and reconciled USD 2,240. Tests verified a single fulfillment receipt and no duplicate order creation.

## Stack
Python · FastAPI · SQLite · JavaScript · state machine · outbox receipts · retry/exception engine.

## Limits
Flagship engineering demonstration, not an enterprise production deployment. Supplier, warehouse, POD, carrier, invoice and bank providers are simulated. Demo roles are selectable, not real identity authentication. Clock advancement is manual; a background worker and production controls remain integration work.
