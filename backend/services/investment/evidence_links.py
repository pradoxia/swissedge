from __future__ import annotations

import uuid
from copy import deepcopy
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel

from backend.models.investment import SpecialSituation
from backend.models.investment_research import ResearchCase
from backend.services.investment.methodology_workspace import WORKSPACE_KEY


GUARDRAILS = [
    "Source links are metadata-only.",
    "No document body has been fetched.",
    "Candidate source does not mean verified.",
    "Evidence found does not mean verified.",
    "Research traceability does not mean evaluation.",
    "No investment recommendation is generated.",
]


class EvidenceLink(BaseModel):
    id: str
    label: str
    url: str | None = None
    source_type: str
    origin: str
    filing_type: str | None = None
    accession_number: str | None = None
    cik: str | None = None
    company_name: str | None = None
    filing_date: str | None = None
    status: str = "metadata_only"
    linked_required_resource_ids: list[str] = []
    linked_checklist_item_ids: list[str] = []
    metadata_only: bool = True
    verified: bool = False
    notes: str | None = None


class EvidenceLinksSummary(BaseModel):
    total_links: int
    sec_links: int
    manual_links: int
    research_source_links: int
    research_document_links: int
    metadata_only_links: int
    missing_link_items: list[str]


class SituationEvidenceLinksPackage(BaseModel):
    situation_id: str
    company_name: str
    ticker: str | None
    sec_detection: dict
    links: list[EvidenceLink]
    required_resource_links: list[dict]
    checklist_links: list[dict]
    search_suggestions: list[dict]
    guardrails: list[str]


class ResearchCaseEvidenceLinksPackage(BaseModel):
    research_case_id: str
    case_title: str | None
    origin: dict
    links: list[EvidenceLink]
    source_links: list[EvidenceLink]
    document_links: list[EvidenceLink]
    snapshot_links: list[EvidenceLink]
    guardrails: list[str]


def _workspace_from_situation(situation: SpecialSituation) -> dict:
    evaluation = situation.evaluation if isinstance(situation.evaluation, dict) else {}
    workspace = evaluation.get(WORKSPACE_KEY)
    return workspace if isinstance(workspace, dict) else {}


def _sec_detection_from_situation(situation: SpecialSituation) -> dict:
    evaluation = situation.evaluation if isinstance(situation.evaluation, dict) else {}
    sec_detection = evaluation.get("sec_detection")
    return sec_detection if isinstance(sec_detection, dict) else {}


def _workspace_snapshot_from_research_case(rc: ResearchCase) -> dict:
    brief = rc.brief if isinstance(rc.brief, dict) else {}
    snapshot = brief.get("methodology_workspace_snapshot")
    return snapshot if isinstance(snapshot, dict) else {}


def _detection_summary_from_research_case(rc: ResearchCase) -> dict:
    brief = rc.brief if isinstance(rc.brief, dict) else {}
    detection = brief.get("detection_summary")
    return detection if isinstance(detection, dict) else {}


def _case_title(rc: ResearchCase) -> str | None:
    brief = rc.brief if isinstance(rc.brief, dict) else {}
    title = brief.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    detection = _detection_summary_from_research_case(rc)
    company = detection.get("company_name")
    filing = detection.get("filing_type")
    parts = [str(value).strip() for value in (company, filing) if isinstance(value, str) and value.strip()]
    return " - ".join(parts) if parts else None


def _source_type(url: str | None, fallback: str = "unknown") -> str:
    if not url:
        return fallback
    host = urlparse(url).netloc.lower()
    if "sec.gov" in host:
        return "sec_filing"
    return fallback


def _stable_id(*parts: Any) -> str:
    raw = "|".join(str(part or "") for part in parts)
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"swissedge-evidence-link:{raw}"))


def _link(
    *,
    label: str,
    url: str | None,
    source_type: str,
    origin: str,
    status: str = "metadata_only",
    filing_type: str | None = None,
    accession_number: str | None = None,
    cik: str | None = None,
    company_name: str | None = None,
    filing_date: str | None = None,
    linked_required_resource_ids: list[str] | None = None,
    linked_checklist_item_ids: list[str] | None = None,
    notes: str | None = None,
) -> EvidenceLink:
    return EvidenceLink(
        id=_stable_id(origin, source_type, url, label, status),
        label=label,
        url=url,
        source_type=source_type,
        origin=origin,
        filing_type=filing_type,
        accession_number=accession_number,
        cik=cik,
        company_name=company_name,
        filing_date=filing_date,
        status=status or "metadata_only",
        linked_required_resource_ids=linked_required_resource_ids or [],
        linked_checklist_item_ids=linked_checklist_item_ids or [],
        notes=notes,
    )


def _merge_links(links: list[EvidenceLink]) -> list[EvidenceLink]:
    merged: dict[tuple[str | None, str, str], EvidenceLink] = {}
    for link in links:
        key = (link.url, link.origin, link.source_type)
        existing = merged.get(key)
        if existing is None:
            merged[key] = link
            continue
        existing.linked_required_resource_ids = sorted(set(existing.linked_required_resource_ids + link.linked_required_resource_ids))
        existing.linked_checklist_item_ids = sorted(set(existing.linked_checklist_item_ids + link.linked_checklist_item_ids))
        if existing.status == "metadata_only" and link.status != "metadata_only":
            existing.status = link.status
        if not existing.notes and link.notes:
            existing.notes = link.notes
    return list(merged.values())


def _candidate_links(candidates: list, *, company_name: str | None = None, detection: dict | None = None, origin: str = "resource_candidate") -> list[EvidenceLink]:
    detection = detection or {}
    links: list[EvidenceLink] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        url = candidate.get("url")
        links.append(_link(
            label=str(candidate.get("title") or candidate.get("source_domain") or "Resource candidate"),
            url=str(url) if isinstance(url, str) and url else None,
            source_type=str(candidate.get("source_type") or _source_type(url, "manual_resource")),
            origin=origin,
            status=str(candidate.get("status") or "candidate_found"),
            filing_type=detection.get("detected_form_type") or detection.get("filing_type"),
            accession_number=detection.get("accession_number"),
            cik=detection.get("cik"),
            company_name=company_name or detection.get("company_name"),
            filing_date=detection.get("filing_date"),
            linked_required_resource_ids=[str(item) for item in candidate.get("related_resource_ids", [])],
            linked_checklist_item_ids=[str(item) for item in candidate.get("related_check_ids", [])],
            notes=candidate.get("notes") if isinstance(candidate.get("notes"), str) else None,
        ))
    return links


def _required_resource_links(workspace: dict, links: list[EvidenceLink]) -> list[dict]:
    resources = workspace.get("required_resources") if isinstance(workspace.get("required_resources"), list) else []
    rows = []
    for resource in resources:
        if not isinstance(resource, dict):
            continue
        resource_id = resource.get("resource_id")
        support = [link.model_dump() for link in links if resource_id and resource_id in link.linked_required_resource_ids]
        rows.append({
            "resource_id": resource_id,
            "title": resource.get("title"),
            "status": resource.get("status", "missing"),
            "links": support,
        })
    return rows


def _checklist_links(workspace: dict, links: list[EvidenceLink]) -> list[dict]:
    checklist = workspace.get("checklist") if isinstance(workspace.get("checklist"), list) else []
    rows = []
    for item in checklist:
        if not isinstance(item, dict):
            continue
        check_id = item.get("check_id")
        support = [link.model_dump() for link in links if check_id and check_id in link.linked_checklist_item_ids]
        rows.append({
            "check_id": check_id,
            "title": item.get("title"),
            "status": item.get("status", "not_started"),
            "links": support,
        })
    return rows


def build_situation_evidence_links(situation: SpecialSituation) -> SituationEvidenceLinksPackage:
    workspace = _workspace_from_situation(situation)
    sec_detection = _sec_detection_from_situation(situation)
    filing_url = sec_detection.get("filing_url") or situation.filing_url
    filing_type = sec_detection.get("detected_form_type") or situation.filing_type
    links: list[EvidenceLink] = []

    if filing_url:
        links.append(_link(
            label=f"{filing_type or 'SEC'} filing",
            url=str(filing_url),
            source_type="sec_filing",
            origin="sec_detection",
            filing_type=filing_type,
            accession_number=sec_detection.get("accession_number"),
            cik=sec_detection.get("cik"),
            company_name=situation.company_name,
            filing_date=sec_detection.get("filing_date"),
            status="metadata_only",
            notes="Original SEC source link that created the detection.",
        ))
    elif sec_detection.get("cik") or sec_detection.get("accession_number"):
        links.append(_link(
            label="SEC detection metadata",
            url=None,
            source_type="sec_company",
            origin="sec_detection",
            filing_type=filing_type,
            accession_number=sec_detection.get("accession_number"),
            cik=sec_detection.get("cik"),
            company_name=situation.company_name,
            filing_date=sec_detection.get("filing_date"),
            status="metadata_only",
            notes="SEC metadata exists, but no stored filing URL is available.",
        ))

    source_urls = situation.source_urls if isinstance(situation.source_urls, list) else []
    for url in source_urls:
        if isinstance(url, str) and url and url != filing_url:
            links.append(_link(
                label="Source URL",
                url=url,
                source_type=_source_type(url, "unknown"),
                origin="sec_detection",
                filing_type=filing_type,
                accession_number=sec_detection.get("accession_number"),
                cik=sec_detection.get("cik"),
                company_name=situation.company_name,
                filing_date=sec_detection.get("filing_date"),
            ))

    candidates = workspace.get("resource_candidates") if isinstance(workspace.get("resource_candidates"), list) else []
    links.extend(_candidate_links(candidates, company_name=situation.company_name, detection=sec_detection))
    merged_links = _merge_links(links)

    suggestions = workspace.get("search_suggestions") if isinstance(workspace.get("search_suggestions"), list) else []
    return SituationEvidenceLinksPackage(
        situation_id=str(situation.id),
        company_name=situation.company_name,
        ticker=situation.ticker,
        sec_detection=deepcopy(sec_detection),
        links=merged_links,
        required_resource_links=_required_resource_links(workspace, merged_links),
        checklist_links=_checklist_links(workspace, merged_links),
        search_suggestions=deepcopy(suggestions),
        guardrails=GUARDRAILS,
    )


def build_research_case_evidence_links(rc: ResearchCase) -> ResearchCaseEvidenceLinksPackage:
    workspace = _workspace_snapshot_from_research_case(rc)
    detection = _detection_summary_from_research_case(rc)
    links: list[EvidenceLink] = []
    filing_url = detection.get("filing_url")
    filing_type = detection.get("filing_type")

    if isinstance(filing_url, str) and filing_url:
        links.append(_link(
            label=f"{filing_type or 'SEC'} filing",
            url=filing_url,
            source_type="sec_filing",
            origin="brief_snapshot",
            filing_type=filing_type,
            accession_number=detection.get("accession_number"),
            company_name=detection.get("company_name"),
            filing_date=detection.get("filing_date"),
            notes="Original SEC link copied into the ResearchCase promotion snapshot.",
        ))

    candidates = workspace.get("resource_candidates") if isinstance(workspace.get("resource_candidates"), list) else []
    links.extend(_candidate_links(candidates, company_name=detection.get("company_name"), detection=detection, origin="brief_snapshot"))

    source_links: list[EvidenceLink] = []
    for source in getattr(rc, "sources", []) or []:
        source_links.append(_link(
            label=source.source_name,
            url=source.source_url,
            source_type=_source_type(source.source_url, "research_source"),
            origin="research_case_source",
            status="metadata_only",
            notes=source.notes,
        ))

    document_links: list[EvidenceLink] = []
    for document in getattr(rc, "documents", []) or []:
        document_links.append(_link(
            label=document.title or document.doc_type or "Research document",
            url=document.url,
            source_type=_source_type(document.url, "research_document"),
            origin="research_case_document",
            status="metadata_only",
            notes=document.summary,
        ))

    snapshot_links = _merge_links(links)
    all_links = _merge_links(snapshot_links + source_links + document_links)
    return ResearchCaseEvidenceLinksPackage(
        research_case_id=str(rc.id),
        case_title=_case_title(rc),
        origin={
            "intake_method": rc.intake_method,
            "situation_id": str(rc.situation_id) if rc.situation_id else None,
            "source": "special_situation_promotion" if rc.intake_method == "special_situation_promotion" else (rc.source_origin_name or "unknown"),
        },
        links=all_links,
        source_links=source_links,
        document_links=document_links,
        snapshot_links=snapshot_links,
        guardrails=GUARDRAILS,
    )


def summarize_evidence_links(links: list[EvidenceLink], *, missing_link_items: list[str] | None = None) -> EvidenceLinksSummary:
    return EvidenceLinksSummary(
        total_links=len(links),
        sec_links=len([link for link in links if link.source_type in {"sec_filing", "sec_company"}]),
        manual_links=len([link for link in links if link.origin in {"resource_candidate", "required_resource", "checklist_item"}]),
        research_source_links=len([link for link in links if link.origin == "research_case_source"]),
        research_document_links=len([link for link in links if link.origin == "research_case_document"]),
        metadata_only_links=len([link for link in links if link.metadata_only]),
        missing_link_items=missing_link_items or [],
    )
