# Linq Alert System

A crypto price alert bot over iMessage/SMS. Users text natural language commands ("alert me when BTC drops below 60k") and receive proactive notifications when thresholds are crossed. An ops dashboard shows live system state.

## Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.12, FastAPI, SQLite (WAL mode) |
| Frontend | Next.js 15, TypeScript, Tailwind CSS |
| LLM | Claude Haiku via Anthropic SDK (tool use) |
| Messaging | Linq API (iMessage/SMS) |
| Real-time | WebSocket (FastAPI native) |

## Architecture

```
Inbound SMS → Linq webhook → LLM intent parsing → alert CRUD
                                                 → message queue

Poller (30s sine wave) → threshold evaluation → message queue
                                              → WebSocket broadcast

Sender (event-driven) → Linq API → delivered/retry/dead-letter
                                  → WebSocket broadcast

Browser ← WebSocket ← broadcaster hub
```

- **No external price API** — prices are simulated with a sine wave (±5% around base) so thresholds cross predictably during demos
- **Event-driven sender** — enqueue wakes the sender immediately via `asyncio.Event`, no polling delay
- **Single WebSocket connection** per dashboard client carries all event types (alerts, queue, prices, history)

## Setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- [ngrok](https://ngrok.com) with a static domain (for receiving webhooks locally)

### Environment

Create `.env` in the project root:

```
LINQ_API_KEY=your_linq_api_key
LINQ_PHONE=your_linq_phone_number   # e.g. +12125551234
LINQ_WEBHOOK_SECRET=your_webhook_secret
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Runs on `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs on `http://localhost:3000`.

### Webhook

Expose the backend via ngrok:

```bash
ngrok http --domain=your-static-domain.ngrok-free.app 8000
```

In the Linq dashboard, set the webhook URL to:
```
https://your-static-domain.ngrok-free.app/webhook
```

Event type: `message.received`

## Environment Variables

| Variable | Description |
|---|---|
| `LINQ_API_KEY` | Linq partner API key |
| `LINQ_PHONE` | Your Linq phone number (sender) |
| `LINQ_WEBHOOK_SECRET` | HMAC secret for webhook signature verification |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude Haiku |
| `BACKEND_URL` | Backend URL for Next.js rewrites (default: `http://localhost:8000`) |
| `NEXT_PUBLIC_WS_URL` | WebSocket base URL for frontend (default: `ws://localhost:8000`) |

## Example SMS Commands

```
alert me when BTC drops below 60k
notify me if ETH goes above 4000
what am I tracking?
cancel my BTC alert
```

## Assumptions & Future Work

The following were out of scope for this prototype but are the natural next steps:

**Rate limiting on alert creation** — a user can create unlimited alerts via SMS. A per-phone token bucket (e.g. 5 alerts/hour) would prevent abuse.

**Webhook payload validation** — inbound Linq payloads are currently validated with `.get()` chaining. A Pydantic model would make the contract explicit and fail fast on unexpected shapes.

**Input validation on LLM outputs** — Claude's tool call outputs (asset name, direction, threshold) are trusted as-is. A validation layer before database writes would catch any malformed LLM responses.

**WebSocket back-pressure** — if a client's event queue fills up (maxsize=100), events are dropped. For a production system, the queue should drain old events or disconnect the slow client explicitly rather than silently losing data.

**Database retention** — alerts and trigger history grow unbounded. A background job pruning records older than N days would be needed at scale.

**Real price feed** — the sine wave poller is a stand-in for a push-based price feed. In production, prices would come from an exchange WebSocket stream (e.g. Binance `!miniTicker@arr`, which publishes all spot prices every second) rather than a 30-second timer. The swap requires no architectural changes: replace the `_run_poller` loop in `main.py` with a WebSocket client coroutine, and replace `_simulate()` with a parser for the exchange message format. Threshold evaluation and dashboard broadcasting are untouched since both paths bottom out in `poller._publish()`.

**Tests** — the message queue state machine (queued → sending → delivered/failed → dead_letter) and threshold evaluation logic in the poller are the highest-value targets for unit tests.

**React error boundary** — a single component exception currently crashes the entire dashboard. An `ErrorBoundary` wrapper would isolate failures.
