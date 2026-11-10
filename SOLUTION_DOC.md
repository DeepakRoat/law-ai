# ⚖️ NyayaMitra: Solution Document
**Grounded Everyday Indian Civil Legal Aid Engine & Anti-Hallucination Guardrail**

* **Problem Chosen:** Problem 2 — Everyday Dispute AI Legal Aid Assistant
* **Repository:** [https://github.com/DeepakRoat/law-ai](https://github.com/DeepakRoat/law-ai)
* **Prototype:** Streamlit Web Console (`app.py`) powered by LangGraph & Google Gemini 2.5 Flash

---

## 1. Problem Statement & Selection Rationale
Over **70% of common grievances** in India revolve around everyday civil disputes:
1. **Unreturned rental security deposits** (landlord-tenant friction)
2. **Withheld salaries & Full-and-Final (F&F) settlements** (workplace disputes)
3. **Defective e-commerce items refused for refund** (consumer deficiency)

While individuals face genuine economic damages (₹15,000–₹1,00,000), hiring a licensed human advocate is economically unviable due to high legal fees, court delays, and procedural intimidation. Most citizens simply abandon legitimate claims.

**Why this problem:** Ordinary citizens lack the legal vocabulary to assert their statutory rights, draft formal notices, or counter counterparty excuses. Generic LLMs hallucinate non-existent sections, cite wrong acts, or attempt to give dangerous pseudo-legal advice in criminal matters. **NyayaMitra** bridges this gap through deterministic statutory grounding, a LangGraph state machine, and a zero-tolerance citation guardrail.

---

## 2. Core Assumptions & Scope Boundaries

### Assumptions
* **Messy Multi-lingual Inputs:** Users express complaints in raw colloquial phrasing (Hinglish, Hindi, regional English) without legal jargon.
* **Codified Ground Truth:** Legal aid must strictly anchor on codified Acts (*Consumer Protection Act 2019*, *Model Tenancy Act*, *Payment of Wages Act 1936*, *Industrial Disputes Act 1947*, *Indian Contract Act 1872*).
* **Strict Criminal Exclusion:** Any police FIR, arrest, or complex criminal/title matter is outside AI safety boundaries and triggers a strict human lawyer referral.

### Boundaries
* **Supported Domains (3):** Consumer Refunds, Landlord Security Deposits, and Unpaid Wages.
* **Safety Escape Hatch:** Immediate escalation to **NALSA Helpline 15100** and District Legal Services Authorities (DLSA) when criminal or out-of-scope triggers are detected.

---

## 3. System Architecture & How It Works

NyayaMitra is designed as a cyclic Directed Acyclic Graph (DAG) using **LangGraph** and **Google Gemini 2.5 Flash** (via `google-genai` SDK on `v1beta`):

```text
[User Input (Any Language)]
             │
             ▼
[Node 1: Intake & Build Case] ──(Gemini 2.5 Flash + Pydantic JSON Schema)
             │
             ├──► Domain: OUT_OF_SCOPE / Criminal ──► [Node 2D: Escalate to Lawyer & NALSA 15100]
             ├──► Next Mode: OPPONENT_SIMULATOR  ──► [Node 2C: Opponent Simulator & Rebuttal Coach]
             ├──► Missing Critical Facts          ──► [Node 2A: Empathetic Clarification Turn]
             └──► Default Civil Matter            ──► [Node 2B: Explain Rights & Draft 15-Day Notice]
                                                                     │
                                                                     ▼
                                                   [Node 3: Deterministic Regex Guardrail]
                                                                     │
                                                                     ▼
                                                          [Verified User Response]
```

### Key Components:
1. **Intake Engine (`intake_and_build_case`)**: Uses Gemini 2.5 Flash with `response_schema=CaseExtraction` to convert unstructured stories into chronology, facts, and available proof.
2. **Dual-Layer Retrieval**: Injects deterministic statutory provisions from `data/statutes_kb.json` supplemented by live API hits to Indian Kanoon (`api.kanoon.dev`).
3. **Deterministic Guardrail (`citation_guardrail`)**: Regex engine intercepts all Section/Order citations. Any statute not present in the verified KB is blocked with `[UNVERIFIED CITATION BLOCKED]`.
4. **Opponent Practice Simulator**: Roleplays stubborn Indian counterparties (e.g. "₹45k deducted for repainting") and immediately provides coached 2-sentence legal shut-down counters.

---

## 4. Scaling to Every Show / Production Domain ("How It Scales")
In production scenarios (e.g., nationwide legal awareness broadcasts, televised consumer grievance helplines, high-volume grievance portals), NyayaMitra is architected for zero-downtime extensibility:

1. **Schema-Driven Knowledge Ingestion:** Adding new civil legal domains (e.g., RERA real estate delay compensations, Motor Vehicle Act claims, cyber phishing refunds) requires **zero pipeline code changes**. Adding a new entry into `data/statutes_kb.json` automatically registers allowed sections, search queries, and remedy steps.
2. **Multi-Backend Grounding API:** Modular adapter pattern in `statutes_loader.py` supports official Indian Kanoon token auth, open REST endpoints, or enterprise internal case-law vectors.
3. **Stateless Client Caching:** Gemini client singleton caching (with `v1beta` HTTP options) minimizes handshake overhead, scaling easily on serverless container orchestrators (Render, Cloud Run, AWS ECS).
4. **Localized Multi-Lingual Adaptation:** Prompt architecture decouples language style detection from statutory reasoning, allowing the system to scale to 12+ Indian regional dialects without retraining.

---

## 5. Evaluation, Quality & Known Failure Modes

### Evaluation Matrix (from `/raw_outputs`)

| Scenario ID | Domain & Language | Node Triggered | Key Output | Guardrail Status |
| :--- | :--- | :--- | :--- | :--- |
| **TC-01** | Defective Laptop (Hinglish) | `explain_and_draft` | CPA 2019 Sec 2(47), 35; Formal 15-day refund notice | ✅ PASSED (0 Hallucinations) |
| **TC-02** | Landlord Deposit (English) | `opponent_simulator` | Rebuttal against repainting deduction + Rent cite | ✅ PASSED (0 Hallucinations) |
| **TC-03** | Unpaid Salary 2-Mo (Hindi) | `explain_and_draft` | Payment of Wages Act Sec 15; Recovery notice | ✅ PASSED (0 Hallucinations) |
| **TC-04** | Criminal Police FIR (Hindi) | `escalate_to_lawyer` | Zero fake penal codes; Direct referral to NALSA 15100 | ✅ PASSED (Safe Refusal) |

### Failure Modes & Defensive Mitigations
1. **Scanty User Information:** Activated `CLARIFY` mode to ask at most 1–2 friendly targeted questions before attempting advice.
2. **Criminal / High-Stakes Manipulation:** Strict classifier redirects to `escalate_to_lawyer`, blocking all legal section hallucination and providing government legal aid contact numbers (NALSA Helpline 15100).
3. **Statutory Section Hallucinations:** Regex guardrail cross-checks every cited section token against `data/statutes_kb.json`. Any mismatch is redacted.
4. **External Legal API Timeouts:** Graceful fallback pipeline: if the live API is slow or offline, NyayaMitra falls back safely to verified local statutory grounding without halting execution.

---

## 6. Deliverables & Submission Checklist
* [x] **Solution Doc (PDF):** [`Solution_Doc_NyayaMitra.pdf`](Solution_Doc_NyayaMitra.pdf) (Exact 2-page publication-ready PDF).
* [x] **Prototype Link:** [https://github.com/DeepakRoat/law-ai](https://github.com/DeepakRoat/law-ai) (Deployable on Streamlit Community Cloud).
* [x] **Raw Outputs Folder:** [`/raw_outputs`](raw_outputs/) containing 4 unedited scenario execution JSON logs and documentation.
* [x] **Walkthrough Video Script:** 3-minute structured demo script ready for recording.
