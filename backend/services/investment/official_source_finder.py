from __future__ import annotations

from copy import deepcopy
from typing import Any, Literal

from pydantic import BaseModel

from backend.models.investment import SpecialSituation
from backend.models.investment_research import ResearchCase
from backend.services.investment.evidence_links import (
    ResearchCaseEvidenceLinksPackage,
    SituationEvidenceLinksPackage,
)
from backend.services.investment.methodology_workspace import WORKSPACE_KEY


CaseType = Literal["special_situation", "research_case"]


class SourceContext(BaseModel):
    source: str = "SEC EDGAR"
    company_name: str | None = None
    ticker: str | None = None
    cik: str | None = None
    accession_number: str | None = None
    filing_type: str | None = None
    filing_date: str | None = None
    situation_type: str | None = None
    selected_playbook: str | None = None
    stored_filing_url: str | None = None


class OfficialSourceLink(BaseModel):
    label: str
    url: str | None = None
    link_type: str
    metadata_only: bool = True
    verified: bool = False
    supports: list[str] = []
    notes: str | None = None


class ManualLocatorStep(BaseModel):
    step: int
    title: str
    description: str
    link_url: str | None = None
    supports_required_resources: list[str] = []
    supports_checklist_items: list[str] = []


class MissingDocumentTarget(BaseModel):
    title: str
    required_resource_id: str | None = None
    checklist_item_id: str | None = None
    priority: Literal["high", "medium", "low"] = "medium"
    why_needed: str
    where_to_search: list[str]
    manual_queries: list[str] = []


class CopyableOfficialSourceQuery(BaseModel):
    query: str
    purpose: str
    where_to_use: str
    supports_required_resources: list[str] = []
    supports_checklist_items: list[str] = []
    not_executed_by_swissedge: bool = True


class OfficialSourceCoverage(BaseModel):
    stored_official_links_count: int
    missing_required_documents_count: int
    manual_queries_count: int
    candidate_sources_count: int
    evidence_found_count: int


class OfficialSourceFinderPackage(BaseModel):
    case_id: str
    case_type: CaseType
    source_context: SourceContext
    official_links: list[OfficialSourceLink]
    manual_locator_steps: list[ManualLocatorStep]
    missing_document_targets: list[MissingDocumentTarget]
    copyable_queries: list[CopyableOfficialSourceQuery]
    coverage: OfficialSourceCoverage
    guardrails: list[str]


GUARDRAILS = [
    "This is a manual source-finding guide.",
    "No external search was executed.",
    "No SEC document body was fetched.",
    "No PDF was downloaded.",
    "Links are metadata-only unless manually reviewed.",
    "Candidate sources are not verified evidence.",
    "Evidence found still requires human verification.",
]


MISSING_STATUSES = {"missing", "needs_evidence", "not_started", "open"}
EVIDENCE_STATUSES = {"evidence_found"}
OFFICIAL_SOURCE_TYPES = {"sec_filing", "sec_detection", "press_release", "company_ir", "ir_page"}


def _clean_dict(value: Any) -> dict:
    return deepcopy(value) if isinstance(value, dict) else {}


def _clean_list(value: Any) -> list[dict]:
    return [deepcopy(item) for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _evaluation_from_situation(situation: SpecialSituation) -> dict:
    return _clean_dict(situation.evaluation)


def _workspace_from_situation(situation: SpecialSituation) -> dict:
    return _clean_dict(_evaluation_from_situation(situation).get(WORKSPACE_KEY))


def _sec_detection_from_situation(situation: SpecialSituation) -> dict:
    return _clean_dict(_evaluation_from_situation(situation).get("sec_detection"))


def _brief_from_case(rc: ResearchCase) -> dict:
    return _clean_dict(rc.brief)


def _workspace_from_case(rc: ResearchCase) -> dict:
    return _clean_dict(_brief_from_case(rc).get("methodology_workspace_snapshot"))


def _detection_from_case(rc: ResearchCase, source_situation: SpecialSituation | None = None) -> dict:
    detection = _clean_dict(_brief_from_case(rc).get("detection_summary"))
    if detection:
        return detection
    if source_situation is None:
        return {}
    sec = _sec_detection_from_situation(source_situation)
    return {
        "company_name": source_situation.company_name,
        "ticker": source_situation.ticker,
        "cik": sec.get("cik"),
        "accession_number": sec.get("accession_number"),
        "filing_type": sec.get("detected_form_type") or source_situation.filing_type,
        "filing_date": sec.get("filing_date"),
        "situation_type": source_situation.situation_type,
        "selected_playbook": sec.get("selected_playbook"),
        "filing_url": sec.get("filing_url") or source_situation.filing_url,
    }


def _text(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _resource_id(item: dict) -> str | None:
    return _text(item.get("resource_id") or item.get("id"))


def _check_id(item: dict) -> str | None:
    return _text(item.get("check_id") or item.get("id"))


def _title(item: dict, fallback: str) -> str:
    return _text(item.get("title") or item.get("label") or item.get("name")) or fallback


def _status(item: dict) -> str:
    return str(item.get("status") or "missing")


def _required_resources(workspace: dict) -> list[dict]:
    return _clean_list(workspace.get("required_resources"))


def _checklist(workspace: dict) -> list[dict]:
    return _clean_list(workspace.get("checklist"))


def _resource_candidates(workspace: dict) -> list[dict]:
    return _clean_list(workspace.get("resource_candidates"))


def _search_suggestions(workspace: dict) -> list[dict]:
    return _clean_list(workspace.get("search_suggestions"))


def _source_context(
    *,
    case_type: CaseType,
    situation: SpecialSituation | None = None,
    rc: ResearchCase | None = None,
    source_situation: SpecialSituation | None = None,
) -> SourceContext:
    if case_type == "special_situation" and situation is not None:
        sec = _sec_detection_from_situation(situation)
        return SourceContext(
            company_name=situation.company_name,
            ticker=situation.ticker,
            cik=_text(sec.get("cik")),
            accession_number=_text(sec.get("accession_number")),
            filing_type=_text(sec.get("detected_form_type") or situation.filing_type),
            filing_date=_text(sec.get("filing_date")),
            situation_type=situation.situation_type,
            selected_playbook=_text(sec.get("selected_playbook")),
            stored_filing_url=_text(sec.get("filing_url") or situation.filing_url),
        )

    detection = _detection_from_case(rc, source_situation) if rc is not None else {}
    return SourceContext(
        company_name=_text(detection.get("company_name")),
        ticker=_text(detection.get("ticker")),
        cik=_text(detection.get("cik")),
        accession_number=_text(detection.get("accession_number")),
        filing_type=_text(detection.get("filing_type") or detection.get("detected_form_type")),
        filing_date=_text(detection.get("filing_date")),
        situation_type=_text(detection.get("situation_type")),
        selected_playbook=_text(detection.get("selected_playbook")),
        stored_filing_url=_text(detection.get("filing_url")),
    )


def _supports_from_candidate(candidate: dict) -> list[str]:
    values = candidate.get("related_resource_ids")
    return [str(item) for item in values if item] if isinstance(values, list) else []


def _official_links(
    *,
    context: SourceContext,
    candidates: list[dict],
    evidence_links: SituationEvidenceLinksPackage | ResearchCaseEvidenceLinksPackage | None,
    rc: ResearchCase | None = None,
) -> list[OfficialSourceLink]:
    links: list[OfficialSourceLink] = []
    if context.stored_filing_url:
        links.append(OfficialSourceLink(
            label="Stored SEC filing URL",
            url=context.stored_filing_url,
            link_type="stored_sec_filing",
            supports=[],
            notes="Stored metadata link only. Open manually to confirm the filing.",
        ))

    for candidate in candidates:
        url = _text(candidate.get("url"))
        source_type = _text(candidate.get("source_type")) or "resource_candidate"
        if not url or source_type not in OFFICIAL_SOURCE_TYPES:
            continue
        if any(link.url == url for link in links):
            continue
        links.append(OfficialSourceLink(
            label=_title(candidate, "Official source candidate"),
            url=url,
            link_type=source_type,
            supports=_supports_from_candidate(candidate),
            notes=f"Candidate status: {_status(candidate)}. Not verified by SwissEdge.",
        ))

    if evidence_links is not None:
        for link in getattr(evidence_links, "links", []):
            if not link.url or any(existing.url == link.url for existing in links):
                continue
            if link.source_type not in OFFICIAL_SOURCE_TYPES:
                continue
            links.append(OfficialSourceLink(
                label=link.label,
                url=link.url,
                link_type=link.source_type,
                supports=list(link.linked_required_resource_ids),
                notes=f"Traceability status: {link.status}. Not automatically verified.",
            ))

    if rc is not None:
        for source in getattr(rc, "sources", []) or []:
            url = _text(getattr(source, "source_url", None))
            if url and "sec.gov" in url.lower() and not any(existing.url == url for existing in links):
                links.append(OfficialSourceLink(
                    label=getattr(source, "source_name", None) or "ResearchCase SEC source",
                    url=url,
                    link_type="research_case_sec_source",
                    notes="ResearchCase source link. Manual review still required.",
                ))
    return links[:12]


def _base_query(context: SourceContext, title: str | None = None) -> str:
    parts = []
    if context.company_name:
        parts.append(f'"{context.company_name}"')
    if title:
        parts.append(f'"{title}"')
    if context.filing_type:
        parts.append(f'"{context.filing_type}"')
    if context.accession_number:
        parts.append(f'"{context.accession_number}"')
    return " ".join(parts) or "\"SEC filing\" \"official source\""


def _where_to_search(title: str) -> list[str]:
    lowered = title.lower()
    if "press" in lowered:
        return ["Company IR", "SEC filing archive", "Google"]
    if "transmittal" in lowered or "offer" in lowered or "purchase" in lowered:
        return ["SEC filing archive", "SC TO exhibits", "Company IR", "Google"]
    return ["SEC EDGAR", "SEC company submissions", "Company IR", "Google"]


def _missing_targets(context: SourceContext, workspace: dict) -> list[MissingDocumentTarget]:
    targets: list[MissingDocumentTarget] = []
    for resource in _required_resources(workspace):
        if _status(resource) not in MISSING_STATUSES:
            continue
        title = _title(resource, "Missing required document")
        query = _base_query(context, title)
        targets.append(MissingDocumentTarget(
            title=title,
            required_resource_id=_resource_id(resource),
            priority="high" if str(resource.get("required_or_optional", "required")) == "required" else "medium",
            why_needed=f"Required resource status is {_status(resource)}.",
            where_to_search=_where_to_search(title),
            manual_queries=[query],
        ))

    for item in _checklist(workspace):
        if _status(item) not in MISSING_STATUSES:
            continue
        title = _title(item, "Missing checklist evidence")
        query = _base_query(context, title)
        targets.append(MissingDocumentTarget(
            title=title,
            checklist_item_id=_check_id(item),
            priority="medium",
            why_needed=f"Checklist item status is {_status(item)}.",
            where_to_search=_where_to_search(title),
            manual_queries=[query],
        ))
    return targets[:12]


def _copyable_queries(context: SourceContext, workspace: dict, targets: list[MissingDocumentTarget]) -> list[CopyableOfficialSourceQuery]:
    rows: list[CopyableOfficialSourceQuery] = []
    for suggestion in _search_suggestions(workspace):
        query = _text(suggestion.get("query"))
        if not query:
            continue
        rows.append(CopyableOfficialSourceQuery(
            query=query,
            purpose=_text(suggestion.get("purpose")) or _text(suggestion.get("suggestion_type")) or "Stored manual search suggestion.",
            where_to_use="Google / SEC search / company IR",
        ))

    for target in targets:
        for query in target.manual_queries:
            if any(row.query == query for row in rows):
                continue
            rows.append(CopyableOfficialSourceQuery(
                query=query,
                purpose=f"Locate official evidence for: {target.title}.",
                where_to_use=" / ".join(target.where_to_search),
                supports_required_resources=[target.required_resource_id] if target.required_resource_id else [],
                supports_checklist_items=[target.checklist_item_id] if target.checklist_item_id else [],
            ))

    if context.cik and not any("CIK" in row.purpose for row in rows):
        rows.append(CopyableOfficialSourceQuery(
            query=f'{context.cik} "{context.company_name or ""}" "{context.filing_type or ""}"'.strip(),
            purpose="CIK metadata search for SEC company submissions. SwissEdge does not construct or validate an archive URL.",
            where_to_use="SEC EDGAR company submissions search",
        ))
    return rows[:15]


def _manual_steps(context: SourceContext, targets: list[MissingDocumentTarget]) -> list[ManualLocatorStep]:
    steps = [
        ManualLocatorStep(
            step=1,
            title="Review stored SEC metadata",
            description="Confirm company, ticker, CIK, accession number, filing type, filing date, and playbook before using any link.",
        ),
    ]
    if context.stored_filing_url:
        steps.append(ManualLocatorStep(
            step=2,
            title="Open stored SEC filing URL",
            description="Open this stored metadata link manually. Confirm it matches the company and form type before mapping evidence.",
            link_url=context.stored_filing_url,
        ))
    else:
        steps.append(ManualLocatorStep(
            step=2,
            title="Locate SEC filing manually",
            description="Use the stored CIK/accession/form metadata in SEC EDGAR. SwissEdge did not build or validate a filing archive link.",
        ))

    step_no = 3
    for target in targets[:5]:
        steps.append(ManualLocatorStep(
            step=step_no,
            title=f"Search for {target.title}",
            description="Use the copyable query in SEC search, company IR, or Google. If found, add it as metadata and map it to the required resource/checklist item.",
            supports_required_resources=[target.required_resource_id] if target.required_resource_id else [],
            supports_checklist_items=[target.checklist_item_id] if target.checklist_item_id else [],
        ))
        step_no += 1
    return steps


def _coverage(links: list[OfficialSourceLink], workspace: dict, queries: list[CopyableOfficialSourceQuery]) -> OfficialSourceCoverage:
    candidates = _resource_candidates(workspace)
    resources = _required_resources(workspace)
    checklist = _checklist(workspace)
    return OfficialSourceCoverage(
        stored_official_links_count=len([link for link in links if link.url]),
        missing_required_documents_count=len([item for item in resources if _status(item) in MISSING_STATUSES]),
        manual_queries_count=len(queries),
        candidate_sources_count=len([item for item in candidates if _status(item) == "candidate_found"]),
        evidence_found_count=len([item for item in resources + checklist + candidates if _status(item) in EVIDENCE_STATUSES]),
    )


def build_situation_official_source_finder(
    situation: SpecialSituation,
    evidence_links: SituationEvidenceLinksPackage | None = None,
) -> OfficialSourceFinderPackage:
    workspace = _workspace_from_situation(situation)
    context = _source_context(case_type="special_situation", situation=situation)
    targets = _missing_targets(context, workspace)
    queries = _copyable_queries(context, workspace, targets)
    links = _official_links(
        context=context,
        candidates=_resource_candidates(workspace),
        evidence_links=evidence_links,
    )
    return OfficialSourceFinderPackage(
        case_id=str(situation.id),
        case_type="special_situation",
        source_context=context,
        official_links=links,
        manual_locator_steps=_manual_steps(context, targets),
        missing_document_targets=targets,
        copyable_queries=queries,
        coverage=_coverage(links, workspace, queries),
        guardrails=GUARDRAILS,
    )


def build_research_case_official_source_finder(
    rc: ResearchCase,
    *,
    evidence_links: ResearchCaseEvidenceLinksPackage | None = None,
    source_situation: SpecialSituation | None = None,
) -> OfficialSourceFinderPackage:
    workspace = _workspace_from_case(rc)
    context = _source_context(case_type="research_case", rc=rc, source_situation=source_situation)
    targets = _missing_targets(context, workspace)
    queries = _copyable_queries(context, workspace, targets)
    links = _official_links(
        context=context,
        candidates=_resource_candidates(workspace),
        evidence_links=evidence_links,
        rc=rc,
    )
    return OfficialSourceFinderPackage(
        case_id=str(rc.id),
        case_type="research_case",
        source_context=context,
        official_links=links,
        manual_locator_steps=_manual_steps(context, targets),
        missing_document_targets=targets,
        copyable_queries=queries,
        coverage=_coverage(links, workspace, queries),
        guardrails=GUARDRAILS,
    )
