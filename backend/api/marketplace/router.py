from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.services.marketplace.adapters.tutti import TuttiAdapter
from backend.services.marketplace.listing_gen import generate_listing as gen_listing
from backend.services.observability import run_logger

router = APIRouter()
_tutti = TuttiAdapter()


class SearchRequest(BaseModel):
    query: str
    limit: int = 20


class PriceRequest(BaseModel):
    query: str


class AnalyzePhotoRequest(BaseModel):
    photo_url: str | None = None
    user_message: str
    chat_id: str | None = None


class GenerateListingRequest(BaseModel):
    item_description: str
    brand: str = ""
    condition: str = "Gut"
    category: str = ""
    price: float = 0


class PublishRequest(BaseModel):
    item_id: str
    marketplace: str = "tutti"
    approved: bool = True


@router.post("/search")
async def search_listings(req: SearchRequest, db: AsyncSession = Depends(get_db)):
    run_id = await run_logger.start_run(
        db,
        agent_name="marketplace_pricer",
        agent_type="fastapi",
        module="api.marketplace.router",
        runtime="fastapi",
        task_name="search_listings",
        input_summary=f"Search: {req.query!r} limit={req.limit}",
    )
    try:
        listings = await _tutti.search(req.query, limit=req.limit)
    except Exception as e:
        await run_logger.fail_run(db, run_id, str(e))
        await db.commit()
        raise HTTPException(status_code=502, detail=f"Tutti.ch search failed: {e}")

    await run_logger.finish_run(
        db, run_id,
        output_summary=f"{len(listings)} listings found for {req.query!r}",
        final_outcome=f"{len(listings)} results",
        outcome_score=1 if listings else 0,
        api_calls_made=[{"source": "tutti_ch", "results": len(listings)}],
    )
    await db.commit()

    return {
        "query": req.query,
        "count": len(listings),
        "listings": [
            {
                "title": l.title,
                "price": l.price,
                "currency": l.currency,
                "url": l.url,
                "marketplace": l.marketplace,
                "condition": l.condition,
            }
            for l in listings
        ],
    }


@router.post("/get-price")
async def get_price(req: PriceRequest, db: AsyncSession = Depends(get_db)):
    run_id = await run_logger.start_run(
        db,
        agent_name="marketplace_pricer",
        agent_type="fastapi",
        module="api.marketplace.router",
        runtime="fastapi",
        task_name="get_price",
        input_summary=f"Price query: {req.query!r}",
    )
    try:
        comparison = await _tutti.get_price(req.query)
    except Exception as e:
        await run_logger.fail_run(db, run_id, str(e))
        await db.commit()
        raise HTTPException(status_code=502, detail=f"Price comparison failed: {e}")

    await run_logger.finish_run(
        db, run_id,
        output_summary=f"avg={comparison.average} median={comparison.median} count={comparison.count}",
        final_outcome=f"Price found: avg {comparison.average} {comparison.currency}",
        outcome_score=1 if comparison.count else 0,
        api_calls_made=[{"source": "tutti_ch", "results": comparison.count}],
    )
    await db.commit()

    return {
        "query": req.query,
        "currency": comparison.currency,
        "average": comparison.average,
        "median": comparison.median,
        "min": comparison.min_price,
        "max": comparison.max_price,
        "count": comparison.count,
    }


@router.post("/analyze-photo")
async def analyze_photo(req: AnalyzePhotoRequest):
    """
    Entry point for OpenClaw: receive photo + user message.
    Phase 1: uses user_message as item description. Phase 2+: vision API for photo.
    """
    try:
        listing, _ = await gen_listing(item_description=req.user_message)
        price_comparison = await _tutti.get_price(listing.get("title", req.user_message))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    return {
        "chat_id": req.chat_id,
        "draft_title": listing.get("title"),
        "draft_description": listing.get("description"),
        "category_suggestion": listing.get("category_suggestion"),
        "price_comparison": {
            "average": price_comparison.average,
            "median": price_comparison.median,
            "min": price_comparison.min_price,
            "max": price_comparison.max_price,
            "count": price_comparison.count,
            "currency": price_comparison.currency,
        },
        "note": "Phase 1: photo analysis not yet active. Description taken from user_message.",
    }


@router.post("/generate-listing")
async def generate_listing_endpoint(req: GenerateListingRequest, db: AsyncSession = Depends(get_db)):
    run_id = await run_logger.start_run(
        db,
        agent_name="marketplace_lister",
        agent_type="fastapi",
        module="api.marketplace.router",
        runtime="fastapi",
        task_name="generate_listing",
        input_summary=f"Item: {req.item_description[:80]!r} brand={req.brand} condition={req.condition}",
        human_approval_required=True,
    )
    try:
        result, usage = await gen_listing(
            item_description=req.item_description,
            brand=req.brand,
            condition=req.condition,
            category=req.category,
            price=req.price,
        )
    except Exception as e:
        await run_logger.fail_run(db, run_id, str(e))
        await db.commit()
        raise HTTPException(status_code=502, detail=str(e))

    # Log AI usage so ai_usage table is populated and tokens/cost are tracked
    try:
        await run_logger.log_ai_usage(
            db,
            run_id=run_id,
            agent_name="marketplace_lister",
            provider=usage.get("provider", "openai"),
            model=usage.get("model", "gpt-4o-mini"),
            prompt_name="listing_generator",
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
        )
    except Exception:
        pass

    title = result.get("title", "")
    await run_logger.finish_run(
        db, run_id,
        output_summary=f"Listing draft: {title!r}",
        final_outcome="Listing draft generated. Awaiting human approval before publish.",
        outcome_score=1 if title else 0,
        model_used=usage.get("model"),
        input_tokens=usage.get("input_tokens"),
        output_tokens=usage.get("output_tokens"),
    )
    await db.commit()
    return result


@router.post("/publish")
async def publish_listing(req: PublishRequest):
    if not req.approved:
        return {"status": "cancelled"}
    draft = await _tutti.create_listing({"title": f"Item {req.item_id}"})
    return draft


@router.post("/check-watched")
async def check_watched_prices():
    """Placeholder for Phase 2 price monitoring cron endpoint."""
    return {"status": "ok", "watched_items_checked": 0, "alerts_sent": 0}
