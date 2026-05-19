from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


KnowledgeEntryType = Literal["document", "term", "playbook", "field"]
Importance = Literal["critical", "high", "medium", "low"]
CourseRelevance = Literal["primary", "secondary"]
ExampleType = Literal["concept", "document_review", "risk", "workflow"]
Relation = Literal["related_document", "related_term", "required_for", "explains"]


class KnowledgeAppliesTo(BaseModel):
    situation_types: list[str] = Field(default_factory=list)
    playbooks: list[str] = Field(default_factory=list)
    document_keys: list[str] = Field(default_factory=list)
    field_keys: list[str] = Field(default_factory=list)


class KnowledgeSourceLocation(BaseModel):
    primary_sources: list[str] = Field(default_factory=list)
    secondary_sources: list[str] = Field(default_factory=list)
    source_notes: str | None = None


class KnowledgeFieldHelp(BaseModel):
    field_key: str
    label: str
    importance: Importance


class KnowledgeCourseReference(BaseModel):
    chapter_id: str
    title: str
    relevance: CourseRelevance
    reason: str


class KnowledgeCourseExample(BaseModel):
    label: str
    example_type: ExampleType
    text: str
    visibility: Literal["internal_only"] = "internal_only"
    source: Literal["course_notes", "dani_notes", "swissedge_summary"] = "swissedge_summary"


class RelatedKnowledgeEntry(BaseModel):
    knowledge_key: str
    label: str
    relation: Relation


class KnowledgeEntry(BaseModel):
    knowledge_key: str
    title: str
    type: KnowledgeEntryType
    summary: str
    badges: list[str] = Field(default_factory=list)
    applies_to: KnowledgeAppliesTo
    why_it_matters: str
    where_it_usually_appears: KnowledgeSourceLocation
    typical_sections: list[str] = Field(default_factory=list)
    search_terms: list[str] = Field(default_factory=list)
    helps_complete_fields: list[KnowledgeFieldHelp] = Field(default_factory=list)
    course_references: list[KnowledgeCourseReference] = Field(default_factory=list)
    course_examples: list[KnowledgeCourseExample] = Field(default_factory=list)
    common_mistakes: list[str] = Field(default_factory=list)
    manual_verification_checklist: list[str] = Field(default_factory=list)
    related_entries: list[RelatedKnowledgeEntry] = Field(default_factory=list)
    guardrail: str


GUARDRAIL = "Guidance only. Not evidence. Not verified. Not investment advice."


def _applies(
    *,
    document_keys: list[str] | None = None,
    field_keys: list[str] | None = None,
) -> KnowledgeAppliesTo:
    return KnowledgeAppliesTo(
        situation_types=["tender_offer"],
        playbooks=["issuer_tender_offer", "tender_offer"],
        document_keys=document_keys or [],
        field_keys=field_keys or [],
    )


def _course(reason: str, relevance: CourseRelevance = "primary") -> list[KnowledgeCourseReference]:
    return [
        KnowledgeCourseReference(
            chapter_id="issuer_tender_offers",
            title="Issuer Tender Offers",
            relevance=relevance,
            reason=reason,
        )
    ]


def _example(label: str, text: str, example_type: ExampleType = "document_review") -> list[KnowledgeCourseExample]:
    return [
        KnowledgeCourseExample(
            label=label,
            example_type=example_type,
            text=text,
            visibility="internal_only",
            source="swissedge_summary",
        )
    ]


def _doc(
    key: str,
    title: str,
    summary: str,
    why: str,
    fields: list[tuple[str, str, Importance]],
    sections: list[str],
    search_terms: list[str],
    related: list[tuple[str, str, Relation]],
    *,
    badges: list[str] | None = None,
    source_notes: str | None = None,
) -> KnowledgeEntry:
    return KnowledgeEntry(
        knowledge_key=key,
        title=title,
        type="document",
        summary=summary,
        badges=badges or ["Tender offer", "Document"],
        applies_to=_applies(document_keys=[key]),
        why_it_matters=why,
        where_it_usually_appears=KnowledgeSourceLocation(
            primary_sources=["SEC EDGAR filing detail page", "Tender offer exhibits"],
            secondary_sources=["Company investor relations page", "Press release"],
            source_notes=source_notes or "Confirm the exact document and amendment date manually before relying on it.",
        ),
        typical_sections=sections,
        search_terms=search_terms,
        helps_complete_fields=[KnowledgeFieldHelp(field_key=f, label=label, importance=importance) for f, label, importance in fields],
        course_references=_course(f"{title} is part of the issuer tender offer documentation map."),
        course_examples=_example(
            f"Reviewing {title}",
            "Use this guidance to identify where the document sits in the package and what case fields it may support. Do not treat presence of a document as accepted evidence.",
        ),
        common_mistakes=[
            "Treating a candidate link as verified evidence.",
            "Using a summary page when the actual exhibit or amendment is required.",
            "Missing later amendments that change terms or dates.",
        ],
        manual_verification_checklist=[
            "Open the SEC detail page or issuer source manually.",
            "Confirm company name, filing type, accession or exhibit reference.",
            "Check whether a later amendment supersedes the document.",
            "Map the document to the required resource/checklist item before accepting any extracted field.",
        ],
        related_entries=[RelatedKnowledgeEntry(knowledge_key=k, label=label, relation=relation) for k, label, relation in related],
        guardrail=GUARDRAIL,
    )


def _term(
    key: str,
    title: str,
    summary: str,
    why: str,
    sections: list[str],
    search_terms: list[str],
    related: list[tuple[str, str, Relation]],
    *,
    importance: Importance = "high",
) -> KnowledgeEntry:
    return KnowledgeEntry(
        knowledge_key=key,
        title=title,
        type="term",
        summary=summary,
        badges=["Tender offer", "Term"],
        applies_to=_applies(field_keys=[key]),
        why_it_matters=why,
        where_it_usually_appears=KnowledgeSourceLocation(
            primary_sources=["Offer to Purchase", "SC TO-I amendments"],
            secondary_sources=["Press release", "FAQ or transaction page"],
            source_notes="Terms should be checked in the governing document, not only in a press summary.",
        ),
        typical_sections=sections,
        search_terms=search_terms,
        helps_complete_fields=[KnowledgeFieldHelp(field_key=key, label=title, importance=importance)],
        course_references=_course(f"{title} affects manual review of issuer tender economics or mechanics."),
        course_examples=_example(
            f"{title} check",
            "Record the term only as draft until Dani confirms the wording against the source document.",
            "concept",
        ),
        common_mistakes=[
            "Copying a term without its conditions or exceptions.",
            "Ignoring whether an amendment changed the value.",
            "Treating extracted wording as verified before review.",
        ],
        manual_verification_checklist=[
            "Find the term in the source document.",
            "Read surrounding conditions and definitions.",
            "Check for amendments or supplements.",
            "Accept, edit, or reject the field explicitly.",
        ],
        related_entries=[RelatedKnowledgeEntry(knowledge_key=k, label=label, relation=relation) for k, label, relation in related],
        guardrail=GUARDRAIL,
    )


ENTRIES: dict[str, KnowledgeEntry] = {
    "sc_to_i": _doc(
        "sc_to_i",
        "SC TO-I",
        "The issuer tender offer statement. It is the core SEC filing that announces and updates an issuer self-tender offer.",
        "It anchors the case because the filing identifies the issuer, offer type, amendments, exhibits, and official SEC package.",
        [("amendments", "Amendments mentioned", "high"), ("conditions_of_offer", "Conditions of offer", "high")],
        ["Cover page", "Summary term sheet", "Exhibits", "Amendments", "Signature page"],
        ["SC TO-I", "Schedule TO-I", "issuer tender offer statement", "amendment to schedule TO"],
        [("offer_to_purchase", "Offer to Purchase", "related_document"), ("issuer_tender_offer", "Issuer tender offer playbook", "required_for")],
        badges=["SEC", "Core filing"],
    ),
    "offer_to_purchase": _doc(
        "offer_to_purchase",
        "Offer to Purchase",
        "The main offer document describing tender terms, procedures, conditions, timing, and payment mechanics.",
        "It usually contains the most complete wording for the economic terms Dani needs to review.",
        [
            ("offer_price", "Offer price or price range", "critical"),
            ("expiration_date", "Expiration date", "critical"),
            ("proration", "Proration terms", "high"),
            ("odd_lot_priority", "Odd-lot priority", "medium"),
            ("source_of_funds", "Source of funds", "high"),
            ("withdrawal_rights", "Withdrawal rights", "high"),
            ("conditions_of_offer", "Conditions of offer", "high"),
        ],
        ["Summary Term Sheet", "The Offer", "Price", "Expiration", "Proration", "Withdrawal Rights", "Conditions", "Source and Amount of Funds"],
        ["offer to purchase", "summary term sheet", "expiration date", "withdrawal rights", "source of funds"],
        [("letter_of_transmittal", "Letter of Transmittal", "related_document"), ("sc_to_i", "SC TO-I", "related_document")],
        badges=["SEC exhibit", "Primary source"],
    ),
    "letter_of_transmittal": _doc(
        "letter_of_transmittal",
        "Letter of Transmittal",
        "The procedural document holders use to tender shares or units under the offer.",
        "It helps validate mechanics such as delivery instructions, representations, deadlines, and procedural requirements.",
        [("withdrawal_rights", "Withdrawal rights", "medium"), ("important_dates", "Important dates", "medium")],
        ["Instructions", "Representations", "Signature guarantee", "Delivery of certificates", "Withdrawal procedure"],
        ["letter of transmittal", "instructions", "signature guarantee", "tender shares"],
        [("offer_to_purchase", "Offer to Purchase", "related_document")],
        badges=["SEC exhibit", "Procedure"],
    ),
    "press_release": _doc(
        "press_release",
        "Press Release",
        "A public announcement summarizing the transaction and high-level rationale.",
        "It gives context and timing, but it is usually secondary to SEC exhibits for exact terms.",
        [("offer_price", "Offer price or price range", "medium"), ("important_dates", "Important dates", "medium")],
        ["Headline", "Transaction summary", "Management quote", "Expected timing", "Investor contact"],
        ["press release", "announces tender offer", "commences tender offer"],
        [("offer_to_purchase", "Offer to Purchase", "related_document")],
        badges=["Context", "Secondary source"],
        source_notes="Use for context; confirm legal terms against SEC documents.",
    ),
    "sec_filing_detail": _doc(
        "sec_filing_detail",
        "SEC Filing Detail Page",
        "The SEC accession directory listing filing documents and exhibits.",
        "It is the navigation hub for finding the actual offer documents, amendments, and exhibit files.",
        [("amendments", "Amendments mentioned", "high")],
        ["Document table", "Form type", "Filing date", "Exhibit list", "Accession metadata"],
        ["SEC filing detail", "Archives edgar data", "exhibit", "document format files"],
        [("sc_to_i", "SC TO-I", "explains"), ("key_exhibits", "Key exhibits", "related_document")],
        badges=["SEC", "Source directory"],
    ),
    "key_exhibits": _doc(
        "key_exhibits",
        "Key Exhibits",
        "The exhibit files attached to the filing package, often including the Offer to Purchase and Letter of Transmittal.",
        "Exhibits are where the specific source documents usually live; the cover filing may only point to them.",
        [("offer_price", "Offer price or price range", "critical"), ("withdrawal_rights", "Withdrawal rights", "high"), ("conditions_of_offer", "Conditions of offer", "high")],
        ["EX-99", "Offer document", "Letter of Transmittal", "Notice of Guaranteed Delivery", "Amendments"],
        ["EX-99", "exhibit", "offer to purchase", "letter of transmittal"],
        [("sec_filing_detail", "SEC Filing Detail Page", "required_for")],
        badges=["SEC exhibits", "Document package"],
    ),
    "offer_price": _term(
        "offer_price",
        "Offer Price",
        "The cash or other consideration offered per share, unit, or security.",
        "It is central to economics and comparison against market price, but it is not an investment conclusion.",
        ["Summary Term Sheet", "Price", "Terms of the Offer"],
        ["offer price", "purchase price", "per share", "per unit"],
        [("offer_to_purchase", "Offer to Purchase", "related_document")],
        importance="critical",
    ),
    "expiration_date": _term(
        "expiration_date",
        "Expiration Date",
        "The deadline by which holders must tender unless the offer is extended.",
        "Timing affects manual workflow, amendment checks, and whether later filings supersede the original terms.",
        ["Summary Term Sheet", "Expiration", "Extension of the Offer"],
        ["expiration date", "expires", "midnight", "extended"],
        [("amendments", "Amendments", "related_term")],
        importance="critical",
    ),
    "withdrawal_rights": _term(
        "withdrawal_rights",
        "Withdrawal Rights",
        "Rules describing when and how tendered securities can be withdrawn.",
        "Withdrawal mechanics affect holder optionality and procedural risk.",
        ["Withdrawal Rights", "Procedures for Withdrawal", "Summary Term Sheet"],
        ["withdrawal rights", "may withdraw", "validly withdraw"],
        [("letter_of_transmittal", "Letter of Transmittal", "related_document")],
    ),
    "proration": _term(
        "proration",
        "Proration",
        "The allocation mechanism used when more securities are tendered than the issuer agrees to buy.",
        "Proration can materially change how much of a holder's position is accepted.",
        ["Proration", "Acceptance for Payment", "Priority of Purchases"],
        ["proration", "prorated", "oversubscribed", "accepted for payment"],
        [("odd_lot_priority", "Odd-lot Priority", "related_term")],
    ),
    "odd_lot_priority": _term(
        "odd_lot_priority",
        "Odd-Lot Priority",
        "A priority rule that may accept small holder tenders before applying proration.",
        "It can change outcomes for small positions and should not be assumed unless explicitly stated.",
        ["Odd Lots", "Priority", "Proration"],
        ["odd-lot", "odd lot", "less than 100 shares"],
        [("proration", "Proration", "related_term")],
        importance="medium",
    ),
    "source_of_funds": _term(
        "source_of_funds",
        "Source of Funds",
        "Disclosure describing how the issuer expects to fund purchases and related costs.",
        "It helps Dani understand financing mechanics and whether conditions or borrowings matter.",
        ["Source and Amount of Funds", "Fees and Expenses", "Financing"],
        ["source of funds", "cash on hand", "borrowings", "financing"],
        [("offer_to_purchase", "Offer to Purchase", "related_document")],
    ),
    "conditions_of_offer": _term(
        "conditions_of_offer",
        "Conditions of Offer",
        "Conditions that must be satisfied or waived before the issuer completes the offer.",
        "Conditions frame completion risk and should be read with amendments and withdrawal rights.",
        ["Conditions", "Certain Conditions of the Offer", "Termination"],
        ["conditions to the offer", "subject to", "waive", "terminate"],
        [("amendments", "Amendments", "related_term")],
    ),
    "amendments": _term(
        "amendments",
        "Amendments",
        "Later filings or supplements that update offer terms, dates, exhibits, or disclosures.",
        "Amendments can supersede earlier information, so the latest applicable filing matters.",
        ["Amendment", "Supplement", "Schedule TO-I/A", "Exhibit updates"],
        ["amendment", "amended", "supplement", "SC TO-I/A"],
        [("sc_to_i", "SC TO-I", "related_document"), ("sec_filing_detail", "SEC Filing Detail Page", "required_for")],
    ),
    "issuer_tender_offer": KnowledgeEntry(
        knowledge_key="issuer_tender_offer",
        title="Issuer Tender Offer Playbook",
        type="playbook",
        summary="A workflow for reviewing issuer self-tender situations using SEC filing metadata, offer documents, exhibits, and manually accepted evidence.",
        badges=["Playbook", "Tender offer", "Manual review"],
        applies_to=_applies(),
        why_it_matters="It organizes the documents and terms Dani needs before deciding whether deeper manual research is warranted.",
        where_it_usually_appears=KnowledgeSourceLocation(
            primary_sources=["SC TO-I", "Offer to Purchase", "Letter of Transmittal", "SEC exhibit directory"],
            secondary_sources=["Press release", "Company IR page"],
            source_notes="The playbook is guidance only; every source still needs manual review.",
        ),
        typical_sections=["Find SEC filing", "Inspect exhibits", "Map required documents", "Draft terms", "Accept/reject fields manually"],
        search_terms=["SC TO-I", "issuer tender offer", "offer to purchase", "letter of transmittal", "proration"],
        helps_complete_fields=[
            KnowledgeFieldHelp(field_key="offer_price", label="Offer price", importance="critical"),
            KnowledgeFieldHelp(field_key="expiration_date", label="Expiration date", importance="critical"),
            KnowledgeFieldHelp(field_key="proration", label="Proration", importance="high"),
            KnowledgeFieldHelp(field_key="source_of_funds", label="Source of funds", importance="high"),
        ],
        course_references=_course("Issuer tender offer workflow and document review sequence."),
        course_examples=_example(
            "Manual issuer tender workflow",
            "Start with the SEC detail page, identify exhibits, map candidate sources, then accept or reject extracted draft fields only after review.",
            "workflow",
        ),
        common_mistakes=[
            "Assuming the cover filing contains all offer terms.",
            "Skipping exhibits or amendments.",
            "Treating candidate links or extracted fields as verified automatically.",
        ],
        manual_verification_checklist=[
            "Confirm the issuer, form type, accession, and filing date.",
            "Open the exhibit directory and identify the primary offer documents.",
            "Map each document to a required resource/checklist item.",
            "Review extracted draft fields individually before accepting them.",
        ],
        related_entries=[
            RelatedKnowledgeEntry(knowledge_key="sc_to_i", label="SC TO-I", relation="related_document"),
            RelatedKnowledgeEntry(knowledge_key="offer_to_purchase", label="Offer to Purchase", relation="related_document"),
            RelatedKnowledgeEntry(knowledge_key="proration", label="Proration", relation="related_term"),
        ],
        guardrail=GUARDRAIL,
    ),
}


FIELD_ALIASES = {
    "proration_terms": "proration",
    "key_conditions": "conditions_of_offer",
    "conditions": "conditions_of_offer",
    "important_dates": "expiration_date",
}

PLAYBOOK_ALIASES = {
    "tender_offer": "issuer_tender_offer",
    "issuer_tender_offer.md": "issuer_tender_offer",
    "tender_offer.md": "issuer_tender_offer",
}


def get_knowledge_entry(knowledge_key: str) -> KnowledgeEntry | None:
    return ENTRIES.get(knowledge_key)


def list_knowledge_entries(type: str | None = None, situation_type: str | None = None) -> list[KnowledgeEntry]:
    rows = list(ENTRIES.values())
    if type:
        rows = [entry for entry in rows if entry.type == type]
    if situation_type:
        rows = [entry for entry in rows if situation_type in entry.applies_to.situation_types]
    return sorted(rows, key=lambda entry: (entry.type, entry.title))


def resolve_knowledge_key_for_document(document_key: str) -> str | None:
    return document_key if document_key in ENTRIES and ENTRIES[document_key].type == "document" else None


def resolve_knowledge_key_for_field(field_key: str) -> str | None:
    key = FIELD_ALIASES.get(field_key, field_key)
    return key if key in ENTRIES and ENTRIES[key].type in {"term", "field"} else None


def resolve_knowledge_key_for_playbook(playbook: str) -> str | None:
    normalized = playbook.strip().lower()
    key = PLAYBOOK_ALIASES.get(normalized, normalized)
    return key if key in ENTRIES and ENTRIES[key].type == "playbook" else None
