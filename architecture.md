# Architecture — SwissEdge Platform

## System Overview

SwissEdge follows a **brain-muscle** architecture where OpenClaw handles lightweight orchestration (brain) and FastAPI handles compute-intensive work (muscle). This minimizes AI token consumption while maintaining full functionality.

```
┌─────────────────────────────────────────────────────┐
│                    Contabo VPS                       │
│                                                     │
│  ┌──────────────┐     ┌──────────────────────────┐  │
│  │   OpenClaw    │────▶│     FastAPI Backend       │  │
│  │  (brain)      │ HTTP│                          │  │
│  │              │◀────│  ┌────────────────────┐   │  │
│  │ • Telegram   │     │  │ Marketplace Service│   │  │
│  │ • Cron jobs  │     │  │ • Adapters         │   │  │
│  │ • Routing    │     │  │ • Price engine     │   │  │
│  └──────────────┘     │  │ • Listing gen      │   │  │
│                       │  └────────────────────┘   │  │
│                       │  ┌────────────────────┐   │  │
│                       │  │ Investment Service  │   │  │
│                       │  │ • SEC/EDGAR search  │   │  │
│                       │  │ • Evaluator         │   │  │
│                       │  │ • Course index      │   │  │
│                       │  └────────────────────┘   │  │
│                       │  ┌────────────────────┐   │  │
│                       │  │ Health Service      │   │  │
│                       │  │ • Component checks  │   │  │
│                       │  │ • OpenClaw monitor  │   │  │
│                       │  └────────────────────┘   │  │
│                       │                          │  │
│                       │  PostgreSQL  ◀──────────▶│  │
│                       └──────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
        │
        │ API calls
        ▼
┌──────────────────┐
│   Vercel          │
│   Next.js web     │
│   Research journal│
└──────────────────┘
```

## Data Flow: Selling an Item

```
User sends photo + "vende esto" via Telegram
        │
        ▼
OpenClaw receives message
        │
        ▼
OpenClaw calls POST /api/marketplace/analyze-photo
  body: { photo_url, user_message, chat_id }
        │
        ▼
FastAPI:
  1. Analyzes photo (vision API or local model)
  2. Identifies item type, brand, condition
  3. Searches similar listings on Tutti.ch via adapter
  4. Calculates price: average, range, percentile
  5. Generates Hochdeutsch title + description
  6. Returns draft listing
        │
        ▼
OpenClaw receives response
        │
        ▼
OpenClaw sends draft to user via Telegram:
  "Título: Samsung Galaxy S23, sehr guter Zustand
   Preis: CHF 350 (Durchschnitt: CHF 380, Bereich: 300-450)
   Beschreibung: [generated text]
   
   ¿Publicar? ✅ Sí  ✏️ Editar  ❌ Cancelar"
        │
        ▼
User approves → OpenClaw calls POST /api/marketplace/publish
        │
        ▼
FastAPI creates listing (phase 1: returns copy-paste text)
(phase 2+: automates via browser)
```

## Data Flow: Finding a Deal

```
User sends "busca una PS5 barata" via Telegram
        │
        ▼
OpenClaw calls POST /api/marketplace/search
  body: { query: "PS5", chat_id }
        │
        ▼
FastAPI:
  1. Searches across configured marketplaces:
     - Tutti.ch (scraping)
     - Ricardo.ch (phase 2)
     - Amazon DE/ES/FR (PA-API)
     - Digitec (scraping)
  2. Aggregates results
  3. Calculates average price and ranking
  4. Identifies best deals (% below average)
  5. Returns ranked results
        │
        ▼
OpenClaw formats and sends via Telegram:
  "PS5 encontradas:
   1. Tutti.ch — CHF 320 (16% unter Durchschnitt) ⭐
   2. Amazon.de — CHF 380 (0% vs Durchschnitt)
   3. Ricardo.ch — CHF 350 (8% unter Durchschnitt)
   
   ¿Quieres que siga monitorizando el precio?"
```

## Data Flow: Special Situations Radar

```
Cron job (4x daily via OpenClaw)
        │
        ▼
OpenClaw calls POST /api/investment/scan
        │
        ▼
FastAPI:
  1. Queries SEC EDGAR for new filings:
     - 8-K (material events)
     - S-1/F-1 (new registrations)
     - SC TO (tender offers)
     - Form 10 (spin-offs)
     - DEF 14A (proxy fights)
  2. Filters by situation type
  3. For each candidate:
     a. Looks up course_index/master_index.json
     b. Finds matching chapter and methodology
     c. Runs evaluation checklist
     d. Scores strengths and weaknesses
     e. Attaches course chapter + timestamp reference
  4. Saves to database with status DETECTED
  5. Returns summary
        │
        ▼
OpenClaw sends alert via Telegram:
  "🔔 3 nuevas situaciones detectadas:
   1. SPIN-OFF: CompanyX separating DivisionY (Form 10 filed)
      → Chapter 7, min 14:30
   2. MERGER: CompanyA acquiring CompanyB ($2.1B, 8-K)
      → Chapter 12, min 8:15
   3. TENDER OFFER: Fund acquiring 30% of CompanyC
      → Chapter 9, min 22:00
   
   Ver detalles: /situations"
```

## Data Flow: Health Check / Doctor

```
Claude Code session starts
  User says: "revisa el sistema" or runs /doctor
        │
        ▼
Claude Code executes: python scripts/doctor.py
        │
        ▼
doctor.py calls GET /api/health/full
        │
        ▼
FastAPI checks each component:
  ✅ PostgreSQL: connected, 1,234 records
  ✅ SEC EDGAR API: responding, last query 2h ago
  ❌ Tutti.ch scraper: blocked (403), last success 3 days ago
  ✅ Telegram bot: webhook active
  ⚠️ OpenClaw cron: "scan_special_situations" last ran 26h ago (expected: 6h)
  ✅ Course index: 20/20 chapters processed
  ❌ Amazon PA-API: auth expired
        │
        ▼
Claude Code reads the report and:
  1. Explains what's broken and why
  2. Suggests fixes
  3. Can apply fixes directly if user approves
```

## Database Schema (Core Tables)

```sql
-- Marketplace
CREATE TABLE inventory_items (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    description_de TEXT,
    photos JSONB,          -- array of photo URLs
    category TEXT,
    condition TEXT,
    price_asked DECIMAL,
    price_market_avg DECIMAL,
    price_market_range JSONB,
    status TEXT DEFAULT 'draft',  -- draft, listed, sold, cancelled
    marketplace TEXT,
    listing_url TEXT,
    trust_score INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Investment
CREATE TABLE special_situations (
    id UUID PRIMARY KEY,
    situation_type TEXT NOT NULL,  -- spin_off, merger, tender_offer, etc.
    company_name TEXT NOT NULL,
    ticker TEXT,
    filing_type TEXT,              -- 8-K, S-1, Form 10, etc.
    filing_url TEXT,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'detected',
    -- detected → analyzing → watchlist → active → closed_profit → closed_loss → passed → expired
    evaluation JSONB,             -- checklist results
    strengths JSONB,
    weaknesses JSONB,
    risks JSONB,
    course_chapter INTEGER,
    course_timestamp TEXT,         -- "14:30"
    source_urls JSONB,
    notes TEXT,
    follow_up_date DATE,           -- agenda: when to check again
    published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE situation_history (
    id UUID PRIMARY KEY,
    situation_id UUID REFERENCES special_situations(id),
    status_from TEXT,
    status_to TEXT,
    reason TEXT,
    changed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Source tracking
CREATE TABLE investment_sources (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    source_type TEXT,        -- sec_edgar, news, blog, newsletter
    active BOOLEAN DEFAULT TRUE,
    last_checked TIMESTAMPTZ,
    check_frequency_hours INTEGER DEFAULT 6,
    notes TEXT
);

-- Contact discovery (phase 3+)
CREATE TABLE investor_contacts (
    id UUID PRIMARY KEY,
    name TEXT,
    platform TEXT,            -- substack, seeking_alpha, twitter, blog
    url TEXT,
    discovered_via TEXT,       -- which historical situation led to finding them
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Health monitoring
CREATE TABLE health_checks (
    id UUID PRIMARY KEY,
    component TEXT NOT NULL,
    status TEXT NOT NULL,       -- ok, warning, error
    message TEXT,
    checked_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Marketplace Adapter Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Listing:
    title: str
    price: float
    currency: str
    url: str
    marketplace: str
    condition: str | None
    image_urls: list[str]

@dataclass 
class PriceComparison:
    average: float
    median: float
    min_price: float
    max_price: float
    count: int
    currency: str
    listings: list[Listing]

class MarketplaceAdapter(ABC):
    @abstractmethod
    async def search(self, query: str, **filters) -> list[Listing]:
        """Search for listings matching query."""
        
    @abstractmethod
    async def get_price(self, query: str) -> PriceComparison:
        """Get price comparison for an item."""
    
    @abstractmethod
    async def create_listing(self, item: dict) -> dict:
        """Create a listing draft or publish."""
    
    @abstractmethod
    async def get_listing_status(self, listing_id: str) -> str:
        """Check listing status."""
```

## Investment Source Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Filing:
    company: str
    ticker: str | None
    filing_type: str
    date: str
    url: str
    summary: str
    situation_type: str | None  # spin_off, merger, etc.

class InvestmentSource(ABC):
    @abstractmethod
    async def search_recent(self, hours_back: int = 6) -> list[Filing]:
        """Search for recent filings/news."""
    
    @abstractmethod
    async def search_by_type(self, situation_type: str) -> list[Filing]:
        """Search for specific situation types."""
```

## Configuration Files

### config/sources.yaml
```yaml
investment_sources:
  - name: SEC EDGAR
    type: sec_edgar
    base_url: https://efts.sec.gov/LATEST/search-index
    filing_types:
      - "8-K"     # material events
      - "S-1"     # IPO registrations
      - "F-1"     # foreign IPO
      - "SC TO"   # tender offers
      - "Form 10" # spin-offs
      - "DEF 14A" # proxy statements
    check_frequency_hours: 6
    active: true

  # Add more sources as you discover them from the course
  # - name: PR Newswire
  #   type: news_feed
  #   ...
```

### config/marketplaces.yaml
```yaml
marketplaces:
  tutti:
    name: Tutti.ch
    active: true
    phase: 1
    method: browser_automation  # no public API
    base_url: https://www.tutti.ch
    language: de
    notes: "robots.txt blocks AI bots. Phase 1 = copy-paste drafts only."

  ricardo:
    name: Ricardo.ch
    active: false
    phase: 2
    method: api
    requires: partnership_key
    notes: "Needs partnership credentials from Ricardo."

  amazon_de:
    name: Amazon.de
    active: false
    phase: 1
    method: pa_api
    requires: amazon_associates_account
    notes: "Product Advertising API for price comparison only."

  digitec:
    name: Digitec.ch
    active: false
    phase: 1
    method: scraping
    notes: "No public API. Use for price comparison only."
```

### config/safety_rules.yaml
```yaml
telegram_bot:
  never_share:
    - phone_number
    - exact_address
    - email
    - bank_details
  
  never_without_approval:
    - accept_offer
    - arrange_pickup
    - share_location
    - publish_listing  # phase 1 always, phase 2 depends on trust score
    - respond_to_buyer_negotiation
  
  auto_respond_allowed:
    - confirm_availability: "Ja, der Artikel ist noch verfügbar."
    - confirm_price: "Der Preis ist CHF {price}."
    - decline_lowball: "Danke für Ihr Interesse, aber der Preis ist fest."

investment:
  mandatory_disclaimer: |
    ⚠️ DISCLAIMER: This analysis is for informational and educational purposes only. 
    It is NOT personalized financial advice. Always do your own research before 
    making investment decisions. Past special situations do not guarantee future results.
  
  always_include:
    - uncertainty_level
    - identified_risks
    - source_urls
    - course_chapter_reference
    - disclaimer
```

## OpenClaw Integration Points

OpenClaw calls these FastAPI endpoints:

| OpenClaw Task | HTTP Method | Endpoint | Frequency |
|---|---|---|---|
| Telegram: sell item | POST | /api/marketplace/analyze-photo | on message |
| Telegram: search deals | POST | /api/marketplace/search | on message |
| Telegram: approve listing | POST | /api/marketplace/publish | on message |
| Scan special situations | POST | /api/investment/scan | 4x daily |
| Follow-up scheduled items | POST | /api/investment/follow-up | 1x daily |
| Health check | GET | /api/health/full | 2x daily |
| Alert on failure | GET | /api/health/full | if error → Telegram alert |

## Token Optimization Strategy

1. **OpenClaw does routing, not reasoning.** It receives Telegram messages and maps them to HTTP endpoints. No complex prompt processing.
2. **Prompts are stored in files** (`backend/prompts/`), not generated dynamically. OpenClaw passes user input to FastAPI, which appends the right prompt template.
3. **Course data is pre-processed.** The master index is a JSON file, not re-analyzed each time.
4. **Scraping results are cached.** Price comparisons cached for 1 hour. SEC results cached for 6 hours.
5. **Health checks are lightweight.** Simple HTTP status checks, no AI reasoning needed.
