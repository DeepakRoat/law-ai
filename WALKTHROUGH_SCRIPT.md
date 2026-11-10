# 🎬 NyayaMitra: 3-Minute Walkthrough Video Script

Use this script to record your quick 3-minute demo screen recording (using Loom, OBS, or Windows Game Bar `Win + G`).

---

### [00:00 - 00:35] Problem Selection & The Big Idea
* **Screen:** Show the Streamlit UI with the NyayaMitra header.
* **What to say:**
  > "Hi everyone, for this challenge I selected **Problem 2: Building an everyday legal aid assistant**, which I named **NyayaMitra**."
  > "In India, over 70% of common civil disputes involve unreturned landlord deposits, unpaid salaries, or e-commerce refund refusals. Ordinary citizens can't afford human lawyers for ₹30,000 to ₹50,000 disputes, and generic AI often hallucinates fake legal sections or gives dangerous advice. NyayaMitra solves this using LangGraph, Google Gemini 2.5 Flash, and a deterministic anti-hallucination guardrail."

---

### [00:35 - 01:25] Demo 1: Hinglish Consumer Refund & Notice Drafting
* **Screen:** Click the sidebar test preset: **'📦 Hinglish Defective Laptop Refund'** and click send.
* **What to say:**
  > "Here, a user writes in raw Hinglish about a cracked laptop where customer care refused a return citing 'no return policy'. Notice what happens behind the scenes:"
  > "1. In Node 1, Gemini 2.5 Flash extracts a structured chronology, evidence available, and missing facts using strict JSON schema."
  > "2. In Node 2, it grounds on the Consumer Protection Act 2019 and queries live Indian Kanoon records."
  > "3. It generates a 4-part legal response: a plain-language explanation of their rights, and a formal 15-Day Registered Post Legal Notice draft with [BRACKETED] placeholders ready to send to the seller."

---

### [01:25 - 02:05] Demo 2: Opponent Simulator & Rebuttal Coach
* **Screen:** Click preset **'🏠 Landlord Deposit Simulator (Argue)'**.
* **What to say:**
  > "One of our most unique features is the **Opponent Simulator**."
  > "When a landlord makes an unfair excuse—like deducting ₹45,000 for repainting—NyayaMitra roleplays as the stubborn landlord, and then immediately steps out of character to coach the citizen with the exact 2-sentence legal rebuttal citing the rent agreement and allowed tenancy provisions."

---

### [02:05 - 02:45] Demo 3: Safety Guardrail & Criminal Escalation
* **Screen:** Click preset **'🚨 Criminal FIR / Arrest (Referral Test)'** and then switch to the **'🛡️ Guardrail & API Audit'** tab on the right.
* **What to say:**
  > "Safety and zero-hallucination are critical. In this third case, the user asks about an urgent criminal FIR and arrest."
  > "Rather than guessing fake criminal sections, our state machine immediately triggers `escalate_to_lawyer`. It strictly refuses legal advice and provides direct government helpline details: NALSA Helpline 15100 and District Legal Services Authorities."
  > "Additionally, on the right pane, our deterministic regex guardrail audits every statute citation against `statutes_kb.json`, ensuring 100% verified legal references."

---

### [02:45 - 03:00] Conclusion & Scalability
* **Screen:** Show the GitHub repository (`DeepakRoat/law-ai`).
* **What to say:**
  > "NyayaMitra is fully modular: new legal domains like RERA or Motor Vehicle claims can be added simply by updating the JSON knowledge base with zero code changes. The code, test suite, and 2-page solution document are all available on my GitHub repository. Thank you!"
