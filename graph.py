import os
from typing import TypedDict, List, Dict, Any, Optional
from dotenv import load_dotenv
from google.genai import types, errors
from langgraph.graph import StateGraph, END

from schemas import CaseExtraction
from statutes_loader import get_domain_context, validate_citations

# Import Google Gemini configuration and client helpers
from config import (
    get_gemini_client,
    reset_gemini_client,
    get_model_id,
    get_default_safety_settings,
    API_VERSION,
)

# Import AI prompts and formatters
from prompts import (
    INTAKE_SYSTEM_INSTRUCTION,
    format_intake_user_prompt,
    get_clarify_system_instruction,
    format_clarify_user_prompt,
    get_explain_and_draft_system_instruction,
    format_explain_and_draft_user_prompt,
    get_opponent_simulator_system_instruction,
    format_opponent_simulator_user_prompt,
    get_escalate_system_instruction,
    format_escalate_user_prompt,
    format_guardrail_footer,
)

load_dotenv()


class LawyerState(TypedDict):
    user_input: str
    chat_history: List[Dict[str, str]]
    force_mode: Optional[str]
    use_live_api: bool
    case_data: Optional[Dict[str, Any]]
    api_retrieval_log: Optional[Dict[str, Any]]
    final_response: str
    guardrail_report: Dict[str, Any]


def intake_and_build_case_node(state: LawyerState) -> Dict[str, Any]:
    """Node 1: Turns a messy story into structured chronology, evidence, and routing."""
    client = get_gemini_client()
    model_id = get_model_id()

    history_turns = state.get("chat_history", [])[-6:]
    history_text = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in history_turns])
    user_content = format_intake_user_prompt(history_text, state["user_input"])

    response = client.models.generate_content(
        model=model_id,
        contents=user_content,
        config=types.GenerateContentConfig(
            http_options=types.HttpOptions(api_version=API_VERSION),
            system_instruction=INTAKE_SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=CaseExtraction,
            temperature=0.1,
            safety_settings=get_default_safety_settings(),
        ),
    )

    # In Google GenAI SDK, parsed structured object is available on response.parsed
    if isinstance(response.parsed, CaseExtraction):
        extracted = response.parsed
    elif isinstance(response.parsed, dict):
        extracted = CaseExtraction.model_validate(response.parsed)
    elif response.text:
        extracted = CaseExtraction.model_validate_json(response.text)
    else:
        raise ValueError("Empty or unparseable response received from Gemini model.")

    case_dict = extracted.model_dump()

    if state.get("force_mode") and state["force_mode"] != "AUTO":
        case_dict["next_mode"] = state["force_mode"]

    return {"case_data": case_dict}


def clarify_node(state: LawyerState) -> Dict[str, Any]:
    """Node 2A: Asks 1-2 clarifying questions in the user's comfortable language."""
    client = get_gemini_client()
    model_id = get_model_id()
    c = state["case_data"]

    system_instruction = get_clarify_system_instruction(c.get("detected_language", "English"))
    user_content = format_clarify_user_prompt(
        domain=c.get("domain", ""),
        evidence_have=c.get("evidence_have"),
        missing_critical_facts=c.get("missing_critical_facts")
    )

    res = client.models.generate_content(
        model=model_id,
        contents=user_content,
        config=types.GenerateContentConfig(
            http_options=types.HttpOptions(api_version=API_VERSION),
            system_instruction=system_instruction,
            temperature=0.3,
            safety_settings=get_default_safety_settings(),
        ),
    )
    return {
        "final_response": res.text or "",
        "api_retrieval_log": {"api_source": "skipped_on_clarify", "live_records": []},
        "guardrail_report": {"passed": True, "flagged_citations": [], "note": "Clarification turn"}
    }


def explain_and_draft_node(state: LawyerState) -> Dict[str, Any]:
    """Node 2B: Fetches laws from JSON file + API, explains options, and drafts a Legal Notice."""
    client = get_gemini_client()
    model_id = get_model_id()
    c = state["case_data"]
    ctx = get_domain_context(c["domain"], use_live_api=state.get("use_live_api", True))

    system_instruction = get_explain_and_draft_system_instruction(c.get("detected_language", "English"))
    user_content = format_explain_and_draft_user_prompt(ctx["prompt_context"], c)

    res = client.models.generate_content(
        model=model_id,
        contents=user_content,
        config=types.GenerateContentConfig(
            http_options=types.HttpOptions(api_version=API_VERSION),
            system_instruction=system_instruction,
            temperature=0.2,
            safety_settings=get_default_safety_settings(),
        ),
    )
    return {
        "final_response": res.text or "",
        "api_retrieval_log": ctx["api_data"]
    }


def opponent_simulator_node(state: LawyerState) -> Dict[str, Any]:
    """Node 2C: Roleplays the opposite side (Landlord/Company/HR) and coaches the user."""
    client = get_gemini_client()
    model_id = get_model_id()
    c = state["case_data"]
    ctx = get_domain_context(c["domain"], use_live_api=state.get("use_live_api", True))

    system_instruction = get_opponent_simulator_system_instruction(
        detected_language=c.get("detected_language", "English"),
        opposite_party=c.get("opposite_party")
    )
    user_content = format_opponent_simulator_user_prompt(ctx["prompt_context"], c, state["user_input"])

    res = client.models.generate_content(
        model=model_id,
        contents=user_content,
        config=types.GenerateContentConfig(
            http_options=types.HttpOptions(api_version=API_VERSION),
            system_instruction=system_instruction,
            temperature=0.3,
            safety_settings=get_default_safety_settings(),
        ),
    )
    return {
        "final_response": res.text or "",
        "api_retrieval_log": ctx["api_data"]
    }


def escalate_to_lawyer_node(state: LawyerState) -> Dict[str, Any]:
    """Node 2D: Honest refusal & human lawyer referral when problem is criminal or out-of-scope."""
    client = get_gemini_client()
    model_id = get_model_id()
    c = state["case_data"]

    system_instruction = get_escalate_system_instruction(
        detected_language=c.get("detected_language", "English"),
        out_of_scope_reason=c.get("out_of_scope_reason")
    )
    user_content = format_escalate_user_prompt(state["user_input"])

    res = client.models.generate_content(
        model=model_id,
        contents=user_content,
        config=types.GenerateContentConfig(
            http_options=types.HttpOptions(api_version=API_VERSION),
            system_instruction=system_instruction,
            temperature=0.1,
            safety_settings=get_default_safety_settings(),
        ),
    )
    return {
        "final_response": res.text or "",
        "api_retrieval_log": {"api_source": "blocked_out_of_scope", "live_records": []},
        "guardrail_report": {
            "passed": True,
            "flagged_citations": [],
            "note": "Out-of-scope escalation triggered safely (Real Lawyer Required)."
        }
    }


def citation_guardrail_node(state: LawyerState) -> Dict[str, Any]:
    """Node 3: Deterministic Regex Guardrail validating output citations against data/statutes_kb.json."""
    c = state["case_data"]
    raw_text = state["final_response"]
    validation = validate_citations(raw_text, c["domain"])
    api_source = state.get("api_retrieval_log", {}).get("api_source", "local_file")
    footer = format_guardrail_footer(api_source, validation)

    return {
        "final_response": validation["cleaned_text"] + footer,
        "guardrail_report": validation
    }


def route_after_intake(state: LawyerState) -> str:
    mode = state["case_data"]["next_mode"]
    if mode == "ESCALATE_TO_LAWYER" or state["case_data"]["domain"] == "OUT_OF_SCOPE":
        return "escalate_to_lawyer"
    if mode == "OPPONENT_SIMULATOR":
        return "opponent_simulator"
    if mode == "CLARIFY":
        return "clarify"
    return "explain_and_draft"


def build_lawyer_graph():
    workflow = StateGraph(LawyerState)

    workflow.add_node("intake_and_build_case", intake_and_build_case_node)
    workflow.add_node("clarify", clarify_node)
    workflow.add_node("explain_and_draft", explain_and_draft_node)
    workflow.add_node("opponent_simulator", opponent_simulator_node)
    workflow.add_node("escalate_to_lawyer", escalate_to_lawyer_node)
    workflow.add_node("citation_guardrail", citation_guardrail_node)

    workflow.set_entry_point("intake_and_build_case")

    workflow.add_conditional_edges(
        "intake_and_build_case",
        route_after_intake,
        {
            "clarify": "clarify",
            "explain_and_draft": "explain_and_draft",
            "opponent_simulator": "opponent_simulator",
            "escalate_to_lawyer": "escalate_to_lawyer",
        }
    )

    workflow.add_edge("clarify", END)
    workflow.add_edge("escalate_to_lawyer", END)
    workflow.add_edge("explain_and_draft", "citation_guardrail")
    workflow.add_edge("opponent_simulator", "citation_guardrail")
    workflow.add_edge("citation_guardrail", END)

    return workflow.compile()
