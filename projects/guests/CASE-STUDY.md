# StayOps — Guarded Guest Support & Reviewed Knowledge

**Value:** Answer known property questions and put uncertain or urgent requests in the right human queue.

## Problem
Multi-property support needs the correct property facts, consistent policies and a safe way to handle questions the knowledge base cannot answer.

## Solution
A multilingual guest desk with reservation identification, global/property-scoped retrieval, approved responses, policy gates and a separate knowledge-review workflow.

## Workflow
Message → language heuristic → reservation match → scoped retrieval → known answer / human escalation / urgent alert. For reusable unknowns: human response → sanitized proposal → separate approval → knowledge update → next matching answer.

## Key technical components
Python lexical retrieval with TF-IDF-style weighting, explicit scope filtering, EN/ES/TR approved answers, SQLite state and local messaging receipts. An optional OpenAI-compatible knowledge-draft adapter is included; free-form generation is disabled by default.

## Reliability / safety
No automatic refunds or early/late stay exceptions. No property facts are disclosed for an unidentified reservation. Emergency phrases trigger a safe standby response and urgent host alert. Learning cannot silently promote protected policy decisions.

## Demo outcome
The initial synthetic set routed 3 of 6 messages to approved answers, 2 to escalation and 1 to emergency handling. A luggage question was answered automatically only after its proposed entry received separate approval. A cross-property test kept that learned answer unavailable to another property.

## Stack
Python · FastAPI · scoped retrieval · SQLite · multilingual knowledge · optional JSON LLM drafts.

## Limits
Self-initiated property-operations demo, not hospitality client experience. Retrieval is lexical, language/emergency detection is heuristic, and support is bounded to the tested examples. Messaging and urgent delivery are simulated. No live LLM, PMS or lodging-platform integration is claimed.
