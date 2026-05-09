# SwissEdge Dashboard Frontend

Private dashboard for SwissEdge investment evaluations and marketplace management.

## Tech Stack

- Next.js 16 (App Router)
- TypeScript
- Tailwind CSS
- React 19

## Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Configure backend URL:
```bash
cp .env.example .env.local
# Edit .env.local and set NEXT_PUBLIC_SWISSEDGE_API_BASE_URL
```

Default backend URL: `http://localhost:8000`

## Development

Start the development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Available Pages

- `/` - Dashboard home with navigation
- `/investment/evaluations` - Investment evaluations list with filters

## API Integration

The frontend connects to the SwissEdge FastAPI backend at the URL specified in `NEXT_PUBLIC_SWISSEDGE_API_BASE_URL`.

API client: `lib/api.ts`

## Build

```bash
npm run build
npm start
```

## Lint

```bash
npm run lint
```

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
