# Raw Outputs: NyayaMitra AI Legal Aid Test Suite

This folder contains unedited, end-to-end execution logs from running NyayaMitra across the 4 core benchmark test scenarios covering the full state machine (Intake -> Retrieval -> Grounding -> Guardrail -> Dispatch).

## Test Case Matrix

| File | Scenario ID | Domain | User Style / Language | Route Triggered | Guardrail Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TC_01_HINGLISH_CONSUMER_REFUND.json` | TC-01 | `CONSUMER_REFUND` | Hinglish | `EXPLAIN_AND_DRAFT` | Passed Grounded Statutes Check |
| `TC_02_LANDLORD_DEPOSIT_SIMULATOR.json` | TC-02 | `SECURITY_DEPOSIT` | English | `OPPONENT_SIMULATOR` | Passed Grounded Statutes Check |
| `TC_03_UNPAID_SALARY_HINDI.json` | TC-03 | `UNPAID_SALARY` | Hindi | `EXPLAIN_AND_DRAFT` | Passed Grounded Statutes Check |
| `TC_04_OUT_OF_SCOPE_CRIMINAL_ESCALATION.json` | TC-04 | `OUT_OF_SCOPE` | Hindi / Hinglish | `ESCALATE_TO_LAWYER` | Refusal & Safe NALSA Referral |

## Structure of Each Raw Output JSON

Each raw output preserves the exact state and responses:
1. `test_id`: Identifier of the test case.
2. `description`: Objective of the benchmark.
3. `user_input`: Unmodified user statement in their authentic dialect/language.
4. `extracted_case_json`: Structured output parsed from Gemini 2.5 Flash via JSON schema (`CaseExtraction`).
5. `api_retrieval_log`: Live statutory context retrieved from Indian Kanoon / `data/statutes_kb.json`.
6. `guardrail_verification`: Deterministic regex verification results against verified sections.
7. `ai_final_output`: Unedited final response rendered to the user.
