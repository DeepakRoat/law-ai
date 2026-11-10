from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class ChronologyItem(BaseModel):
    date_or_period: str = Field(description="Date or approximate timeframe of the event")
    event: str = Field(description="What happened clearly stated")


class CaseExtraction(BaseModel):
    detected_language: str = Field(
        description="Language the user wrote in (e.g., 'Hindi', 'Hinglish', 'English'). Replies MUST match this language style."
    )
    domain: Literal["CONSUMER_REFUND", "SECURITY_DEPOSIT", "UNPAID_SALARY", "OUT_OF_SCOPE"] = Field(
        description="Classify into one of the 3 supported everyday civil domains, or OUT_OF_SCOPE for criminal, family, property title, or complex litigation."
    )
    out_of_scope_reason: Optional[str] = Field(
        default=None,
        description="If OUT_OF_SCOPE, explain why this requires a human lawyer in India (e.g., criminal FIR/arrest, title dispute, divorce)."
    )
    complainant_name: Optional[str] = Field(default=None, description="Name of the user/victim if mentioned")
    opposite_party: Optional[str] = Field(default=None, description="Name of company, landlord, or employer")
    claim_amount_inr: Optional[str] = Field(default=None, description="Disputed amount in INR if mentioned")
    chronology: List[ChronologyItem] = Field(default_factory=list, description="Chronological list of events extracted from the user's messy story")
    evidence_have: List[str] = Field(default_factory=list, description="Proof/documents the user explicitly mentioned having")
    evidence_missing_or_needed: List[str] = Field(default_factory=list, description="Crucial proof the user needs to gather to strengthen their case")
    missing_critical_facts: List[str] = Field(
        default_factory=list,
        description="1 to 2 critical missing details needed before drafting a notice (e.g., opposite party name, amount)"
    )
    is_ready_for_action: bool = Field(
        description="True if we know what happened and basic context, or if the user wants immediate action/drafting."
    )
    next_mode: Literal["CLARIFY", "EXPLAIN_AND_DRAFT", "OPPONENT_SIMULATOR", "ESCALATE_TO_LAWYER"] = Field(
        description="Route to ESCALATE_TO_LAWYER if OUT_OF_SCOPE; OPPONENT_SIMULATOR if user wants to practice arguing; CLARIFY if story has almost zero facts; otherwise EXPLAIN_AND_DRAFT."
    )