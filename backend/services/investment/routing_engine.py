import logging
import re
from backend.services.investment.sources.base import Filing
from backend.services.investment.playbook_loader import (
    load_evaluation_schema,
    get_default_playbook_status,
)

logger = logging.getLogger(__name__)


def detect_form_type(filing: Filing) -> str:
    """Extract EDGAR form type from filing.

    Returns normalized form type (e.g., '8-K', 'SC TO-T', 'Form 10').
    """
    if not filing.filing_type:
        return "unknown"

    form = filing.filing_type.strip().upper()

    # Normalize common variations
    if form.startswith("8-K"):
        return "8-K"
    elif form.startswith("DEFM14A"):
        return "DEFM14A"
    elif form.startswith("PREM14A"):
        return "PREM14A"
    elif "SC TO-T" in form or "SC 13E-4" in form:
        return "SC TO-T"
    elif "SC TO-I" in form or "SC 13E-1" in form:
        return "SC TO-I"
    elif "SC 14D-9" in form or "SCHEDULE 14D-9" in form:
        return "SC 14D-9"
    elif "FORM 10" in form or form == "10":
        return "Form 10"
    elif "14-12B" in form or "FORM 14-12B" in form:
        return "Form 14-12B"
    elif "SC 13D" in form or "SCHEDULE 13D" in form:
        return "SC 13D"
    elif "DFAN14A" in form:
        return "DFAN14A"
    elif "S-3" in form:
        return "S-3"
    elif "F-3" in form:
        return "F-3"
    elif "DEF 14A" in form or "DEFINITIVE PROXY" in form:
        return "DEF 14A"
    elif "13E-3" in form:
        return "13E-3"
    elif form.startswith("S-4"):
        return "S-4"

    return form


def detect_situation_type(filing: Filing) -> dict:
    """Detect situation type from filing using deterministic rules.

    Returns dict with:
        - situation_type: str
        - subtype: str | None
        - detection_confidence: str (HIGH, MEDIUM, LOW)
        - detected_signal: str (what triggered detection)
    """
    form_type = detect_form_type(filing)
    summary_lower = filing.summary.lower() if filing.summary else ""

    # High-confidence form-based detection
    if form_type == "SC TO-T":
        return {
            "situation_type": "merger_arbitrage",
            "subtype": "acquisition_tender_offer",
            "detection_confidence": "HIGH",
            "detected_signal": f"Form type: {form_type} (third-party acquisition tender)",
        }

    if form_type == "SC TO-I":
        return {
            "situation_type": "tender_offer",
            "subtype": "self_tender",
            "detection_confidence": "HIGH",
            "detected_signal": f"Form type: {form_type} (issuer self-tender)",
        }

    if form_type in ("Form 10", "Form 14-12B"):
        return {
            "situation_type": "spin_off",
            "subtype": "standard_spin_off",
            "detection_confidence": "HIGH",
            "detected_signal": f"Form type: {form_type} (spinco registration)",
        }

    if form_type == "SC 13D":
        return {
            "situation_type": "proxy_fight",
            "subtype": "activist_campaign",
            "detection_confidence": "HIGH",
            "detected_signal": f"Form type: {form_type} (activist ownership >5%)",
        }

    if form_type == "DFAN14A":
        return {
            "situation_type": "proxy_fight",
            "subtype": "proxy_contest",
            "detection_confidence": "HIGH",
            "detected_signal": f"Form type: {form_type} (dissident proxy solicitation)",
        }

    if form_type in ("S-3", "F-3") and ("rights offering" in summary_lower or "subscription rights" in summary_lower):
        return {
            "situation_type": "rights_offering",
            "subtype": "rights_offering",
            "detection_confidence": "HIGH",
            "detected_signal": f"Form type: {form_type} + rights offering language",
        }

    # Medium-confidence: 8-K or DEF 14A with keyword detection
    if form_type in ("8-K", "DEF 14A"):
        # Plan of dissolution/liquidation
        dissolution_patterns = [
            "plan of dissolution",
            "plan of liquidation",
            "liquidation",
            "dissolution",
            "complete dissolution",
            "wind down",
            "liquidating distribution",
        ]
        if any(pattern in summary_lower for pattern in dissolution_patterns):
            return {
                "situation_type": "bankruptcy",
                "subtype": "voluntary_liquidation",
                "detection_confidence": "HIGH",
                "detected_signal": f"Form type: {form_type} + dissolution language",
            }

        # Merger agreement
        merger_patterns = [
            "definitive merger agreement",
            "merger agreement",
            "acquisition agreement",
        ]
        if any(pattern in summary_lower for pattern in merger_patterns):
            # Check if it's a tender offer structure
            if "tender offer" in summary_lower:
                return {
                    "situation_type": "merger",
                    "subtype": "merger_via_tender",
                    "detection_confidence": "HIGH",
                    "detected_signal": f"Form type: {form_type} + merger + tender language",
                }
            return {
                "situation_type": "merger",
                "subtype": "cash_or_stock_merger",
                "detection_confidence": "MEDIUM",
                "detected_signal": f"Form type: {form_type} + merger agreement language",
            }

        # Non-binding offer (watchlist only)
        if "non-binding" in summary_lower or "exploring strategic alternatives" in summary_lower:
            return {
                "situation_type": "merger",
                "subtype": "non_binding_offer",
                "detection_confidence": "LOW",
                "detected_signal": f"Form type: {form_type} + non-binding language",
            }

    # DEFM14A / PREM14A
    if form_type == "DEFM14A":
        return {
            "situation_type": "merger",
            "subtype": "definitive_merger_proxy",
            "detection_confidence": "HIGH",
            "detected_signal": f"Form type: {form_type} (definitive merger proxy)",
        }

    if form_type == "PREM14A":
        return {
            "situation_type": "merger",
            "subtype": "preliminary_merger_proxy",
            "detection_confidence": "MEDIUM",
            "detected_signal": f"Form type: {form_type} (preliminary merger proxy)",
        }

    # S-4 (stock-for-stock merger)
    if form_type == "S-4":
        return {
            "situation_type": "merger",
            "subtype": "stock_for_stock_merger",
            "detection_confidence": "HIGH",
            "detected_signal": f"Form type: {form_type} (acquirer share registration)",
        }

    # 13E-3 (going-private)
    if form_type == "13E-3":
        return {
            "situation_type": "tender_offer",
            "subtype": "going_private",
            "detection_confidence": "HIGH",
            "detected_signal": f"Form type: {form_type} (going-private transaction)",
        }

    # Unknown
    return {
        "situation_type": "unknown",
        "subtype": None,
        "detection_confidence": "LOW",
        "detected_signal": f"Form type: {form_type} does not match known patterns",
    }


def route_playbook(situation_type: str, subtype: str | None, form_type: str | None) -> dict:
    """Route situation to appropriate playbook.

    Returns dict with:
        - selected_playbook: str (playbook name)
        - routed_from: str | None (source playbook if gateway)
        - routed_to: str | None (destination playbook if gateway)
        - routing_reason: str
    """
    # Direct routing for terminal playbooks
    if situation_type == "merger_arbitrage":
        return {
            "selected_playbook": "merger_arbitrage.md",
            "routed_from": None,
            "routed_to": None,
            "routing_reason": "SC TO-T acquisition tender routes directly to merger_arbitrage",
        }

    if situation_type == "spin_off":
        return {
            "selected_playbook": "spin_off.md",
            "routed_from": None,
            "routed_to": None,
            "routing_reason": "Form 10 / Form 14-12B routes directly to spin_off",
        }

    if situation_type == "tender_offer":
        return {
            "selected_playbook": "tender_offer.md",
            "routed_from": None,
            "routed_to": None,
            "routing_reason": "SC TO-I self-tender routes directly to tender_offer",
        }

    if situation_type == "bankruptcy":
        return {
            "selected_playbook": "bankruptcy.md",
            "routed_from": None,
            "routed_to": None,
            "routing_reason": "Plan of dissolution routes directly to bankruptcy (voluntary liquidation path)",
        }

    if situation_type == "proxy_fight":
        return {
            "selected_playbook": "proxy_fight.md",
            "routed_from": None,
            "routed_to": None,
            "routing_reason": "SC 13D / DFAN14A routes to proxy_fight (detection-only)",
        }

    if situation_type == "rights_offering":
        return {
            "selected_playbook": "rights_offering.md",
            "routed_from": None,
            "routed_to": None,
            "routing_reason": "S-3 / F-3 rights offering routes to rights_offering (detection-only)",
        }

    # Gateway routing for merger
    if situation_type == "merger":
        # Check if it should route to merger_arbitrage or tender_offer
        if subtype == "merger_via_tender":
            return {
                "selected_playbook": "merger.md",
                "routed_from": None,
                "routed_to": "merger_arbitrage.md",
                "routing_reason": "Merger via tender offer routes through merger gateway to merger_arbitrage",
            }

        if subtype in ("cash_or_stock_merger", "definitive_merger_proxy"):
            return {
                "selected_playbook": "merger.md",
                "routed_from": None,
                "routed_to": "merger_arbitrage.md",
                "routing_reason": "Definitive merger agreement routes through merger gateway to merger_arbitrage",
            }

        if subtype == "stock_for_stock_merger":
            return {
                "selected_playbook": "merger.md",
                "routed_from": None,
                "routed_to": "merger_arbitrage.md",
                "routing_reason": "Stock-for-stock merger routes through merger gateway to merger_arbitrage (cash component only evaluable)",
            }

        # Non-binding or preliminary: stay at gateway, watchlist only
        return {
            "selected_playbook": "merger.md",
            "routed_from": None,
            "routed_to": None,
            "routing_reason": "Non-binding or preliminary merger filing: detection only, watchlist",
        }

    # Unknown
    return {
        "selected_playbook": None,
        "routed_from": None,
        "routed_to": None,
        "routing_reason": f"Unknown situation type: {situation_type}",
    }


def check_scope(situation_type: str, subtype: str | None) -> dict:
    """Check if situation is within validated playbook scope.

    Returns dict with:
        - playbook_status: str (evaluator_ready, partial, routing_detection_only, detection_only, out_of_scope)
        - out_of_scope_reason: str | None
    """
    # Get default playbook status from evaluation_schema.json
    try:
        default_status = get_default_playbook_status(situation_type)
        if default_status:
            return {
                "playbook_status": default_status,
                "out_of_scope_reason": None,
            }
    except Exception as e:
        logger.warning(f"Could not load playbook status for {situation_type}: {e}")

    # Fallback to hardcoded rules if schema not available
    if situation_type == "merger_arbitrage":
        # Check for out-of-scope subtypes
        if subtype and ("stock_for_stock" in subtype or "cvr" in subtype):
            return {
                "playbook_status": "partial",
                "out_of_scope_reason": "Stock-for-stock and CVR components outside validated scope; cash component only evaluable",
            }
        return {
            "playbook_status": "evaluator_ready",
            "out_of_scope_reason": None,
        }

    if situation_type == "merger":
        return {
            "playbook_status": "routing_detection_only",
            "out_of_scope_reason": None,
        }

    if situation_type in ("spin_off", "tender_offer", "bankruptcy"):
        return {
            "playbook_status": "partial",
            "out_of_scope_reason": None,
        }

    if situation_type in ("proxy_fight", "rights_offering"):
        return {
            "playbook_status": "detection_only",
            "out_of_scope_reason": "Course provides no evaluation methodology for this situation type",
        }

    if situation_type == "unknown":
        return {
            "playbook_status": "out_of_scope",
            "out_of_scope_reason": "Situation type could not be determined from filing",
        }

    return {
        "playbook_status": "out_of_scope",
        "out_of_scope_reason": f"Situation type {situation_type} not recognized",
    }


def build_routing_decision(filing: Filing) -> dict:
    """Build complete routing decision for a filing.

    Returns dict matching routing_decision_schema from evaluation_schema.json.
    """
    form_type = detect_form_type(filing)
    detection = detect_situation_type(filing)
    routing = route_playbook(
        detection["situation_type"],
        detection.get("subtype"),
        form_type,
    )
    scope = check_scope(
        detection["situation_type"],
        detection.get("subtype"),
    )

    return {
        "detected_form_type": form_type,
        "detected_signal": detection["detected_signal"],
        "selected_playbook": routing["selected_playbook"],
        "routed_from": routing["routed_from"],
        "routed_to": routing["routed_to"],
        "routing_reason": routing["routing_reason"],
        "out_of_scope_reason": scope["out_of_scope_reason"],
        "detection_confidence": detection["detection_confidence"],
        "situation_type": detection["situation_type"],
        "subtype": detection.get("subtype"),
        "playbook_status": scope["playbook_status"],
    }
