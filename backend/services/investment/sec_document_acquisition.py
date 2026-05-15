from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from typing import Awaitable, Callable
from urllib.parse import urljoin, urlparse

import httpx
from pydantic import BaseModel, Field

from backend.config import get_settings
from backend.models.investment import SpecialSituation
from backend.models.investment_research import ResearchCase, ResearchDocument, ResearchSource
from backend.services.investment.methodology_workspace import WORKSPACE_KEY

SEC_HOSTS = {"www.sec.gov", "sec.gov"}
SEC_ARCHIVE_PREFIX = "https://www.sec.gov/Archives/"
MAX_RESPONSE_CHARS = 250_000
FETCH_TIMEOUT_SECONDS = 8.0
THROTTLE_SECONDS = 0.75


class SecIdentifierPreview(BaseModel):
    filing_url: str | None = None
    cik: str | None = None
    accession_number: str | None = None
    filing_type: str | None = None
    filing_date: str | None = None
    company_name: str | None = None
    ticker: str | None = None


class SecDocumentTarget(BaseModel):
    label: str
    expected_doc_type: str
    reason: str


class SecLocatorStep(BaseModel):
    step: int
    title: str
    description: str
    link_url: str | None = None


class SecCopyableQuery(BaseModel):
    query: str
    purpose: str
    where_to_use: str = "SEC EDGAR search"
    not_executed_by_swissedge: bool = True


class SecAcquiredDocument(BaseModel):
    title: str
    url: str
    doc_type: str
    accession_number: str | None = None
    form_type: str | None = None
    acquisition_status: str = "acquired_metadata"
    human_review_required: bool = True
    verified: bool = False


class SecDocumentAcquisitionPackage(BaseModel):
    case_id: str
    case_type: str
    mode: str = "manual_sec_only"
    available_identifiers: SecIdentifierPreview
    missing_identifiers: list[str] = Field(default_factory=list)
    official_links: list[SecAcquiredDocument] = Field(default_factory=list)
    likely_document_targets: list[SecDocumentTarget] = Field(default_factory=list)
    manual_locator_steps: list[SecLocatorStep] = Field(default_factory=list)
    copyable_queries: list[SecCopyableQuery] = Field(default_factory=list)
    acquired_documents: list[SecAcquiredDocument] = Field(default_factory=list)
    stored_records: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    manual_next_steps: list[str] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)


FetchFn = Callable[[str], Awaitable[str]]


def _text(value) -> str | None:
    if value is None:
        return None
    raw = str(value).strip()
    return raw or None


def _brief(rc: ResearchCase) -> dict:
    return rc.brief if isinstance(rc.brief, dict) else {}


def _workspace_from_situation(situation: SpecialSituation) -> dict:
    evaluation = situation.evaluation if isinstance(situation.evaluation, dict) else {}
    workspace = evaluation.get(WORKSPACE_KEY)
    return workspace if isinstance(workspace, dict) else {}


def _workspace_from_case(rc: ResearchCase) -> dict:
    workspace = _brief(rc).get("methodology_workspace_snapshot")
    return workspace if isinstance(workspace, dict) else {}


def _sec_detection_from_situation(situation: SpecialSituation) -> dict:
    evaluation = situation.evaluation if isinstance(situation.evaluation, dict) else {}
    detection = evaluation.get("sec_detection")
    return detection if isinstance(detection, dict) else {}


def _sec_detection_from_case(rc: ResearchCase, source_situation: SpecialSituation | None = None) -> dict:
    brief = _brief(rc)
    detection = brief.get("detection_summary")
    if isinstance(detection, dict):
        return detection
    if source_situation:
        return _sec_detection_from_situation(source_situation)
    return {}


def _identifiers_for_situation(situation: SpecialSituation) -> SecIdentifierPreview:
    detection = _sec_detection_from_situation(situation)
    return SecIdentifierPreview(
        filing_url=_text(situation.filing_url or detection.get("filing_url") or detection.get("url")),
        cik=_text(detection.get("cik") or detection.get("company_cik")),
        accession_number=_text(detection.get("accession_number") or detection.get("accession_no")),
        filing_type=_text(situation.filing_type or detection.get("filing_type") or detection.get("detected_form_type")),
        filing_date=_text(detection.get("filing_date") or detection.get("date")),
        company_name=_text(situation.company_name or detection.get("company_name") or detection.get("company")),
        ticker=_text(situation.ticker or detection.get("ticker")),
    )


def _identifiers_for_case(rc: ResearchCase, source_situation: SpecialSituation | None = None) -> SecIdentifierPreview:
    detection = _sec_detection_from_case(rc, source_situation)
    return SecIdentifierPreview(
        filing_url=_text(detection.get("filing_url") or detection.get("url")),
        cik=_text(detection.get("cik") or detection.get("company_cik")),
        accession_number=_text(detection.get("accession_number") or detection.get("accession_no")),
        filing_type=_text(detection.get("filing_type") or detection.get("detected_form_type")),
        filing_date=_text(detection.get("filing_date") or detection.get("date")),
        company_name=_text(detection.get("company_name") or detection.get("company") or _brief(rc).get("title")),
        ticker=_text(detection.get("ticker")),
    )


def _missing_identifiers(identifiers: SecIdentifierPreview) -> list[str]:
    required = {
        "filing_url": identifiers.filing_url,
        "cik": identifiers.cik,
        "accession_number": identifiers.accession_number,
        "filing_type": identifiers.filing_type,
    }
    return [key for key, value in required.items() if not value]


def _is_sec_url(url: str | None) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.netloc.lower() in SEC_HOSTS


def _company(identifiers: SecIdentifierPreview) -> str:
    return identifiers.company_name or identifiers.ticker or "company"


def _targets(workspace: dict, identifiers: SecIdentifierPreview) -> list[SecDocumentTarget]:
    targets: list[SecDocumentTarget] = []
    resources = workspace.get("required_resources") if isinstance(workspace.get("required_resources"), list) else []
    for resource in resources:
        if not isinstance(resource, dict):
            continue
        status = _text(resource.get("status")) or "missing"
        if status not in {"missing", "candidate_found", "needs_evidence"}:
            continue
        title = _text(resource.get("title")) or _text(resource.get("resource_id")) or "Required SEC document"
        source_type = _text(resource.get("source_type")) or _text(resource.get("resource_id")) or "official_sec"
        targets.append(SecDocumentTarget(
            label=title,
            expected_doc_type=source_type,
            reason=f"Stored workspace marks this resource as {status}; acquire SEC metadata as a candidate for manual review.",
        ))
    if not targets:
        form = (identifiers.filing_type or "SEC filing").upper()
        targets.append(SecDocumentTarget(
            label=f"{form} primary filing metadata",
            expected_doc_type="official_sec_filing",
            reason="Use the official SEC filing metadata as the starting source candidate.",
        ))
    return targets[:8]


def _queries(identifiers: SecIdentifierPreview, targets: list[SecDocumentTarget]) -> list[SecCopyableQuery]:
    company = _company(identifiers)
    form = identifiers.filing_type or "SEC filing"
    queries = [
        SecCopyableQuery(
            query=" ".join(part for part in [f'"{company}"', f'"{form}"', identifiers.accession_number] if part),
            purpose="Locate the official SEC filing or accession page by company, form, and accession metadata.",
        )
    ]
    for target in targets[:5]:
        queries.append(SecCopyableQuery(
            query=f'"{company}" "{target.label}" "{form}"',
            purpose=f"Find the SEC exhibit or filing item that may support: {target.label}.",
        ))
    return queries


def _locator_steps(identifiers: SecIdentifierPreview) -> list[SecLocatorStep]:
    steps = [
        SecLocatorStep(
            step=1,
            title="Open the stored SEC filing URL",
            description="Use this as the official starting point. Review metadata and document links manually.",
            link_url=identifiers.filing_url if _is_sec_url(identifiers.filing_url) else None,
        ),
        SecLocatorStep(
            step=2,
            title="Open the SEC accession filing detail page",
            description="Use CIK and accession number to locate exhibits, primary filing documents, and accession metadata.",
        ),
        SecLocatorStep(
            step=3,
            title="Map documents manually",
            description="Attach useful SEC document URLs to required resources or checklist items only after manual review.",
        ),
    ]
    return steps


def _guardrails() -> list[str]:
    return [
        "Manual SEC EDGAR acquisition only.",
        "Official SEC documents are stored as candidates or metadata.",
        "Evidence remains unverified until manual review.",
        "No scanner, evaluator, AI, publishing, or automatic promotion is triggered.",
    ]


def build_situation_sec_document_acquisition_preview(situation: SpecialSituation) -> SecDocumentAcquisitionPackage:
    identifiers = _identifiers_for_situation(situation)
    workspace = _workspace_from_situation(situation)
    targets = _targets(workspace, identifiers)
    warnings = []
    if identifiers.filing_url and not _is_sec_url(identifiers.filing_url):
        warnings.append("Stored filing URL is not an official SEC URL; acquisition will not fetch it.")
    return SecDocumentAcquisitionPackage(
        case_id=str(situation.id),
        case_type="special_situation",
        available_identifiers=identifiers,
        missing_identifiers=_missing_identifiers(identifiers),
        official_links=[
            SecAcquiredDocument(
                title="Stored SEC filing URL",
                url=identifiers.filing_url,
                doc_type="stored_sec_filing",
                accession_number=identifiers.accession_number,
                form_type=identifiers.filing_type,
            )
        ] if _is_sec_url(identifiers.filing_url) else [],
        likely_document_targets=targets,
        manual_locator_steps=_locator_steps(identifiers),
        copyable_queries=_queries(identifiers, targets),
        warnings=warnings,
        manual_next_steps=[
            "Run manual acquisition only when stored SEC metadata points to sec.gov.",
            "Review acquired metadata before mapping it to evidence.",
            "Keep candidate sources unverified until Dani confirms the document.",
        ],
        guardrails=_guardrails(),
    )


def build_research_case_sec_document_acquisition_preview(
    rc: ResearchCase,
    *,
    source_situation: SpecialSituation | None = None,
) -> SecDocumentAcquisitionPackage:
    identifiers = _identifiers_for_case(rc, source_situation)
    workspace = _workspace_from_case(rc)
    targets = _targets(workspace, identifiers)
    warnings = []
    if identifiers.filing_url and not _is_sec_url(identifiers.filing_url):
        warnings.append("Stored filing URL is not an official SEC URL; acquisition will not fetch it.")
    return SecDocumentAcquisitionPackage(
        case_id=str(rc.id),
        case_type="research_case",
        available_identifiers=identifiers,
        missing_identifiers=_missing_identifiers(identifiers),
        official_links=[
            SecAcquiredDocument(
                title="Stored SEC filing URL",
                url=identifiers.filing_url,
                doc_type="stored_sec_filing",
                accession_number=identifiers.accession_number,
                form_type=identifiers.filing_type,
            )
        ] if _is_sec_url(identifiers.filing_url) else [],
        likely_document_targets=targets,
        manual_locator_steps=_locator_steps(identifiers),
        copyable_queries=_queries(identifiers, targets),
        warnings=warnings,
        manual_next_steps=[
            "Review acquired SEC metadata against the ResearchCase brief.",
            "Attach only manually reviewed URLs to documents or sources.",
            "Keep evidence unverified until Dani confirms the document.",
        ],
        guardrails=_guardrails(),
    )


async def _default_fetch_sec_url(url: str) -> str:
    if not _is_sec_url(url):
        raise ValueError("SEC document acquisition only allows official sec.gov URLs.")
    settings = get_settings()
    headers = {
        "User-Agent": settings.sec_user_agent or "SwissEdge/1.0 (manual-sec-document-acquisition)",
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.8,*/*;q=0.5",
    }
    await asyncio.sleep(THROTTLE_SECONDS)
    async with httpx.AsyncClient(timeout=FETCH_TIMEOUT_SECONDS, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.text[:MAX_RESPONSE_CHARS]


def _extract_sec_documents(html: str, base_url: str, identifiers: SecIdentifierPreview) -> list[SecAcquiredDocument]:
    documents: list[SecAcquiredDocument] = []
    seen: set[str] = set()
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)
    for href in hrefs:
        url = urljoin(base_url, href)
        if not _is_sec_url(url):
            continue
        path = urlparse(url).path.lower()
        if "/archives/" not in path:
            continue
        if url in seen:
            continue
        seen.add(url)
        filename = path.rsplit("/", 1)[-1] or "SEC document"
        if not re.search(r"\.(htm|html|txt|xml|pdf)$", filename):
            continue
        documents.append(SecAcquiredDocument(
            title=filename,
            url=url,
            doc_type=_doc_type_from_filename(filename),
            accession_number=identifiers.accession_number,
            form_type=identifiers.filing_type,
        ))
        if len(documents) >= 12:
            break
    return documents


def _doc_type_from_filename(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return "official_sec_pdf_metadata"
    if "exhibit" in lower or re.search(r"ex[-_]?\d+", lower):
        return "official_sec_exhibit"
    if lower.endswith(".xml"):
        return "official_sec_xml_metadata"
    return "official_sec_filing_document"


async def acquire_sec_documents_from_preview(
    preview: SecDocumentAcquisitionPackage,
    *,
    fetcher: FetchFn | None = None,
) -> SecDocumentAcquisitionPackage:
    identifiers = preview.available_identifiers
    if not _is_sec_url(identifiers.filing_url):
        preview.warnings.append("Acquisition skipped: no official sec.gov filing URL is available.")
        return preview

    fetch = fetcher or _default_fetch_sec_url
    try:
        html = await fetch(identifiers.filing_url)
    except Exception as exc:
        preview.warnings.append(f"SEC acquisition failed safely: {exc}")
        return preview

    docs = _extract_sec_documents(html, identifiers.filing_url, identifiers)
    if not docs and _is_sec_url(identifiers.filing_url):
        docs = [
            SecAcquiredDocument(
                title="Stored SEC filing URL",
                url=identifiers.filing_url,
                doc_type="official_sec_filing_metadata",
                accession_number=identifiers.accession_number,
                form_type=identifiers.filing_type,
            )
        ]
    preview.acquired_documents = docs
    preview.official_links = _merge_documents(preview.official_links, docs)
    preview.manual_next_steps.insert(0, "Review each acquired SEC candidate before linking it to evidence.")
    return preview


def _merge_documents(existing: list[SecAcquiredDocument], new_docs: list[SecAcquiredDocument]) -> list[SecAcquiredDocument]:
    by_url = {doc.url: doc for doc in existing}
    for doc in new_docs:
        by_url.setdefault(doc.url, doc)
    return list(by_url.values())


def _candidate_id(url: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", url.lower()).strip("-")
    return f"sec-doc-{slug[-48:]}" if slug else "sec-doc-candidate"


def apply_situation_sec_acquisition_metadata(
    situation: SpecialSituation,
    package: SecDocumentAcquisitionPackage,
) -> list[dict]:
    evaluation = dict(situation.evaluation or {})
    workspace = dict(evaluation.get(WORKSPACE_KEY) or {})
    candidates = list(workspace.get("resource_candidates") or [])
    existing_urls = {str(item.get("url")) for item in candidates if isinstance(item, dict)}
    stored: list[dict] = []
    for doc in package.acquired_documents:
        if doc.url in existing_urls:
            continue
        record = {
            "resource_candidate_id": _candidate_id(doc.url),
            "title": doc.title,
            "url": doc.url,
            "source_type": "official_sec",
            "source_domain": "sec.gov",
            "status": "candidate_found",
            "confidence": "official_metadata",
            "related_resource_ids": [],
            "related_check_ids": [],
            "discovered_by": "manual_sec_document_acquisition",
            "discovered_at": datetime.now(timezone.utc).isoformat(),
            "notes": "Official SEC metadata candidate. Human review required; not verified evidence.",
            "human_review_required": True,
            "verified": False,
            "acquisition_status": doc.acquisition_status,
            "accession_number": doc.accession_number,
            "form_type": doc.form_type,
        }
        candidates.append(record)
        stored.append(record)
    workspace["resource_candidates"] = candidates
    workspace["sec_document_acquisition"] = {
        "last_manual_acquisition_at": datetime.now(timezone.utc).isoformat(),
        "stored_candidate_count": len(stored),
        "verified": False,
        "human_review_required": True,
    }
    evaluation[WORKSPACE_KEY] = workspace
    situation.evaluation = evaluation
    package.stored_records = stored
    return stored


def apply_research_case_sec_acquisition_metadata(
    rc: ResearchCase,
    package: SecDocumentAcquisitionPackage,
) -> list[ResearchDocument | ResearchSource]:
    existing_doc_urls = {doc.url for doc in (rc.documents or [])}
    existing_source_urls = {src.source_url for src in (rc.sources or [])}
    stored: list[ResearchDocument | ResearchSource] = []
    for doc in package.acquired_documents:
        if doc.url not in existing_doc_urls:
            research_doc = ResearchDocument(
                research_case_id=rc.id,
                doc_type=doc.doc_type,
                url=doc.url,
                title=doc.title,
                retrieved_at=datetime.now(timezone.utc),
                summary="Official SEC metadata candidate. Human review required; not verified evidence.",
                added_by="manual_sec_document_acquisition",
            )
            stored.append(research_doc)
            existing_doc_urls.add(doc.url)
        if doc.url not in existing_source_urls:
            source = ResearchSource(
                research_case_id=rc.id,
                source_name="SEC EDGAR official document candidate",
                source_url=doc.url,
                signal_quality="medium",
                notes="Manual SEC acquisition metadata only. Human review required; not verified evidence.",
            )
            stored.append(source)
            existing_source_urls.add(doc.url)
    package.stored_records = [
        {
            "record_type": "research_document" if isinstance(item, ResearchDocument) else "research_source",
            "url": item.url if isinstance(item, ResearchDocument) else item.source_url,
            "verified": False,
            "human_review_required": True,
        }
        for item in stored
    ]
    return stored
