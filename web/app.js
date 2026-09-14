const config = {
  remittance: {
    name: "LedgerFlow",
    tag: "FINANCE OPERATIONS",
    title: "Remittance inbox",
    sub: "Every payment accounted for. Every exception visible.",
    accent: "#087f74",
    soft: "#e8f4ef",
    sidebar: "#123832",
    icon: "↗",
    cta: "Process document",
    tabs: ["Overview", "Review queue", "Audit trail", "Architecture"],
  },
  leads: {
    name: "FieldFlow",
    tag: "SERVICE BUSINESS OPERATIONS",
    title: "From first hello to booked job",
    sub: "Qualification, quotes and follow-through in one place.",
    accent: "#376bc0",
    soft: "#edf3fc",
    sidebar: "#172d4c",
    icon: "⌁",
    cta: "New lead",
    tabs: ["Overview", "Pipeline", "Activity", "Architecture"],
  },
  guests: {
    name: "StayOps",
    tag: "GUEST OPERATIONS",
    title: "A thoughtful answer. A safer stay.",
    sub: "Property-aware responses with a human always within reach.",
    accent: "#976a38",
    soft: "#f6f0e6",
    sidebar: "#353226",
    icon: "⌂",
    cta: "New message",
    tabs: ["Overview", "Conversations", "Knowledge base", "Architecture"],
  },
  orders: {
    name: "TradeFlow",
    tag: "ORDER-TO-CASH CONTROL TOWER",
    title: "Operations, without blind spots",
    sub: "A single view from approved quote to reconciled payment.",
    accent: "#326e94",
    soft: "#eaf2f7",
    sidebar: "#182b3a",
    icon: "▦",
    cta: "Create order",
    tabs: ["Overview", "Orders", "Exceptions", "Architecture"],
  },
};
const app = document.querySelector("#app");
let project = location.pathname.slice(1),
  view = "Overview",
  state,
  selected = null,
  guestSelected = null,
  role = "operator",
  search = "",
  filter = "all",
  busy = false;
const esc = (s) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const money = (n) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format((n || 0) / 100);
const label = (s) =>
  String(s ?? "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
const count = (items, status) =>
  items.filter((x) => status.includes(x.status)).length;
function badge(status) {
  let color = [
    "posted",
    "resolved",
    "auto_resolved",
    "completed",
    "approved",
    "booked",
    "sandbox_delivered",
  ].includes(status)
    ? "green"
    : [
          "review",
          "approval",
          "quote_approval",
          "quoted",
          "pending",
          "retry_wait",
          "escalated",
          "awaiting_payment",
        ].includes(status)
      ? "amber"
      : ["blocked", "exception", "emergency", "rejected", "lost"].includes(
            status,
          )
        ? "red"
        : [
              "shipped",
              "human_resolved",
              "fulfillment",
              "invoicing",
              "reconciling",
            ].includes(status)
          ? "blue"
          : "gray";
  return `<span class="badge ${color}">${esc(label(status))}</span>`;
}
function metric(name, value, note) {
  return `<div class="metric"><div class="metric-label">${name}<span>↗</span></div><div class="metric-value">${value}</div><div class="metric-note">${note}</div></div>`;
}
function panel(title, sub, body, extra = "") {
  return `<section class="panel"><div class="panel-heading"><div><h2>${title}</h2>${sub ? `<p>${sub}</p>` : ""}</div>${extra}</div>${body}</section>`;
}
function btn(text, action, id = "", cls = "") {
  return `<button class="${cls}" data-action="${action}" data-id="${esc(id)}">${text}</button>`;
}
function toast(text, error = false) {
  let t = document.querySelector("#toast");
  t.textContent = text;
  t.style.background = error ? "#8f3935" : "#183b34";
  t.style.display = "block";
  setTimeout(() => (t.style.display = "none"), 4800);
}
async function api(path, data) {
  const response = await fetch(
    path,
    data
      ? {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        }
      : {},
  );
  if (!response.ok) {
    let e = await response.json();
    throw new Error(
      typeof e.detail === "string" ? e.detail : JSON.stringify(e.detail),
    );
  }
  return response.json();
}
async function load() {
  state = await api("/api/state");
  render();
}
async function command(action, entity = "", data = {}) {
  if (busy) return;
  busy = true;
  try {
    const result = await api(`/api/${project}/command`, {
      action,
      entity,
      data,
      role,
    });
    state = await api("/api/state");
    render();
    toast("Workflow updated · audit history saved");
    return result;
  } catch (e) {
    toast(e.message, true);
    throw e;
  } finally {
    busy = false;
  }
}
function shell(body) {
  let c = config[project];
  document.title = c
    ? c.name + " | Automation Portfolio"
    : "Automation Portfolio | Working demos";
  document.documentElement.style.cssText = c
    ? `--accent:${c.accent};--soft:${c.soft};--sidebar:${c.sidebar}`
    : "";
  return `<div class="shell ${c ? "" : "landing"}"><aside class="sidebar"><a class="brand" href="/"><span class="mark">${c?.icon || "M"}</span>${c?.name || "Metehan"}</a><div class="workspace-label">${c ? "WORKSPACE" : "AUTOMATION PORTFOLIO"}</div><nav class="side-nav">${(c?.tabs || ["Portfolio"]).map((tab, i) => `<button data-view="${tab}" class="${view === tab || !c ? "active" : ""}"><span class="side-icon">${["◫", "≡", "◷", "◇"][i]}</span>${tab}</button>`).join("")}</nav><div class="side-rule"></div><div class="workspace-label">EXPLORE THE DEMOS</div>${Object.entries(
    config,
  )
    .map(
      ([k, v]) =>
        `<a class="suite-link ${project === k ? "current" : ""}" href="/${k}"><span class="dot"></span>${v.name}</a>`,
    )
    .join(
      "",
    )}<div class="sidebar-bottom"><span class="sandbox-label">● SYNTHETIC SANDBOX</span><p>Working software. Fictional data.<br>Provider deliveries are simulated.</p><a class="suite-link" href="/docs" target="_blank">API documentation ↗</a></div></aside><div class="content"><header class="topbar"><div class="breadcrumb"><a href="/">Portfolio</a><span>/</span><strong>${c?.name || "Commercial automation demos"}</strong>${c ? `<span>/</span>${view}` : ""}</div><div class="top-meta"><span class="online">Persistent sandbox</span>${project === "orders" ? `<select id="role" aria-label="Demo role" class="role-select">${["operator", "approver", "finance", "viewer"].map((r) => `<option ${role === r ? "selected" : ""}>${r}</option>`).join("")}</select>` : ""}<span>Demo workspace</span><div class="avatar">MB</div></div></header><main class="main">${body}<p class="footnote">Synthetic demonstration • No client data or production results • Local provider receipts • <a href="/api/export">Export this sandbox’s audit data ↗</a></p></main></div></div>`;
}
function heading() {
  const c = config[project];
  return `<div class="page-heading"><div><div class="eyebrow">${c.tag}</div><h1>${c.title}</h1><p class="subheading">${c.sub}</p></div><div class="actions">${["leads", "orders"].includes(project) ? btn(project === "leads" ? "Advance 2 demo days" : "Advance 4 demo hours", "tick", "", "small") : ""}${btn(c.cta, "new", "", "primary")}</div></div>`;
}
function landing() {
  return `<div class="welcome"><div class="eyebrow">PYTHON · APIs · WORKFLOW ENGINEERING</div><h1>Reliable automation.<br>From input to resolution.</h1><p>Four working systems for the operational work that happens between your tools. Explore the workflows, trigger a failure, and see how a human gets the process moving again.</p></div><div class="portfolio-grid">${Object.entries(
    config,
  )
    .map(
      ([k, c], i) =>
        `<a class="portfolio-card" href="/${k}" style="--accent:${c.accent}"><div class="eyebrow">0${i + 1} / ${c.tag}</div><h2>${c.name}</h2><p>${{ remittance: "Turn incoming remittances into validated postings, with a review inbox for the payments that need a second look.", leads: "Run a cleaning business from lead capture to quote, calendar booking and customer follow-up.", guests: "Answer from approved property knowledge. Escalate unknowns, protect policies and learn through human review.", orders: "Coordinate inventory, fulfillment, invoicing and payment. Recover from supplier failures without duplicating work." }[k]}</p><footer><span class="tech-tags">FastAPI · SQLite · ${k === "guests" ? "Scoped retrieval" : k === "orders" ? "Durable workflows" : "Business rules"}</span><strong>Open demo ↗</strong></footer></a>`,
    )
    .join(
      "",
    )}</div><div class="notice" style="margin-top:24px">Each visitor receives an isolated sandbox. All business names, contacts, payments and reservations are fictional. AI provider adapters are optional; the default demo uses local extraction, retrieval and deterministic rules without API charges.</div>`;
}
function activities(entity = null, limit = 6) {
  let events = state.events
    .filter((e) => e.project === project && (!entity || e.entity === entity))
    .slice(-limit)
    .reverse();
  return `<div class="panel-body">${events.map((e) => `<div class="activity"><span class="event-dot"></span><div><strong>${esc(e.event)}</strong><p>${esc(e.detail)}</p><time>${esc(e.actor)} · ${new Date(e.at).toLocaleTimeString("en-GB")}</time></div></div>`).join("") || '<div class="empty">No activity yet</div>'}</div>`;
}
function remittanceTable(items) {
  return `<div class="table-wrap"><table><thead><tr><th>Document / customer</th><th>Invoice</th><th class="money">Payment</th><th>Decision</th><th></th></tr></thead><tbody>${items.map((d) => `<tr class="row"><td><strong>${esc(d.name)}</strong><small>${esc(d.fields.customer || "Extraction incomplete")}</small></td><td>${esc(d.fields.invoice || "—")}<small>${esc(d.fields.reference || "No reference")}</small></td><td class="money">${d.fields.amount ? money(d.fields.amount) : "—"}</td><td>${badge(d.status)}</td><td>${btn("Review ↗", "detail", d.id, "text-button small")}</td></tr>`).join("")}</tbody></table></div>`;
}
function remittanceView() {
  const b = state.remittance,
    docs = b.documents,
    posted = count(docs, ["posted", "resolved"]),
    review = count(docs, ["review"]),
    auto = count(docs, ["posted"]),
    pct = Math.round((auto / docs.length) * 100) || 0;
  let stats = `<div class="metrics">${metric("Documents processed", docs.length, "All uploaded and seeded documents")}${metric("Auto-posting rate", pct + "%", "<em>" + auto + " passed</em> every validation rule")}${metric("Needs review", review, "Exceptions held before posting")}${metric("Payment postings", money(b.postings.reduce((a, p) => a + p.amount, 0)), "Recorded in the sandbox ledger")}</div>`;
  if (view === "Review queue")
    return (
      stats +
      panel(
        "Review queue",
        "Resolve only after verifying the source and payment reference.",
        remittanceTable(docs.filter((d) => d.status === "review")),
      )
    );
  return (
    stats +
    `<div class="banner"><div><strong>${review} remittances need a second look</strong><div class="note">Partial payments, missing references and unmatched records are safely held.</div></div>${btn("Open review queue →", "queue", "", "small")}</div><div class="split"><div>${panel("Incoming remittances", "Matched against 8 synthetic invoices · USD", remittanceTable(docs), '<span class="pill">' + docs.length + " documents</span>")}</div><div>${panel("Processing decisions", "Measured from the current sandbox", `<div class="queue-summary"><div class="ring" style="--pct:${pct}"><span>${pct}%</span></div><div><div class="legend">Auto-posted <b>${auto}</b></div><div class="legend">Human review <b>${review}</b></div><div class="legend">Duplicate / rejected <b>${count(docs, ["duplicate", "rejected"])}</b></div></div></div>`)}${panel("Latest activity", "Every decision leaves a trace", activities(null, 5))}</div></div>`
  );
}
function leadCard(l) {
  return `<button class="lead-card" data-action="detail" data-id="${l.id}"><div class="conversation-head"><h3>${esc(l.name)}</h3>${l.urgent ? '<span class="badge amber">Urgent</span>' : ""}</div><p>${esc(l.service)}<br>${esc(l.location)} · ${l.rooms} rooms</p>${badge(l.status)}<footer><strong>${money(l.quote)}</strong><span class="score">${l.score}/100 fit</span></footer></button>`;
}
function leadsView() {
  const b = state.leads,
    ls = b.leads,
    qualified = ls.filter((l) => l.stage_history.includes("qualified")),
    quotes = ls.filter((l) => l.stage_history.includes("quoted")),
    booked = ls.filter((l) => l.stage_history.includes("booked")),
    pipeline = ls
      .filter((l) => !["completed", "lost", "exception"].includes(l.status))
      .reduce((s, l) => s + l.quote, 0);
  let stats = `<div class="metrics">${metric("Leads captured", ls.length, "Normalized contact records")}${metric("Booked jobs", booked.length, "Confirmed in the demo calendar")}${metric("Estimated pipeline", money(pipeline), "Open estimates · not earned revenue")}${metric("Pending human actions", count(ls, ["approval", "exception"]), "Quote approvals and service exceptions")}</div>`;
  let funnel = panel(
    "Lead-to-job funnel",
    "Cumulative lifecycle stages, not projected revenue",
    `<div class="pipeline-stats">${[
      ["Leads", ls.length],
      ["Qualified", qualified.length],
      ["Quotes sent", quotes.length],
      ["Jobs booked", booked.length],
      ["Completed", count(ls, ["completed"])],
    ]
      .map(
        ([n, v]) =>
          `<div class="pipeline-stage"><b>${v}</b><small>${n}</small></div>`,
      )
      .join("")}</div>`,
    `<span class="pill">Demo day ${b.clock}</span>`,
  );
  const lanes = [
    ["Needs a decision", ["approval", "exception"]],
    ["Quote sent", ["quoted", "reactivated"]],
    ["Booked", ["booked"]],
    ["Completed / lost", ["completed", "lost"]],
  ];
  return (
    stats +
    (view === "Overview" ? funnel : "") +
    `<div class="board">${lanes
      .map(
        ([name, statuses]) =>
          `<section class="lane"><div class="lane-head">${name}<span>${count(ls, statuses)}</span></div>${
            ls
              .filter((l) => statuses.includes(l.status))
              .map(leadCard)
              .join("") || '<div class="empty">No leads in this stage</div>'
          }</section>`,
      )
      .join(
        "",
      )}</div><p class="footnote">${count(ls, ["lost"])} lost leads · Duplicate intake returns the existing contact · Outreach reactivation requires recorded consent</p>`
  );
}
function guestChat(c) {
  if (!c) return '<div class="empty">Select a conversation</div>';
  let p = state.guests.properties.find((p) => p.id === c.property);
  return `<div class="chat-pane"><div class="chat-header"><div><h2>${esc(c.guest)}</h2><p>${esc(p?.name || "Unverified property")} · ${esc(c.reservation)} · ${c.language.toUpperCase()}</p></div>${badge(c.status)}</div><div class="bubble-label">Guest message</div><div class="bubble">${esc(c.message)}</div><div class="bubble-label" style="text-align:right">${c.status === "auto_resolved" ? "Approved knowledge response" : "Safe response"}</div><div class="bubble reply">${esc(c.response)}</div>${c.human_answer ? `<div class="bubble-label" style="text-align:right">Human response</div><div class="bubble reply">${esc(c.human_answer)}</div>` : ""}<div class="source-box"><strong>${esc(c.reason)}</strong>${c.sources.length ? c.sources.map((s) => `${esc(s.scope)} / ${esc(s.question)} · retrieval score ${s.score}`).join("<br>") : "No unsupported property facts disclosed."}</div>${["escalated", "emergency"].includes(c.status) ? btn("Respond & resolve", "detail", c.id, "primary small") : btn("View audit history", "detail", c.id, "small")}<p class="footnote">${c.status === "auto_resolved" ? "Response quoted from approved knowledge." : "A delivery receipt is recorded in the sandbox outbox."} Language: heuristic detection.</p></div>`;
}
function guestsView() {
  const b = state.guests,
    cs = b.conversations,
    auto = count(cs, ["auto_resolved"]);
  let stats = `<div class="metrics">${metric("Conversations", cs.length, "Across " + b.properties.length + " demo properties")}${metric("Auto-resolved", Math.round((auto / cs.length) * 100 || 0) + "%", auto + " answered from approved knowledge")}${metric("Escalations", count(cs, ["escalated"]), "Waiting for a host’s judgment")}${metric("Emergencies", count(cs, ["emergency"]), "Urgent alert + safe standby message")}</div>`;
  if (view === "Knowledge base") return stats + knowledgeView();
  let chosen = cs.find((c) => c.id === guestSelected) || cs[0];
  return (
    stats +
    panel(
      "Guest conversations",
      "English · Spanish · Turkish | Property scope enforced",
      `<div class="inbox"><div class="conversation-list">${cs
        .slice()
        .reverse()
        .map(
          (c) =>
            `<button class="conversation ${chosen?.id === c.id ? "active" : ""}" data-chat="${c.id}"><div class="conversation-head"><strong>${esc(c.guest)}</strong><span class="pill">${c.language.toUpperCase()}</span></div><p>${esc(c.message)}</p>${badge(c.status)}</button>`,
        )
        .join("")}</div>${guestChat(chosen)}</div>`,
      `<span class="pill">${b.proposals.filter((p) => p.status === "pending").length} knowledge approvals</span>`,
    ) +
    `<div class="policy">Policy guardrails: refunds, early check-in and late checkout require human approval. Unknown facts stay unknown.</div>`
  );
}
function knowledgeView() {
  let b = state.guests;
  return (
    panel(
      "Knowledge approval queue",
      "Sanitized proposals become usable only after a separate review.",
      `<div class="panel-body">${b.proposals.map((p) => `<div class="activity"><span class="event-dot"></span><div style="flex:1"><strong>${esc(p.question)}</strong><p>${esc(p.answer)}</p><span class="pill">${p.scope} · ${p.language.toUpperCase()}</span> ${badge(p.status)}</div>${p.status === "pending" ? btn("Review", "knowledge", p.id, "small") : ""}</div>`).join("") || '<div class="empty">Answer an unknown guest question and propose a knowledge entry to begin.</div>'}</div>`,
    ) +
    panel(
      "Approved knowledge",
      "Global policies and property-specific facts stay separate.",
      `<div class="table-wrap"><table><thead><tr><th>Question</th><th>Scope</th><th>Languages</th><th>Source</th></tr></thead><tbody>${b.knowledge.map((k) => `<tr><td><strong>${esc(k.question)}</strong><small>${esc(k.answers.en || Object.values(k.answers)[0])}</small></td><td>${esc(k.scope)}</td><td>${Object.keys(k.answers).join(" · ").toUpperCase()}</td><td><small>${esc(k.source)}</small></td></tr>`).join("")}</tbody></table></div>`,
    )
  );
}
function orderTable(items) {
  return `<div class="table-wrap"><table><thead><tr><th>Order / account</th><th>Fulfillment</th><th class="money">Value</th><th>Workflow state</th><th></th></tr></thead><tbody>${items.map((o) => `<tr class="row"><td><strong>${esc(o.key)}</strong><small>${esc(o.customer)}</small></td><td>${esc(label(o.route))}<small>${o.quantity} × ${esc(o.product)}</small></td><td class="money">${money(o.total)}</td><td>${badge(o.status)}</td><td>${btn("Open ↗", "detail", o.id, "text-button small")}</td></tr>`).join("")}</tbody></table></div>`;
}
function ordersView() {
  const b = state.orders,
    os = b.orders,
    ex = b.exceptions.filter((e) => e.status === "open"),
    breached = ex.filter((e) => e.due < b.clock);
  let stats = `<div class="metrics">${metric("Active orders", os.filter((o) => o.status !== "completed").length, "Across warehouse, supplier and custom routes")}${metric("Open order value", money(os.filter((o) => o.status !== "completed").reduce((a, o) => a + o.total, 0)), "Synthetic pipeline · not revenue")}${metric("Open exceptions", ex.length, breached.length + " SLA breaches · " + count(os, ["retry_wait"]) + " retries scheduled")}${metric("Pending approvals", count(os, ["quote_approval"]), "Account pricing applied before approval")}</div>`;
  if (view === "Exceptions") return stats + exceptionsView();
  return (
    stats +
    `<div class="banner"><div><strong>Recovery is part of the workflow</strong><div class="note">${count(os, ["retry_wait"])} supplier request awaiting retry · ${ex.length} exceptions held for review · demo hour ${b.clock}</div></div>${btn("Exception desk →", "queue", "", "small")}</div>` +
    panel(
      "Order-to-cash flow",
      "A durable state machine, with explicit approvals at the decision points",
      `<div class="orders-flow">${[
        ["Account", "Identity & terms"],
        ["Quote", "Human approval"],
        ["Inventory", "Reserve or route"],
        ["Fulfillment", "Retry safely"],
        ["Shipment", "Track & notify"],
        ["Invoice", "Validate total"],
        ["Payment", "Reconcile"],
      ]
        .map(
          ([n, s], i) =>
            `<div class="flow-node ${i < 4 ? "done" : ""}"><strong>${String(i + 1).padStart(2, "0")} · ${n}</strong><small>${s}</small></div>`,
        )
        .join("")}</div>`,
    ) +
    `<div class="split"><div>${panel("Active order book", "Open an order to advance, inspect or recover its workflow.", orderTable(os))}</div><div>${panel("Exception radar", "Severity and service-level deadlines", exceptionItems(ex.slice(0, 5)))}${panel("Latest events", "Provider attempts and business decisions", activities(null, 4))}</div></div>`
  );
}
function exceptionItems(items) {
  return `<div class="exception-list">${items.map((e) => `<div class="exception-item"><div class="severity-icon">!</div><div><strong>${esc(label(e.code))}</strong><p>${esc(e.severity)} · ${e.due < state.orders.clock ? "SLA breached" : "Due in " + (e.due - state.orders.clock) + " demo hours"}</p></div>${btn("Inspect", "detail", e.order, "text-button small")}</div>`).join("") || '<div class="empty">No open exceptions</div>'}</div>`;
}
function exceptionsView() {
  return panel(
    "Exception desk",
    "A documented resolution resumes the same order; it does not create a replacement.",
    `<div class="table-wrap"><table><thead><tr><th>Exception</th><th>Severity</th><th>Deadline</th><th>State</th><th></th></tr></thead><tbody>${state.orders.exceptions.map((e) => `<tr><td><strong>${esc(label(e.code))}</strong><small>${esc(e.detail)}</small></td><td>${badge(e.severity === "critical" ? "emergency" : "review")}</td><td>Hour ${e.due}<small>${e.due < state.orders.clock && e.status === "open" ? "SLA breached" : ""}</small></td><td>${badge(e.status)}</td><td>${btn("Open order", "detail", e.order, "small")}</td></tr>`).join("")}</tbody></table></div>`,
  );
}
const diagrams = {
  remittance: [
    [
      ["Email / upload", "EML · text PDF · XLSX · CSV"],
      ["Extraction", "Structured fields + source text"],
      ["Validation", "Customer · invoice · reference · balance"],
    ],
    [
      ["Safe posting", "Atomic invoice update + ledger receipt"],
      ["Human review", "Correct fields with evidence or reject"],
      ["Audit trail", "Decision history + notification outbox"],
    ],
  ],
  leads: [
    [
      ["Lead intake", "Normalize email · suppress duplicates"],
      ["Qualification", "Service · area · urgency · score"],
      ["Quote approval", "Deterministic estimate + human decision"],
    ],
    [
      ["Booking", "Calendar conflict checks + confirmation"],
      ["Lifecycle scheduler", "Reminders · follow-up · recovery"],
      ["CRM state", "Job completion · consent-based reactivation"],
    ],
  ],
  guests: [
    [
      ["Guest message", "Language + verified reservation"],
      ["Scoped retrieval", "Global policy + this property only"],
      ["Policy gate", "Emergency · protected request · unknown"],
    ],
    [
      ["Known answer", "Quote approved knowledge + source"],
      ["Human escalation", "Safe standby + urgent alert when needed"],
      ["Reviewed learning", "Sanitize → propose → approve → retrieve"],
    ],
  ],
  orders: [
    [
      ["Source order", "Idempotency key + account pricing"],
      ["Approval & inventory", "Role gate + atomic stock reservation"],
      ["Fulfillment router", "Warehouse · supplier · POD · manual"],
    ],
    [
      ["Recovery engine", "Bounded backoff · SLA · human resolution"],
      ["Shipment & invoice", "Tracking receipt + quote-total validation"],
      ["Cash reconciliation", "Finance role · payment match · completion"],
    ],
  ],
};
function architecture() {
  return (
    panel(
      "How the system works",
      "Business decisions stay visible at each system boundary.",
      `<div class="architecture">${diagrams[project].map((row, i) => `<div class="arch-caption">${i ? "RESOLUTION & FEEDBACK" : "INPUT & DECISIONS"}</div><div class="arch-row">${row.map(([title, desc], j) => `${j ? '<div class="arch-arrow">→</div>' : ""}<div class="arch-node"><strong>${title}</strong><p>${desc}</p></div>`).join("")}</div>`).join("")}<div class="notice">FastAPI endpoints → SQLite transaction → state + append-only application events + idempotent sandbox receipts. All external business providers are simulated. ${project === "guests" ? "Local TF-IDF-style retrieval; approved answers in EN / ES / TR. Free-form model generation is disabled by default." : ""}${project === "orders" ? "Demo roles illustrate enforced action permissions; this role switch is not production authentication." : ""}</div></div>`,
    ) +
    panel(
      "Integration boundaries",
      "What is running here, and what a client deployment would connect.",
      `<div class="panel-body"><div class="readonly-data"><div><dt>Working now</dt><dd>Parsing, validation, state transitions, review actions, persistence and audit export</dd></div><div><dt>Simulated providers</dt><dd>${{ remittance: "Mailbox delivery, accounting ledger and notifications", leads: "Email delivery, CRM provider and calendar provider", guests: "Guest messaging and host-alert provider", orders: "Supplier, warehouse, POD, carrier, bank and invoicing provider" }[project]}</dd></div><div><dt>Production handoff</dt><dd>Provider credentials, webhooks, identity, background worker and integration acceptance tests</dd></div><div><dt>Data boundary</dt><dd>Isolated browser session, fictional fixtures, 7-day sandbox expiry</dd></div></div></div>`,
    )
  );
}
function auditView() {
  return panel(
    "Workflow audit trail",
    "Chronological business events and sandbox delivery receipts.",
    `<div class="table-wrap"><table><thead><tr><th>Time / actor</th><th>Event</th><th>Detail</th></tr></thead><tbody>${state.events
      .filter((e) => e.project === project)
      .slice()
      .reverse()
      .map(
        (e) =>
          `<tr><td>${new Date(e.at).toLocaleTimeString("en-GB")}<small>${esc(e.actor)}</small></td><td><strong>${esc(e.event)}</strong><small>${esc(e.entity)}</small></td><td>${esc(e.detail)}</td></tr>`,
      )
      .join("")}</tbody></table></div>`,
  );
}
function render() {
  let body;
  if (!config[project]) body = landing();
  else
    body =
      heading() +
      (view === "Architecture"
        ? architecture()
        : ["Audit trail", "Activity"].includes(view)
          ? auditView()
          : {
              remittance: remittanceView,
              leads: leadsView,
              guests: guestsView,
              orders: ordersView,
            }[project]());
  app.innerHTML = shell(body);
  if (selected) drawDetail(selected);
  bind();
}
function drawer(title, subtitle, body) {
  document.querySelector(".drawer-backdrop")?.remove();
  document.body.insertAdjacentHTML(
    "beforeend",
    `<div class="drawer-backdrop"><section class="drawer" role="dialog" aria-modal="true" aria-label="${esc(title)}"><header class="drawer-header"><div><h2>${title}</h2><span class="details-count">${subtitle}</span></div>${btn("×", "close", "", "close")}</header><div class="drawer-body"><div class="form-error" role="alert"></div>${body}</div></section></div>`,
  );
  document.querySelector(".drawer .close").focus();
  bind();
}
function field(labelText, name, value = "", type = "text") {
  return `<label class="field">${labelText}<input name="${name}" type="${type}" value="${esc(value)}" required></label>`;
}
function selectField(title, name, options, value) {
  return `<label class="field">${title}<select name="${name}">${options
    .map((o) => {
      let [v, t] = Array.isArray(o) ? o : [o, o];
      return `<option value="${esc(v)}" ${v === value ? "selected" : ""}>${esc(t)}</option>`;
    })
    .join("")}</select></label>`;
}
function formButton(text, action, id = "", cls = "primary") {
  return `<button type="submit" data-submit="${action}" data-id="${esc(id)}" class="${cls}">${text}</button>`;
}
function sourcePanel(title, text) {
  return panel(
    title,
    "",
    `<div class="panel-body"><pre class="source-text">${esc(text)}</pre></div>`,
  );
}
function newForm() {
  selected = null;
  let body = "";
  if (project === "remittance")
    body = `<div class="notice">Upload an actual text PDF, XLSX, CSV or EML, or paste a structured remittance. Scanned PDFs are routed to review; this demo does not claim OCR.</div><form id="upload-form"><label class="field">Attachment<input name="file" type="file" accept=".pdf,.xlsx,.csv,.eml,.txt" required></label><p>${formButton("Upload & process", "upload")}</p></form><hr style="border:0;border-top:1px solid var(--line);margin:24px 0"><form><label class="field">Email body<textarea name="text" rows="8">Customer: Northline Studio\nInvoice: INV-1004\nAmount: 640.00\nReference: BANK-NEW-001\nCurrency: USD</textarea></label><p>${formButton("Process remittance", "intake")}</p></form>`;
  if (project === "leads")
    body = `<form><div class="field-grid">${field("Contact name", "name", "Jamie Taylor")}${field("Email", "email", "jamie@example.test", "email")}${selectField("Service area", "location", ["Central", "North", "West", "Outside area"])}${field("Rooms", "rooms", 3, "number")}</div><label class="field">Service request<textarea name="message">Moving out next week. Please quote a full clean for three rooms.</textarea></label><label class="checkbox"><input name="consent" type="checkbox" checked>Opted into future service updates (synthetic consent)</label>${formButton("Qualify & prepare quote", "intake")}</form>`;
  if (project === "guests")
    body = `<div class="notice">Try a Wi-Fi question, an unknown luggage question, a late-checkout request or an emergency. Reservation identity controls which property facts can be retrieved.</div><form>${selectField(
      "Reservation",
      "reservation",
      state.guests.reservations.map((r) => [
        r.id,
        r.id +
          " · " +
          r.guest +
          " · " +
          state.guests.properties.find((p) => p.id === r.property).name,
      ]),
    )}<label class="field" style="margin-top:18px">Guest message<textarea name="message">Can we store our luggage at the property?</textarea></label><p>${formButton("Route message", "intake")}</p></form>`;
  if (project === "orders")
    body = `<div class="notice">Every source order has a stable idempotency key. Re-submit the same payload with the same key to inspect duplicate suppression.</div><form><div class="field-grid">${field("Source order key", "key", "WEB-" + Date.now().toString().slice(-6))}${selectField(
      "Account",
      "account",
      state.orders.accounts.map((a) => [a.id, a.name]),
    )}${selectField(
      "Product",
      "sku",
      state.orders.catalog.map((i) => [i.sku, i.name]),
    )}${field("Quantity", "quantity", 4, "number")}</div>${selectField(
      "Demo scenario",
      "scenario",
      [
        ["normal", "Normal fulfillment"],
        ["supplier_failure", "Supplier API fails three times"],
        ["delayed", "Shipment delayed"],
        ["payment_mismatch", "Payment amount mismatch"],
        ["invoice_mismatch", "Invoice total mismatch"],
        ["manual", "Manual fulfillment"],
      ],
    )}<p>${formButton("Create order & quote", "intake")}</p></form>`;
  drawer(config[project].cta, "New input · synthetic sandbox", body);
}
function drawDetail(id) {
  if (project === "remittance") {
    let d = state.remittance.documents.find((d) => d.id === id);
    if (!d) return;
    drawer(
      d.name,
      `${esc(d.id)} · ${label(d.status)}`,
      `<div class="notice">${esc(d.resolution || d.reasons.join(" · ") || "All validation checks passed.")}</div>${sourcePanel("Original document", d.source || "No readable text available")}${panel(
        "Extracted fields",
        "Rule validation score is not model probability.",
        `<div class="panel-body"><dl class="readonly-data">${Object.entries(
          d.fields,
        )
          .map(
            ([k, v]) =>
              `<div><dt>${label(k)}</dt><dd>${k === "amount" ? money(v) : esc(v || "Missing")}</dd></div>`,
          )
          .join(
            "",
          )}</dl><p class="footnote">Validation score ${d.confidence}/100 · Actual processing duration ${d.duration_ms} ms</p></div>`,
      )}${
        d.status === "review"
          ? panel(
              "Review decision",
              "Confirm the invoice, amount and bank reference before posting.",
              `<div class="panel-body"><form><div class="field-grid">${selectField(
                "Verified invoice",
                "invoice",
                state.remittance.invoices.map((i) => [
                  i.id,
                  i.id + " · " + money(i.total - i.paid) + " open",
                ]),
                d.fields.invoice,
              )}${field("Payment amount (USD)", "amount", (d.fields.amount || 0) / 100, "number")}${field("Verified payment reference", "reference", d.fields.reference || "")}</div><label class="field">Evidence / correction note<textarea name="note" placeholder="What did you verify against the source?"></textarea></label><p class="actions">${formButton("Approve posting", "approve", id)}${btn("Reject document", "reject", id, "danger")}</p></form></div>`,
            )
          : ""
      }${panel("Workflow history", "Persisted business events", activities(id, 20))}`,
    );
  }
  if (project === "leads") {
    let l = state.leads.leads.find((l) => l.id === id);
    if (!l) return;
    drawer(
      l.name,
      `${esc(l.id)} · ${label(l.status)}`,
      `<div class="notice">${esc(l.status === "booked" ? "Booking confirmed" : l.status === "completed" ? "Job completed; review request recorded" : l.reason)} · ${l.score}/100 fit · ${esc(l.classification)}</div>${sourcePanel("Original service request", l.message)}${panel("CRM record", "Estimate prepared from service and room count.", `<div class="panel-body"><dl class="readonly-data"><div><dt>Service</dt><dd>${esc(l.service)}</dd></div><div><dt>Estimate</dt><dd>${money(l.quote)}</dd></div><div><dt>Contact</dt><dd>${esc(l.email)}</dd></div><div><dt>Location / rooms</dt><dd>${esc(l.location)} / ${l.rooms}</dd></div><div><dt>Calendar</dt><dd>${esc(l.slot || "Not booked")}</dd></div><div><dt>Marketing consent</dt><dd>${l.consent ? "Recorded (demo)" : "Not recorded"}</dd></div></dl></div>`)}<div class="actions">${l.status === "approval" ? btn("Approve & send quote", "approve", id, "primary") : ""}${l.status === "booked" ? btn("Mark job completed", "complete", id, "primary") : ""}${["approval", "quoted", "exception", "reactivated"].includes(l.status) ? btn("Mark lost", "lose", id, "danger") : ""}</div>${["quoted", "reactivated"].includes(l.status) ? `<form style="margin-top:20px">${selectField("Appointment slot", "slot", ["Tomorrow · 09:00", "Tomorrow · 13:00", "Friday · 09:00", "Friday · 13:00"])}<p>${formButton("Accept quote & book", "book", id)}</p></form>` : ""}${["exception", "lost"].includes(l.status) ? `<form style="margin-top:20px"><label class="field">Resolution note<textarea name="note" placeholder="Record manual coverage confirmation or reason to reopen."></textarea></label><p>${formButton("Reopen for quote approval", "reopen", id)}</p></form>` : ""}<div style="margin-top:22px">${panel("Customer lifecycle", "Events and sandbox provider receipts", activities(id, 20))}</div>`,
    );
  }
  if (project === "guests") {
    let c = state.guests.conversations.find((c) => c.id === id);
    if (!c) return;
    drawer(
      c.guest,
      `${esc(c.reservation)} · ${label(c.status)}`,
      `${sourcePanel("Guest question", c.message)}<div class="policy">${esc(c.reason)}</div>${["escalated", "emergency"].includes(c.status) ? `<form style="margin-top:20px"><label class="field">Human response<textarea name="answer" placeholder="Write a verified answer for this guest."></textarea></label>${c.status !== "emergency" ? `<label class="checkbox"><input name="learn" type="checkbox" checked>Propose a reusable knowledge entry for separate review</label><label class="field">Generalized question<input name="question" value="${esc(c.message)}"></label>` : ""}<p>${formButton("Send human response", "answer", id)}</p></form>` : ""}${panel("Response history", "Guest replies and host alerts", activities(id, 20))}`,
    );
  }
  if (project === "orders") {
    let o = state.orders.orders.find((o) => o.id === id),
      e = state.orders.exceptions.find((e) => e.id === o?.exception);
    if (!o) return;
    let next = {
      inventory: "Check inventory",
      fulfillment: "Send fulfillment request",
      shipped: "Check shipment",
      invoicing: "Create & validate invoice",
      awaiting_payment: "Receive sandbox payment",
      reconciling: "Reconcile payment",
    }[o.status];
    drawer(
      o.key,
      `${esc(o.customer)} · ${label(o.status)}`,
      `<div class="notice">Current demo role: <strong>${role}</strong>. Quote and exception approval require approver; payment actions require finance. Change role in the top bar.</div>${panel("Order summary", "Immutable source identity; durable workflow progress.", `<div class="panel-body"><dl class="readonly-data"><div><dt>Product / quantity</dt><dd>${esc(o.product)} × ${o.quantity}</dd></div><div><dt>Approved quote total</dt><dd>${money(o.total)}</dd></div><div><dt>Fulfillment route</dt><dd>${esc(label(o.route))}</dd></div><div><dt>Provider attempts</dt><dd>${o.attempts}</dd></div><div><dt>Invoice</dt><dd>${o.invoice ? esc(o.invoice.id) + " · " + money(o.invoice.total) : "Not issued"}</dd></div><div><dt>Payment</dt><dd>${o.payment ? money(o.payment.amount) : "Not received"}</dd></div></dl></div>`)}<div class="actions">${o.status === "quote_approval" ? btn("Approve quote", "approve", id, "primary") : ""}${next ? btn(next, "advance", id, "primary") : ""}${o.status === "retry_wait" ? btn("Advance to next retry", "tick", id, "primary") : ""}</div>${
        e
          ? panel(
              "Resolve: " + esc(label(e.code)),
              e.detail,
              `<div class="panel-body"><div class="notice">${label(e.severity)} severity · SLA hour ${e.due} · ${e.retryable ? "Safe retry after recovery confirmation" : "Human decision required"}</div><form>${
                e.code === "missing_customer"
                  ? selectField(
                      "Verified account",
                      "account",
                      state.orders.accounts.map((a) => [a.id, a.name]),
                    )
                  : ""
              }${e.code === "payment_mismatch" ? field("Verified total received (cents)", "amount", o.total, "number") : ""}<label class="field">Resolution evidence<textarea name="note" placeholder="Record the verified recovery or correction."></textarea></label><p>${formButton("Resolve & resume workflow", "resolve", id)}</p></form></div>`,
            )
          : ""
      }<div style="margin-top:22px">${panel("Workflow history", "Stable order identity across retries and recovery", activities(id, 25))}</div>`,
    );
  }
}
function knowledgeDrawer(id) {
  let p = state.guests.proposals.find((p) => p.id === id);
  drawer(
    "Review knowledge proposal",
    `${p.scope} · ${p.language.toUpperCase()} · Separate approval required`,
    `<div class="notice">Private emails, phone numbers and labeled access codes were redacted by rules. Check names, accuracy, policy and property scope before approval.</div><form>${field("Generalized question", "question", p.question)}<label class="field" style="margin-top:16px">Approved answer<textarea name="answer" rows="6">${esc(p.answer)}</textarea></label><p class="actions">${formButton("Approve knowledge entry", "knowledge", id)}${btn("Reject proposal", "reject-knowledge", id, "danger")}</p></form>`,
  );
}
function bind() {
  document.querySelectorAll("[data-view]").forEach(
    (el) =>
      (el.onclick = () => {
        view = el.dataset.view;
        selected = null;
        render();
      }),
  );
  document.querySelectorAll("[data-chat]").forEach(
    (el) =>
      (el.onclick = () => {
        guestSelected = el.dataset.chat;
        render();
      }),
  );
  document.querySelector("#role")?.addEventListener("change", (e) => {
    role = e.target.value;
    render();
  });
  document.querySelectorAll("[data-action]").forEach(
    (el) =>
      (el.onclick = async () => {
        let { action, id } = el.dataset;
        try {
          if (action === "close") {
            selected = null;
            document.querySelector(".drawer-backdrop")?.remove();
            return;
          }
          if (action === "new") return newForm();
          if (action === "detail") {
            selected = id;
            drawDetail(id);
            return;
          }
          if (action === "knowledge") return knowledgeDrawer(id);
          if (action === "queue") {
            view = project === "remittance" ? "Review queue" : "Exceptions";
            render();
            return;
          }
          if (action === "tick") {
            await command(
              "tick",
              "",
              project === "leads" ? { days: 2 } : { hours: 4 },
            );
            return;
          }
          if (action === "reject-knowledge") {
            await command("knowledge", id, { reject: true });
            document.querySelector(".drawer-backdrop")?.remove();
            return;
          }
          await command(
            action,
            id,
            action === "reject"
              ? { note: "Rejected after manual source review" }
              : {},
          );
        } catch (e) {
          document
            .querySelector(".form-error")
            ?.replaceChildren(document.createTextNode(e.message));
        }
      }),
  );
  document.querySelectorAll(".drawer form").forEach(
    (form) =>
      (form.onsubmit = async (e) => {
        e.preventDefault();
        const button = e.submitter;
        if (!button) return;
        button.disabled = true;
        let data = Object.fromEntries(new FormData(form));
        for (let box of form.querySelectorAll("input[type=checkbox]"))
          data[box.name] = box.checked;
        try {
          let result;
          if (button.dataset.submit === "upload") {
            let response = await fetch("/api/remittance/upload", {
              method: "POST",
              body: new FormData(form),
            });
            let json = await response.json();
            if (!response.ok) throw Error(json.detail);
            result = json;
            await load();
            toast("Attachment parsed and routed");
          } else
            result = await command(
              button.dataset.submit,
              button.dataset.id,
              data,
            );
          if (
            button.dataset.submit === "intake" ||
            button.dataset.submit === "upload"
          ) {
            selected = result.id;
            if (project === "guests") guestSelected = result.id;
            render();
          } else if (button.dataset.submit === "knowledge") {
            document.querySelector(".drawer-backdrop")?.remove();
            view = "Knowledge base";
            render();
          }
        } catch (err) {
          document
            .querySelector(".form-error")
            ?.replaceChildren(document.createTextNode(err.message));
        } finally {
          button.disabled = false;
        }
      }),
  );
}
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    selected = null;
    document.querySelector(".drawer-backdrop")?.remove();
  }
  if (e.key === "Tab") {
    let dialog = document.querySelector(".drawer");
    if (!dialog) return;
    let focusable = [
      ...dialog.querySelectorAll("button,input,textarea,select,a[href]"),
    ].filter((x) => !x.disabled);
    if (!focusable.length) return;
    let first = focusable[0],
      last = focusable.at(-1);
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }
});
load().catch((e) => {
  app.innerHTML = `<div class="boot"><h1>Unable to open the sandbox</h1><p>${esc(e.message)}</p><button id="retry">Try again</button></div>`;
  document.querySelector("#retry").onclick = () => location.reload();
});
