# Smart Mess Waste Intelligence Platform
## Framework Analysis & Phase-Wise Implementation Plan

---

# 1. Executive Summary

This document presents a comprehensive analysis of technology framework options for the **Smart Mess Waste Intelligence Platform** — a Raspberry Pi-based institutional food waste management system. The analysis considers the unique constraints of running on edge hardware (Raspberry Pi) alongside ML models, while supporting API-driven architecture, real-time analytics, notifications, and public internet exposure.

### Key Decision Drivers

| Driver | Priority | Description |
|--------|----------|-------------|
| Resource Efficiency | 🔴 Critical | Raspberry Pi has limited RAM (4GB/8GB); ML models already consume significant resources |
| ML Co-existence | 🔴 Critical | ML pipeline runs on same device; shared runtime avoids overhead |
| API-First Architecture | 🟡 High | System must be API-driven for frontend agnosticism |
| Always-On Services | 🟡 High | Analytics, notifications, rule engine must run continuously even when dashboard is idle |
| Low Concurrent Users | 🟢 Medium | Web dashboard used by few admins; not a high-traffic application |
| Public Internet Exposure | 🟡 High | College authority must access dashboard remotely |
| Offline Survivability | 🟡 High | System must function without internet; sync when restored |

---

# 2. Backend Framework Analysis

## 2.1 Evaluation Criteria

Each framework is rated on a scale of 1-10 across the following criteria:

| Criteria | Weight | Description |
|----------|--------|-------------|
| RAM Efficiency | 20% | Memory footprint on Raspberry Pi |
| ML Integration | 20% | Ability to co-exist with Python ML pipeline |
| Async Support | 15% | Non-blocking I/O for concurrent operations |
| WebSocket Support | 10% | Native real-time communication |
| API Design | 10% | REST API development ergonomics |
| Ecosystem & Libraries | 10% | Available packages and community support |
| Developer Experience | 10% | Type safety, docs, debugging tools |
| Production Readiness | 5% | Proven at scale, stability |

---

## 2.2 Framework Ratings

### FastAPI (Python) — ⭐ 9.5/10 🏆 RECOMMENDED

| Criteria | Score | Notes |
|----------|-------|-------|
| RAM Efficiency | 9/10 | ~30-50MB base; much lighter than Django |
| ML Integration | 10/10 | **Same Python runtime as ML** — zero overhead |
| Async Support | 10/10 | Native async/await built on Starlette |
| WebSocket Support | 9/10 | Built-in WebSocket via Starlette |
| API Design | 10/10 | Automatic OpenAPI/Swagger docs; Pydantic validation |
| Ecosystem | 9/10 | Full Python ecosystem; pip packages |
| Developer Experience | 9/10 | Type hints, auto-docs, great IDE support |
| Production Readiness | 8/10 | Used by Microsoft, Uber; proven at scale |

**Strengths:**
- Same runtime as ML pipeline — no second language runtime overhead on Pi
- Native async/await — handles concurrent API + WebSocket + background tasks efficiently
- Built-in WebSocket support — real-time dashboard without extra dependencies
- Automatic OpenAPI documentation — API-first architecture gets free interactive docs
- Pydantic validation — perfect for complex rule engine conditions and API data contracts
- Background tasks + Celery/ARQ integration — notifications, emails, scheduled analytics
- ~30-50MB RAM footprint — leaves room for ML models on Pi's 4GB/8GB
- Type hints throughout — reduces bugs in complex rule engine logic
- Dependency injection system — clean, testable architecture

**Weaknesses:**
- GIL limitation for CPU-bound tasks (not an issue since ML uses separate processes)
- Relatively newer than Flask/Django (but mature and production-proven)

**RAM Budget on Pi (4GB model):**
```
OS + System:           ~300MB
ML Pipeline:           ~800MB-1.5GB
FastAPI Backend:       ~50-80MB
SQLite:                ~20-50MB
Redis:                 ~30-50MB
Nginx:                 ~10-20MB
Remaining available:   ~1.5-2GB
```

---

### Go — Gin/Fiber — ⭐ 7.5/10

| Criteria | Score | Notes |
|----------|-------|-------|
| RAM Efficiency | 10/10 | ~10-20MB; most memory-efficient option |
| ML Integration | 4/10 | Requires CGo or subprocess communication |
| Async Support | 9/10 | Goroutines; excellent concurrency |
| WebSocket Support | 9/10 | Excellent via gorilla/websocket or nhooyr |
| API Design | 8/10 | Clean but manual Swagger docs |
| Ecosystem | 7/10 | Growing but smaller than Python |
| Developer Experience | 7/10 | Strong typing but more verbose |
| Production Readiness | 9/10 | Built for production systems |

**Strengths:**
- Lowest RAM footprint (~10-20MB)
- Excellent concurrency via goroutines
- Single binary deployment — zero dependency
- Fastest response times
- Built for production systems

**Weaknesses:**
- Cannot share runtime with Python ML — must use IPC (gRPC/subprocess)
- Smaller web ecosystem than Python
- More verbose code for complex business logic (rule engine)
- Two-language stack increases complexity
- No automatic API documentation

**Verdict:** Excellent performance but the two-language overhead (Go + Python for ML) makes it suboptimal when ML runs on the same device.

---

### Express.js (Node.js) — ⭐ 6.5/10

| Criteria | Score | Notes |
|----------|-------|-------|
| RAM Efficiency | 6/10 | ~50-80MB; V8 engine overhead |
| ML Integration | 3/10 | Requires child_process or microservice |
| Async Support | 8/10 | Event loop; good for I/O |
| WebSocket Support | 9/10 | socket.io is mature and battle-tested |
| API Design | 7/10 | Good but manual validation |
| Ecosystem | 9/10 | npm is the largest package registry |
| Developer Experience | 8/10 | Good tooling, but JavaScript quirks |
| Production Readiness | 8/10 | Very widely used |

**Strengths:**
- socket.io is the most mature real-time library
- Massive npm ecosystem
- JSON-native (API responses are natural)
- Good developer availability

**Weaknesses:**
- Requires separate Python runtime for ML — doubles runtime overhead on Pi
- V8 engine uses ~50-80MB minimum
- No built-in type safety (TypeScript helps but adds complexity)
- Callback/promise complexity for rule engine logic
- Manual validation (needs joi/zod)

**Verdict:** Good for real-time but running Node.js + Python on same Pi is wasteful when FastAPI handles both.

---

### Flask (Python) — ⭐ 6/10

| Criteria | Score | Notes |
|----------|-------|-------|
| RAM Efficiency | 7/10 | ~20-40MB; lightweight |
| ML Integration | 10/10 | Same Python runtime |
| Async Support | 3/10 | Limited async (Flask 2.0+ has basic support) |
| WebSocket Support | 4/10 | Requires Flask-SocketIO extension |
| API Design | 6/10 | Manual; no auto-docs |
| Ecosystem | 8/10 | Mature Python ecosystem |
| Developer Experience | 7/10 | Simple but lacks modern features |
| Production Readiness | 8/10 | Battle-tested |

**Strengths:**
- Lightweight WSGI framework
- Same runtime as ML
- Simple to start with
- Mature ecosystem

**Weaknesses:**
- No native async — requires workarounds for concurrent operations
- No built-in WebSocket — needs Flask-SocketIO (adds complexity)
- No automatic API documentation
- No built-in data validation (needs marshmallow/pydantic separately)
- WSGI model not ideal for real-time features
- Less modern developer experience compared to FastAPI

**Verdict:** FastAPI is strictly superior for this use case — Flask offers no advantage.

---

### NestJS (Node.js/TypeScript) — ⭐ 5.5/10

| Criteria | Score | Notes |
|----------|-------|-------|
| RAM Efficiency | 4/10 | ~80-120MB; heavy Node.js framework |
| ML Integration | 3/10 | Requires child_process or microservice |
| Async Support | 8/10 | Good async support |
| WebSocket Support | 9/10 | Built-in gateway support |
| API Design | 9/10 | Decorators, guards, pipes — excellent |
| Ecosystem | 8/10 | Good TypeScript ecosystem |
| Developer Experience | 9/10 | Excellent for enterprise patterns |
| Production Readiness | 7/10 | Good but heavy for Pi |

**Strengths:**
- Enterprise-grade architecture
- Built-in WebSocket gateway
- Excellent TypeScript support
- Angular-like module system
- Dependency injection

**Weaknesses:**
- Too heavy for Raspberry Pi (~80-120MB minimum)
- Requires separate Python runtime for ML
- Enterprise patterns add unnecessary complexity for this scale
- Steeper learning curve

**Verdict:** Overkill for Raspberry Pi deployment. Designed for enterprise servers, not edge devices.

---

### Django (Python) — ⭐ 4/10

| Criteria | Score | Notes |
|----------|-------|-------|
| RAM Efficiency | 3/10 | ~80-150MB; heaviest Python framework |
| ML Integration | 10/10 | Same Python runtime |
| Async Support | 4/10 | Limited (Django 4.0+ has ASGI but immature) |
| WebSocket Support | 4/10 | Django Channels adds complexity |
| API Design | 7/10 | DRF is good but verbose |
| Ecosystem | 10/10 | Most complete Python web ecosystem |
| Developer Experience | 7/10 | Good admin, but heavy conventions |
| Production Readiness | 9/10 | Battle-tested at scale |

**Strengths:**
- Most complete Python web framework
- Built-in admin interface
- Django ORM is powerful
- Django REST Framework for APIs
- Massive ecosystem

**Weaknesses:**
- Heaviest Python framework — too resource-intensive for Pi
- Django Channels for WebSocket is complex and adds Redis dependency
- ORM is heavier than needed for SQLite edge deployment
- Monolithic — hard to use only what you need
- Sync-first architecture; async is bolted on

**Verdict:** Too heavy for Raspberry Pi. FastAPI provides all needed features at a fraction of the resource cost.

---

## 2.3 Backend Framework Summary

| Rank | Framework | Rating | RAM | ML Co-exist | Async | WS | Best For |
|------|-----------|--------|-----|-------------|-------|----|----------|
| 🥇 | **FastAPI** | **9.5/10** | 30-50MB | ✅ Native | ✅ Native | ✅ Native | **Our use case** |
| 🥈 | Go (Gin/Fiber) | 7.5/10 | 10-20MB | ❌ IPC | ✅ Goroutines | ✅ Native | Performance-critical without ML |
| 🥉 | Express.js | 6.5/10 | 50-80MB | ❌ Subprocess | ⚠️ Event loop | ✅ socket.io | JS-heavy teams |
| 4 | Flask | 6/10 | 20-40MB | ✅ Native | ❌ Limited | ⚠️ Extension | Simple CRUD apps |
| 5 | NestJS | 5.5/10 | 80-120MB | ❌ Subprocess | ✅ | ✅ Gateway | Enterprise servers |
| 6 | Django | 4/10 | 80-150MB | ✅ Native | ⚠️ Basic | ⚠️ Channels | Content-heavy sites |

### ✅ Final Backend Recommendation: FastAPI

---

# 3. Frontend Framework Analysis

## 3.1 Evaluation Criteria

| Criteria | Weight | Description |
|----------|--------|-------------|
| Bundle Size | 20% | Smaller = faster load on Pi-served pages, less bandwidth over tunnel |
| Server-Side Rendering | 15% | SSR improves initial load over slow connections |
| Real-time Integration | 15% | WebSocket/SSE integration quality |
| Component Ecosystem | 15% | Available UI libraries and chart components |
| Developer Productivity | 15% | Speed of building complex dashboards |
| Resource Efficiency on Pi | 10% | Build tool RAM usage during development |
| Learning Curve | 10% | Team adoption speed |

---

## 3.2 Framework Ratings

### SvelteKit — ⭐ 9/10 🏆 RECOMMENDED

| Criteria | Score | Notes |
|----------|-------|-------|
| Bundle Size | 10/10 | ~10-30KB gzipped; smallest of all frameworks |
| Server-Side Rendering | 9/10 | Built-in SSR with adapter-node |
| Real-time Integration | 8/10 | Good WebSocket support; lighter than React |
| Component Ecosystem | 7/10 | Growing; shadcn-svelte available |
| Developer Productivity | 9/10 | Least boilerplate; reactive by default |
| Resource Efficiency | 9/10 | Vite-based; fast builds |
| Learning Curve | 8/10 | Simplest reactive model |

**Strengths:**
- **Smallest bundle size** — critical for Pi-served pages over limited bandwidth / Cloudflare Tunnel
- **Built-in SSR** — fast initial loads for dashboard accessed over internet
- **No virtual DOM** — reactivity compiled away; less CPU on client, smoother on low-end devices
- **Less boilerplate** — faster development for complex dashboards with many components
- **Vite-powered** — fast development builds
- **Adapter-node** — can run SSR on Pi or deploy statically

**Weaknesses:**
- Smaller ecosystem than React
- Fewer charting libraries (but can use any JS chart lib)
- Team may need to learn Svelte

---

### React + Vite + ShadCN + Tailwind — ⭐ 8/10

| Criteria | Score | Notes |
|----------|-------|-------|
| Bundle Size | 6/10 | ~150KB+ gzipped; larger than Svelte |
| Server-Side Rendering | 5/10 | Requires Next.js or separate SSR setup |
| Real-time Integration | 9/10 | socket.io client is mature |
| Component Ecosystem | 10/10 | Largest ecosystem; shadcn/ui, Recharts, etc. |
| Developer Productivity | 8/10 | Excellent with TypeScript + ShadCN |
| Resource Efficiency | 7/10 | Vite is efficient; React runtime adds weight |
| Learning Curve | 8/10 | Most developers know React |

**Strengths:**
- Largest component ecosystem
- ShadCN/ui provides beautiful, accessible components
- Recharts + React ecosystem for analytics charts
- Most developers know React — easier team adoption
- Excellent TypeScript support
- Rich debugging tools (React DevTools)

**Weaknesses:**
- Larger bundle size (~150KB+ gzipped)
- No built-in SSR (need separate setup or Next.js)
- Virtual DOM overhead on low-end client devices
- More boilerplate than Svelte for reactive state

---

### Vue + Vite — ⭐ 7.5/10

| Criteria | Score | Notes |
|----------|-------|-------|
| Bundle Size | 8/10 | ~50KB gzipped; moderate |
| Server-Side Rendering | 7/10 | Nuxt.js provides SSR |
| Real-time Integration | 8/10 | Good WebSocket support |
| Component Ecosystem | 8/10 | Good; Vuetify, Element Plus, Naive UI |
| Developer Productivity | 8/10 | Composition API is clean |
| Resource Efficiency | 8/10 | Vite is efficient |
| Learning Curve | 7/10 | Moderate; Composition API needs learning |

**Strengths:**
- Good balance of bundle size and ecosystem
- Composition API is clean and powerful
- Nuxt.js for SSR
- Good charting libraries (ECharts Vue wrapper)
- Approachable learning curve

**Weaknesses:**
- Smaller ecosystem than React
- Two API styles (Options + Composition) can confuse
- Less enterprise adoption than React

---

### HTMX + Alpine.js — ⭐ 6/10

| Criteria | Score | Notes |
|----------|-------|-------|
| Bundle Size | 10/10 | ~30KB total; minimal |
| Server-Side Rendering | 10/10 | Server-rendered by default |
| Real-time Integration | 6/10 | SSE support; limited WebSocket |
| Component Ecosystem | 3/10 | No component system; server-side |
| Developer Productivity | 5/10 | Fast for simple UIs; hard for complex dashboards |
| Resource Efficiency | 10/10 | Almost zero client overhead |
| Learning Curve | 9/10 | Simplest to learn |

**Strengths:**
- Tiny footprint — ideal for bandwidth-constrained access
- Server-rendered — no client framework needed
- Simple mental model
- Works great for simple CRUD

**Weaknesses:**
- No component model — hard to build complex analytics dashboards
- Limited interactivity for dynamic charts and real-time updates
- No state management — complex rule builder UI is very difficult
- Not suitable for the sophisticated dashboard this platform requires

---

### Next.js — ⭐ 5/10

| Criteria | Score | Notes |
|----------|-------|-------|
| Bundle Size | 3/10 | ~200KB+; heaviest SPA option |
| Server-Side Rendering | 10/10 | Best SSR implementation |
| Real-time Integration | 8/10 | Good; custom server for WS |
| Component Ecosystem | 10/10 | Full React ecosystem |
| Developer Productivity | 7/10 | Good but many Next.js-specific patterns |
| Resource Efficiency | 3/10 | Heavy build process; not ideal for Pi |
| Learning Curve | 5/10 | Next.js adds complexity on top of React |

**Strengths:**
- Best-in-class SSR
- Full React ecosystem
- Great for SEO (not needed for this app)
- Vercel deployment optimization

**Weaknesses:**
- **Too heavy for Raspberry Pi** — build process can consume 500MB+ RAM
- SEO is irrelevant for an admin dashboard behind auth
- Next.js server adds unnecessary overhead when FastAPI serves the API
- Over-engineered for a dashboard with few concurrent users

---

## 3.3 Frontend Framework Summary

| Rank | Framework | Rating | Bundle | SSR | Charts | Real-time | Best For |
|------|-----------|--------|--------|-----|--------|-----------|----------|
| 🥇 | **SvelteKit** | **9/10** | 10-30KB | ✅ Built-in | ✅ Any lib | ✅ WS | **Our use case** |
| 🥈 | React+Vite+ShadCN | 8/10 | 150KB+ | ❌ Needs setup | ✅ Recharts | ✅ socket.io | React-experienced teams |
| 🥉 | Vue+Vite | 7.5/10 | ~50KB | ✅ Nuxt | ✅ ECharts | ✅ WS | Balanced choice |
| 4 | HTMX+Alpine | 6/10 | ~30KB | ✅ Server | ⚠️ Limited | ⚠️ SSE | Simple dashboards |
| 5 | Next.js | 5/10 | 200KB+ | ✅ Best | ✅ Full | ✅ WS | SEO-heavy public sites |

### ✅ Final Frontend Recommendation: SvelteKit

**Alternative:** If the team has strong React experience and prefers the larger ecosystem, **React + Vite + ShadCN + Tailwind** is the recommended fallback. The trade-off is larger bundle size and no built-in SSR.

---

# 4. Database Strategy

## 4.1 On-Device (Raspberry Pi) — SQLite

| Aspect | Details |
|--------|---------|
| **Why SQLite** | Zero configuration, serverless, single-file database |
| **RAM Usage** | ~20-50MB |
| **Write Performance** | ~50K inserts/sec (sufficient for waste entries) |
| **Read Performance** | Excellent for analytics queries with proper indexing |
| **Offline Support** | Works without network; no separate process |
| **Backup** | Single file copy; simple automated backup |

**Schema Design Considerations:**
- WAL mode for concurrent reads during analytics
- Proper indexing on `student_id`, `timestamp`, `meal_type` for fast queries
- Partitioning strategy: archive old data to compressed files
- Full-text search for student lookup

## 4.2 Cache & Real-time Layer — Redis

| Aspect | Details |
|--------|---------|
| **Why Redis** | Session management, WebSocket state, rule engine state cache |
| **RAM Usage** | ~30-50MB (configurable maxmemory) |
| **Use Cases** | API rate limiting, live dashboard state, rule evaluation cache |
| **Alternative** | If RAM is too tight, use Python `dict`-based caching with SQLite fallback |

## 4.3 Future Centralized — PostgreSQL

| Aspect | Details |
|--------|---------|
| **When** | When scaling to multi-Pi centralized dashboard |
| **Where** | Cloud VPS or central campus server |
| **Why** | Multi-device aggregation, complex joins, JSON queries |
| **Migration** | SQLite → PostgreSQL migration scripts built into the system from Phase 1 |

### ✅ Database Strategy: SQLite (edge) + Redis (cache) + PostgreSQL (future central)

---

# 5. Public Internet Exposure Strategy

## 5.1 Comparison

| Option | Cost | RAM on Pi | Complexity | Security | Custom Domain |
|--------|------|-----------|------------|----------|---------------|
| **Cloudflare Tunnel** | Free | ~20MB | Low | ✅ No open ports, DDoS protection | ✅ Yes |
| **Tailscale Funnel** | Free | ~30MB | Low | ✅ WireGuard-based | ⚠️ Limited |
| **ngrok** | Freemium | ~15MB | Very Low | ⚠️ Random URL on free tier | ❌ Paid only |
| **VPS Reverse Proxy** | $5-10/mo | 0 (off-Pi) | Medium | ✅ Full control | ✅ Yes |

### ✅ Recommendation: Cloudflare Tunnel

**Why:**
- **Free** — no recurring cost
- **No open ports** — Pi never exposes ports to the internet
- **DDoS protection** — Cloudflare absorbs attacks
- **Custom domain** — e.g., `mess.yourcollege.edu.in`
- **Low resource usage** — `cloudflared` daemon uses ~20MB RAM
- **Easy setup** — one-time configuration

**Setup Flow:**
```
1. Register domain on Cloudflare
2. Install cloudflared on Raspberry Pi
3. Authenticate: cloudflared tunnel login
4. Create tunnel: cloudflared tunnel create mess-dashboard
5. Configure: map tunnel to localhost:80 (Nginx)
6. Run: cloudflared tunnel run mess-dashboard
```

---

# 6. System Architecture

## 6.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    RASPBERRY PI                          │
│                                                         │
│  ┌──────────────┐    ┌──────────────────────────────┐   │
│  │  ML Pipeline │    │     FastAPI Application       │   │
│  │  (Python)    │───▶│                              │   │
│  │              │    │  ┌────────────────────────┐  │   │
│  │ - Plate Det. │    │  │   REST API Layer        │  │   │
│  │ - Weight     │    │  │   /api/v1/*             │  │   │
│  │ - User ID    │    │  └────────────────────────┘  │   │
│  │ - Food Items │    │  ┌────────────────────────┐  │   │
│  └──────────────┘    │  │   WebSocket Server      │  │   │
│                      │  │   /ws/*                 │  │   │
│                      │  └────────────────────────┘  │   │
│                      │  ┌────────────────────────┐  │   │
│                      │  │   Rule Engine           │  │   │
│                      │  │   Event → Evaluate →   │  │   │
│                      │  │   Action                │  │   │
│                      │  └────────────────────────┘  │   │
│                      │  ┌────────────────────────┐  │   │
│                      │  │   Analytics Engine      │  │   │
│                      │  │   Aggregation + Scoring │  │   │
│                      │  └────────────────────────┘  │   │
│                      │  ┌────────────────────────┐  │   │
│                      │  │   Notification Engine   │  │   │
│                      │  │   Email + Alerts        │  │   │
│                      │  └────────────────────────┘  │   │
│                      └──────────────────────────────┘   │
│                                    │                    │
│                      ┌────────────┴────────────┐       │
│                      │                         │       │
│                ┌─────┴─────┐          ┌───────┴──────┐ │
│                │  SQLite   │          │    Redis      │ │
│                │  (Primary)│          │   (Cache)     │ │
│                └───────────┘          └───────────────┘ │
│                                                         │
│  ┌──────────────┐    ┌──────────────┐                   │
│  │   Nginx      │    │ Cloudflare  │                   │
│  │   (Reverse   │    │  Tunnel      │                   │
│  │    Proxy)    │    │ (cloudflared)│                   │
│  └──────┬───────┘    └──────┬───────┘                   │
│         │                    │                           │
└─────────┼────────────────────┼───────────────────────────┘
          │                    │
          ▼                    ▼
   ┌──────────────┐    ┌──────────────┐
   │  SvelteKit   │    │   Public     │
   │  Dashboard   │    │   Internet   │
   │  (Static/SSR)│    │   (College   │
   └──────────────┘    │   Authority) │
                       └──────────────┘
```

## 6.2 Data Flow

```
[ML Detection]
     │
     ▼
[POST /api/v1/waste/entries] ──▶ [Validation (Pydantic)]
     │                                    │
     ▼                                    ▼
[Store in SQLite] ──────────────▶ [Rule Engine Evaluation]
     │                                    │
     │                          ┌─────────┼─────────┐
     │                          ▼         ▼         ▼
     │                     [Warning]  [Penalty]  [Alert]
     │                          │         │         │
     │                          ▼         ▼         ▼
     │                     [Notification Engine]
     │                          │
     │                    ┌─────┼─────┐
     │                    ▼     ▼     ▼
     │                 [Email] [WS] [Dashboard]
     │
     ▼
[Analytics Engine (Background)]
     │
     ├──▶ Aggregation (hourly/daily)
     ├──▶ Sustainability Scoring
     ├──▶ Trend Computation
     └──▶ Report Generation
```

## 6.3 Service Architecture on Pi

```
Docker Compose:
├── fastapi-app        (Main API + Rule Engine + Analytics)  Port: 8000
├── celery-worker      (Background Tasks: Email, Reports, Analytics) 
├── redis              (Cache + Message Broker)               Port: 6379
├── nginx              (Reverse Proxy + Static Files)         Port: 80/443
├── cloudflared        (Public Internet Tunnel)
└── ml-pipeline        (Computer Vision + Detection)         Internal

Volumes:
├── sqlite-data        (/data/cleanplates.db)
├── redis-data         (/data/redis/)
├── uploads            (/data/uploads/)
└── logs               (/var/log/cleanplates/)
```

---

# 7. Phase-Wise Implementation Plan

## Phase 1: Foundation & Core API (Weeks 1-2)

### Objectives
- Establish project scaffold, database, and core CRUD APIs
- Set up development environment and deployment pipeline

### Tasks

#### 1.1 Project Scaffold
- [ ] Initialize FastAPI project with async structure
- [ ] Configure `pyproject.toml` with dependencies
- [ ] Set up project directory structure (routes, models, services, schemas)
- [ ] Configure `alembic` for database migrations
- [ ] Set up `pytest` with `pytest-asyncio` for testing
- [ ] Configure `ruff` for linting and `mypy` for type checking
- [ ] Create `.env` configuration system with Pydantic Settings

#### 1.2 Database Layer
- [ ] Design SQLite schema with proper indexing
- [ ] Create SQLAlchemy async models for all core entities:
  - `devices` — Raspberry Pi device identity
  - `institutions` — Institution configuration
  - `mess_units` — Mess/block configuration
  - `students` — Student profiles
  - `meals` — Meal session definitions
  - `waste_entries` — Waste log entries
  - `food_items` — Food catalog
- [ ] Set up Alembic migration system
- [ ] Create seed data scripts for development
- [ ] Implement repository pattern for data access

#### 1.3 Core API Endpoints
- [ ] Device Management APIs
  - `POST /api/v1/devices` — Register device
  - `GET /api/v1/devices/{id}` — Get device info
  - `PATCH /api/v1/devices/{id}` — Update device
  - `GET /api/v1/devices/{id}/health` — Device health
- [ ] Student Management APIs
  - `POST /api/v1/students` — Create student
  - `GET /api/v1/students` — List students (paginated, filtered)
  - `GET /api/v1/students/{id}` — Get student details
  - `PATCH /api/v1/students/{id}` — Update student
- [ ] Waste Entry APIs
  - `POST /api/v1/waste/entries` — Log waste entry
  - `GET /api/v1/waste/entries` — List entries (paginated, filtered)
  - `GET /api/v1/waste/entries/{id}` — Get entry details
- [ ] Configuration APIs
  - `GET /api/v1/config/institution` — Get institution config
  - `PATCH /api/v1/config/institution` — Update institution config
  - `GET /api/v1/config/device` — Get device config

#### 1.4 Authentication & Authorization
- [ ] JWT token generation and validation
- [ ] Role-based access control middleware
- [ ] API key authentication for ML pipeline
- [ ] User model and role definitions

#### 1.5 Development Infrastructure
- [ ] Docker Compose for local development
- [ ] Dockerfile for Raspberry Pi (ARM64)
- [ ] Nginx configuration
- [ ] Health check endpoints
- [ ] Logging configuration (structured JSON logging)

### Deliverables
- Working FastAPI application with core CRUD APIs
- SQLite database with migrations
- Docker setup for development
- API documentation (auto-generated Swagger/OpenAPI)
- Basic authentication system

---

## Phase 2: ML Integration API Layer (Week 3)

### Objectives
- Create API endpoints for ML pipeline to push detected data
- Handle offline scenarios and data synchronization

### Tasks

#### 2.1 ML Data Ingestion APIs
- [ ] `POST /api/v1/ml/detect` — Accept plate detection payload
  ```json
  {
    "user_id": "string",
    "user_image": "base64 (optional)",
    "plate_image": "base64",
    "weight_grams": 150.5,
    "food_items": ["rice", "dal"],
    "meal_type": "lunch",
    "confidence_score": 0.95,
    "timestamp": "2026-05-09T12:30:00Z",
    "device_id": "string",
    "metadata": {}
  }
  ```
- [ ] `POST /api/v1/ml/identify` — Accept user identification
- [ ] `POST /api/v1/ml/sync` — Bulk sync endpoint for offline data
- [ ] `POST /api/v1/ml/heartbeat` — ML pipeline health status

#### 2.2 Data Processing Pipeline
- [ ] Validate incoming ML data with Pydantic models
- [ ] Enrich waste entries with computed fields (session, period, etc.)
- [ ] Resolve student identity (face ID → student record)
- [ ] Classify waste severity based on thresholds
- [ ] Store processed data in SQLite
- [ ] Publish event to rule engine queue

#### 2.3 Offline & Sync Mechanism
- [ ] Local SQLite queue for outgoing sync (if centralized DB exists)
- [ ] Incoming bulk sync API for offline ML data
- [ ] Conflict resolution strategy (last-write-wins with timestamps)
- [ ] Sync status tracking and reporting

#### 2.4 Edge Processing
- [ ] Edge-side validation rules
- [ ] Local rule execution even when offline
- [ ] Queue management for notifications when offline
- [ ] Data integrity checks on sync

### Deliverables
- ML pipeline API endpoints
- Data processing pipeline
- Offline sync mechanism
- Edge validation system

---

## Phase 3: Rule Engine (Weeks 4-5)

### Objectives
- Build the configurable, dynamic rule engine — the heart of the platform

### Tasks

#### 3.1 Rule Definition Schema
- [ ] Design JSON-based rule schema:
  ```json
  {
    "rule_id": "string",
    "name": "Daily Waste Threshold",
    "description": "Trigger warning when waste exceeds limit",
    "priority": "high",
    "type": "threshold",
    "active": true,
    "conditions": [
      {
        "field": "waste_grams",
        "operator": "greater_than",
        "value": 150
      }
    ],
    "time_constraints": {
      "window": "per_meal",
      "period": "daily"
    },
    "scope": {
      "target": "student",
      "filters": {}
    },
    "actions": [
      {
        "type": "generate_warning",
        "params": { "level": "yellow" }
      },
      {
        "type": "send_email",
        "params": { "template": "warning" }
      }
    ]
  }
  ```
- [ ] Rule CRUD APIs
  - `POST /api/v1/rules` — Create rule
  - `GET /api/v1/rules` — List rules (filterable)
  - `GET /api/v1/rules/{id}` — Get rule details
  - `PATCH /api/v1/rules/{id}` — Update rule
  - `DELETE /api/v1/rules/{id}` — Deactivate rule
  - `POST /api/v1/rules/{id}/test` — Test rule with sample data

#### 3.2 Event Processor
- [ ] Event bus implementation (in-process + Redis pub/sub)
- [ ] Event types: `waste_entry_created`, `threshold_crossed`, `warning_issued`, etc.
- [ ] Event subscription system for rule evaluation
- [ ] Event persistence for audit trail

#### 3.3 Rule Evaluator
- [ ] Condition matcher engine:
  - Numeric comparisons (>, <, =, >=, <=, between)
  - String matching (equals, contains, regex)
  - Time window evaluation (within X hours/days)
  - Frequency counting (occurs N times within period)
  - Trend detection (increasing/decreasing over period)
  - Aggregate evaluation (average, sum, count within scope)
- [ ] Scope resolver (institution, hostel, mess, branch, year, student)
- [ ] Priority-based rule execution order
- [ ] Rule conflict detection and resolution

#### 3.4 Action Executor
- [ ] Action types implementation:
  - `generate_warning` — Create warning record
  - `send_email` — Queue email notification
  - `increase_penalty` — Add penalty points
  - `trigger_escalation` — Escalate to higher authority
  - `notify_admin` — Dashboard + email alert
  - `lock_privileges` — Restrict student access
  - `generate_report_entry` — Add to report queue
  - `create_audit_log` — Log the action
  - `classify_student` — Update student risk classification
- [ ] Action result tracking
- [ ] Action rollback for simulation mode

#### 3.5 Rule Chaining
- [ ] Chain execution: Warning → Escalation → Penalty → Admin Review
- [ ] Chain validation (prevent circular chains)
- [ ] Chain visualization data API

#### 3.6 Rule Builder API
- [ ] Condition builder API (AND/OR logic groups)
- [ ] Available fields metadata API (for UI dropdowns)
- [ ] Available operators metadata API
- [ ] Available actions metadata API
- [ ] Rule validation API (syntax + logic)
- [ ] Rule simulation API (test against historical data)

#### 3.7 Rule Audit System
- [ ] Rule execution logs
- [ ] Rule modification history
- [ ] Admin change tracking
- [ ] Trigger source recording

### Deliverables
- Complete rule engine with CRUD, evaluation, and execution
- Event processing pipeline
- Action execution system with all action types
- Rule chaining mechanism
- Rule builder API for dynamic rule creation
- Rule simulation and audit logging

---

## Phase 4: Analytics Engine (Weeks 6-7)

### Objectives
- Build the intelligence layer — aggregation, scoring, trend analysis, comparisons

### Tasks

#### 4.1 Aggregation Pipeline
- [ ] Hourly waste aggregation (background task)
- [ ] Daily waste aggregation
- [ ] Weekly waste aggregation
- [ ] Monthly waste aggregation
- [ ] Per-student aggregation
- [ ] Per-food-item aggregation
- [ ] Per-meal-type aggregation
- [ ] Per-branch/hostel aggregation
- [ ] Materialized views in SQLite for fast dashboard queries

#### 4.2 Trend Analysis
- [ ] Daily trend computation (compare to previous day/week/month)
- [ ] Moving average calculation (7-day, 30-day)
- [ ] Trend direction detection (improving, stable, worsening)
- [ ] Anomaly detection (spike identification)
- [ ] Seasonal pattern detection

#### 4.3 Comparison Analytics
- [ ] Branch vs Branch comparison
- [ ] Hostel vs Hostel comparison
- [ ] Week vs Week comparison
- [ ] Month vs Month comparison
- [ ] Meal vs Meal comparison
- [ ] Food vs Food comparison
- [ ] Comparison ranking system

#### 4.4 Peak Waste Analytics
- [ ] Peak waste hour detection
- [ ] Peak waste meal identification
- [ ] Peak waste weekday analysis
- [ ] Seasonal waste pattern tracking

#### 4.5 Sustainability Scoring System
- [ ] Score calculation algorithm:
  - Average waste weight (40%)
  - Improvement trend (25%)
  - Violation frequency (20%)
  - Consistency score (10%)
  - Meal participation (5%)
- [ ] Score levels: Excellent (90-100), Good (75-89), Average (50-74), Poor (<50)
- [ ] Batch scoring job (daily recalculation)
- [ ] Real-time score updates on new waste entries

#### 4.6 Dynamic Filter System
- [ ] Time filters (today, yesterday, 7d, 30d, semester, custom)
- [ ] Institution filters (campus, hostel, mess, floor, wing)
- [ ] Student filters (name, roll, branch, year, status)
- [ ] Food filters (meal type, category, specific item)
- [ ] Filter composition (combine multiple filters)
- [ ] Filter serialization (save/load filter presets)

#### 4.7 Analytics API Endpoints
- [ ] `GET /api/v1/analytics/overview` — Global KPIs
- [ ] `GET /api/v1/analytics/trends` — Trend data
- [ ] `GET /api/v1/analytics/comparisons` — Comparison data
- [ ] `GET /api/v1/analytics/peaks` — Peak waste data
- [ ] `GET /api/v1/analytics/sustainability` — Sustainability scores
- [ ] `GET /api/v1/analytics/top-waste-contributors` — Student ranking
- [ ] `GET /api/v1/analytics/food-waste-distribution` — Food analytics
- [ ] `GET /api/v1/analytics/meal-distribution` — Meal analytics

#### 4.8 Background Processing
- [ ] Celery/ARQ worker setup
- [ ] Scheduled tasks (aggregation, scoring, cleanup)
- [ ] Task monitoring and failure recovery
- [ ] Task priority management

### Deliverables
- Complete analytics engine with all aggregation types
- Sustainability scoring system
- Dynamic filter system
- Analytics API endpoints
- Background task processing

---

## Phase 5: Real-Time & Notification System (Week 8)

### Objectives
- Implement WebSocket-based real-time updates
- Build the notification and email engine

### Tasks

#### 5.1 WebSocket Server
- [ ] FastAPI WebSocket endpoints
  - `/ws/dashboard` — Live dashboard updates
  - `/ws/monitoring` — Live feed panel
  - `/ws/alerts` — Real-time alert stream
  - `/ws/device/{id}` — Device-specific updates
- [ ] Connection management (connect, disconnect, heartbeat)
- [ ] Authentication on WebSocket connections
- [ ] Room-based broadcasting (by device, by mess, by role)
- [ ] Message types: `waste_entry`, `warning`, `penalty`, `alert`, `rule_executed`, `device_status`

#### 5.2 Live Dashboard Updates
- [ ] Push new waste entries in real-time
- [ ] Push warning/penalty events
- [ ] Push rule execution results
- [ ] Push device status changes
- [ ] KPI card value updates
- [ ] Live feed panel messages

#### 5.3 Email Notification Engine
- [ ] SMTP configuration system
- [ ] Email sending service (async with `aiosmtplib`)
- [ ] Email queue management (retry, priority)
- [ ] Email template engine with Jinja2:
  - Warning email template
  - Penalty email template
  - Appreciation email template
  - Awareness email template
  - Operational alert template
  - Device offline template
  - Custom template support
- [ ] Template CRUD APIs:
  - `POST /api/v1/templates` — Create template
  - `GET /api/v1/templates` — List templates
  - `PATCH /api/v1/templates/{id}` — Update template
  - `POST /api/v1/templates/{id}/preview` — Preview with sample data

#### 5.4 Notification System
- [ ] Notification model (type, priority, channel, recipient, content, status)
- [ ] Notification CRUD APIs
- [ ] Notification dispatching (email, dashboard, browser push)
- [ ] Notification preferences per user/role
- [ ] Broadcast notification (admin → all students in hostel)
- [ ] Notification history and tracking

#### 5.5 Alert Management
- [ ] Alert priority system (critical, high, medium, low)
- [ ] Escalation timer system (alert → escalate if not acknowledged)
- [ ] Alert acknowledgment workflow
- [ ] Alert dashboard API

### Deliverables
- WebSocket server with real-time updates
- Email notification engine with template system
- Alert management system
- Notification dispatching and tracking

---

## Phase 6: Frontend Dashboard (Weeks 9-12)

### Objectives
- Build the complete web dashboard with all views

### Tasks

#### 6.1 Frontend Project Setup (Week 9)
- [ ] Initialize SvelteKit project with TypeScript
- [ ] Configure Tailwind CSS
- [ ] Set up ShadCN-Svelte component library
- [ ] Configure API client (fetch wrapper with auth)
- [ ] Set up WebSocket client
- [ ] Create layout system (sidebar, header, content)
- [ ] Implement auth flow (login, token management)
- [ ] Set up charting library (Chart.js / D3 / Recharts via svelte wrapper)

#### 6.2 Global Overview Dashboard (Week 9)
- [ ] KPI cards section:
  - Total Waste Today/Week/Month
  - Average Daily Waste
  - Waste Reduction %
  - Peak Waste Time
  - Total Active Students
  - Students Under Warning/Penalty
  - Most Improved Students
  - High Risk Students
  - Active/Offline Devices
  - Alerts/Rule Violations Today
- [ ] Weekly Waste Trend chart
- [ ] Monthly Waste Comparison chart
- [ ] Branch-wise Waste Heatmap
- [ ] Meal Type Distribution chart
- [ ] Food Item Waste Distribution chart

#### 6.3 Live Monitoring Dashboard (Week 10)
- [ ] Real-time waste entry feed (WebSocket)
- [ ] Live event stream panel
- [ ] Real-time KPI updates
- [ ] Active session monitoring
- [ ] Device status grid
- [ ] Alert feed panel

#### 6.4 Analytics Dashboard (Week 10-11)
- [ ] Dynamic filter system UI
  - Time filter component
  - Institution filter component
  - Student filter component
  - Food filter component
  - Filter preset management
- [ ] Top Waste Contributors table
- [ ] Most Wasted Food Items chart
- [ ] Improvement Tracking view
- [ ] Smart Comparison Analytics (side-by-side)
- [ ] Peak Waste Analytics (heatmaps, timelines)
- [ ] Sustainability Analytics dashboard
- [ ] Branch Analytics dashboard
- [ ] Food Analytics dashboard
- [ ] Meal Analytics dashboard

#### 6.5 Student Intelligence Dashboard (Week 11)
- [ ] Student list with search/filter/sort
- [ ] Student profile page:
  - Identity information
  - Waste statistics
  - Behavioral metrics
  - Timeline analytics
- [ ] Student status indicator (Green/Yellow/Orange/Red)
- [ ] Student waste history timeline
- [ ] Student improvement tracking chart
- [ ] Student comparison tool

#### 6.6 Admin Configuration Dashboard (Week 12)
- [ ] Institution settings page
- [ ] Device identity configuration
- [ ] Threshold configuration
- [ ] Meal timing configuration
- [ ] Branch/Hostel mapping
- [ ] Notification policy settings
- [ ] Email template management
- [ ] Role and permission management
- [ ] Dynamic rule builder UI:
  - Visual condition builder (IF [field] [operator] [value])
  - AND/OR logic grouping
  - Action selection
  - Scope targeting
  - Rule simulation/testing
- [ ] System policy configuration

#### 6.7 Additional Pages
- [ ] Warning & Penalty management
- [ ] Notification center
- [ ] Report generation & download
- [ ] Device management
- [ ] Audit log viewer
- [ ] Settings page

### Deliverables
- Complete SvelteKit dashboard application
- All dashboard views implemented
- Real-time updates via WebSocket
- Dynamic filter system
- Visual rule builder
- Responsive design for desktop and tablet

---

## Phase 7: Reporting & Advanced Features (Weeks 13-14)

### Objectives
- Build report generation system and advanced operational features

### Tasks

#### 7.1 Report Generation
- [ ] PDF report generation (WeasyPrint)
  - Daily waste report
  - Weekly summary report
  - Monthly analysis report
  - Branch comparison report
  - Student history report
- [ ] CSV export for all data tables
- [ ] Excel report generation (OpenPyXL)
- [ ] Report scheduling (daily/weekly/monthly auto-generation)
- [ ] Report storage and download API
- [ ] Report delivery via email

#### 7.2 Report API Endpoints
- [ ] `POST /api/v1/reports/generate` — Generate report
- [ ] `GET /api/v1/reports` — List generated reports
- [ ] `GET /api/v1/reports/{id}/download` — Download report file
- [ ] `DELETE /api/v1/reports/{id}` — Delete report
- [ ] `GET /api/v1/reports/schedules` — List scheduled reports
- [ ] `POST /api/v1/reports/schedules` — Create report schedule

#### 7.3 Device Health Monitoring
- [ ] CPU usage tracking
- [ ] RAM usage tracking
- [ ] Temperature monitoring
- [ ] Storage usage monitoring
- [ ] Network connectivity status
- [ ] Service health checks
- [ ] Device health history API
- [ ] Device health dashboard widget

#### 7.4 Auto-Recovery System
- [ ] Service watchdog (auto-restart crashed services)
- [ ] Cache recovery on restart
- [ ] Failed sync recovery
- [ ] Database integrity checks on startup
- [ ] Graceful degradation modes

#### 7.5 Offline Mode Enhancement
- [ ] Offline indicator on dashboard
- [ ] Sync status display
- [ ] Pending notifications queue
- [ ] Data freshness indicators
- [ ] Manual sync trigger

### Deliverables
- Report generation system (PDF, CSV, Excel)
- Scheduled reports
- Device health monitoring
- Auto-recovery system
- Enhanced offline mode

---

## Phase 8: Deployment, Security & Production (Weeks 15-16)

### Objectives
- Production hardening, security, deployment automation

### Tasks

#### 8.1 Docker & Deployment
- [ ] Production Docker Compose configuration
- [ ] Multi-stage Dockerfile (smaller final image)
- [ ] ARM64-optimized base images
- [ ] Docker health checks for all services
- [ ] Docker log management (log rotation)
- [ ] Backup automation (SQLite file, config, uploads)
- [ ] Deployment script (one-command update)

#### 8.2 Nginx Configuration
- [ ] Reverse proxy to FastAPI
- [ ] Static file serving for SvelteKit build
- [ ] SSL/TLS with Let's Encrypt (or self-signed for local)
- [ ] Gzip compression
- [ ] Rate limiting
- [ ] Security headers

#### 8.3 Cloudflare Tunnel Setup
- [ ] Install and configure `cloudflared`
- [ ] Create and authenticate tunnel
- [ ] Map tunnel to Nginx
- [ ] Set up as systemd service (auto-start on boot)
- [ ] Custom domain DNS configuration
- [ ] Test public access

#### 8.4 Security Hardening
- [ ] RBAC implementation:
  - Super Admin (full access)
  - Institution Admin (institution-level)
  - Mess Admin (mess-level operations)
  - Analytics Viewer (read-only analytics)
  - Staff Operator (entry logging only)
- [ ] API rate limiting
- [ ] Input sanitization and validation
- [ ] CORS configuration
- [ ] CSRF protection
- [ ] SQL injection prevention (parameterized queries via SQLAlchemy)
- [ ] XSS prevention
- [ ] Secure headers
- [ ] Secret management (.env, not in code)

#### 8.5 Audit Logging
- [ ] Login activity logging
- [ ] Rule change logging
- [ ] Configuration change logging
- [ ] Report generation logging
- [ ] API access logging
- [ ] Audit log search and filter API
- [ ] Audit log retention policy

#### 8.6 Performance Optimization
- [ ] Database query optimization
- [ ] API response caching
- [ ] Static asset compression
- [ ] WebSocket message batching
- [ ] Background task priority tuning
- [ ] Memory usage monitoring and optimization

#### 8.7 Documentation
- [ ] API documentation (auto-generated + custom)
- [ ] Deployment guide (step-by-step Pi setup)
- [ ] Configuration guide
- [ ] Rule engine user guide
- [ ] Troubleshooting guide
- [ ] Architecture decision records

### Deliverables
- Production-ready Docker deployment
- Public internet access via Cloudflare Tunnel
- Full security hardening
- Complete audit logging
- Performance optimization
- Comprehensive documentation

---

# 8. Technology Stack Summary

## Final Recommended Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Backend Framework** | FastAPI | 0.110+ | REST API + WebSocket server |
| **ASGI Server** | Uvicorn | 0.27+ | Production ASGI server |
| **ORM** | SQLAlchemy (async) | 2.0+ | Database models and queries |
| **Migrations** | Alembic | 1.13+ | Database schema management |
| **Validation** | Pydantic | 2.0+ | Data validation and serialization |
| **Background Tasks** | ARQ (async Redis queue) | 0.25+ | Email, analytics, scheduled jobs |
| **Database** | SQLite | 3.42+ | Primary edge storage |
| **Cache** | Redis | 7.2+ | Cache, sessions, pub/sub |
| **Email** | aiosmtplib + Jinja2 | — | Async email with templates |
| **Reports** | WeasyPrint + OpenPyXL | — | PDF and Excel generation |
| **Frontend** | SvelteKit | 2.0+ | Dashboard SPA with SSR |
| **CSS** | Tailwind CSS | 3.4+ | Utility-first styling |
| **UI Components** | shadcn-svelte | — | Accessible component library |
| **Charts** | Chart.js / D3 | — | Data visualization |
| **WebSocket Client** | Native WebSocket API | — | Real-time updates |
| **HTTP Client** | ky / fetch wrapper | — | API communication |
| **Reverse Proxy** | Nginx | 1.25+ | Static files, SSL, proxy |
| **Containerization** | Docker + Docker Compose | — | Service management |
| **Public Access** | Cloudflare Tunnel | — | Secure internet exposure |
| **Process Manager** | systemd | — | Service auto-restart |
| **ML Pipeline** | Python (OpenCV, etc.) | — | Plate detection, weight, ID |
| **Language** | Python 3.11+ / TypeScript | — | Backend / Frontend |

## Python Dependencies (Core)

```toml
[project]
name = "cleanplates"
version = "0.1.0"
requires-python = ">=3.11"

[project.dependencies]
fastapi = ">=0.110.0"
uvicorn = {extras = ["standard"], version = ">=0.27.0"}
sqlalchemy = {extras = ["asyncio"], version = ">=2.0"}
aiosqlite = ">=0.19.0"
alembic = ">=1.13.0"
pydantic = ">=2.0"
pydantic-settings = ">=2.0"
python-jose = {extras = ["cryptography"], version = ">=3.3"}
passlib = {extras = ["bcrypt"], version = ">=1.7"}
python-multipart = ">=0.0.6"
aiosmtplib = ">=3.0"
jinja2 = ">=3.1"
redis = {extras = ["hiredis"], version = ">=5.0"}
arq = ">=0.25"
weasyprint = ">=60"
openpyxl = ">=3.1"
csv = ">=1.0"
httpx = ">=0.27"
```

---

# 9. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Pi runs out of RAM with ML + API | Medium | High | Monitor memory; use swap as fallback; Redis maxmemory limit |
| SQLite write contention under load | Low | Medium | WAL mode; batch writes; async operations |
| Cloudflare Tunnel downtime | Low | Medium | Local network access still works; tunnel auto-reconnects |
| SD card corruption on Pi | Medium | High | Read-only root filesystem; log to RAM; regular backups |
| ML pipeline crashes | Medium | High | Separate process; auto-restart via systemd; health monitoring |
| Security breach via public tunnel | Low | Critical | Cloudflare DDoS protection; JWT auth; rate limiting; RBAC |

---

# 10. Success Metrics

| Metric | Target |
|--------|--------|
| API response time (CRUD) | < 100ms |
| API response time (analytics) | < 500ms |
| WebSocket message latency | < 50ms |
| RAM usage (total on Pi) | < 2GB (leaving room for ML) |
| Offline data retention | 7 days without internet |
| Dashboard initial load | < 2 seconds |
| Email delivery time | < 30 seconds |
| Rule evaluation time | < 200ms per event |
| Report generation time | < 10 seconds |
| System uptime | 99.5%+ |

---

# 11. Future Roadmap (Post-Phase 8)

| Feature | Timeline | Description |
|---------|----------|-------------|
| Multi-Pi Central Dashboard | Month 5 | Centralized PostgreSQL + dashboard for all mess units |
| Mobile App | Month 6 | React Native app for students and admins |
| SMS Notifications | Month 5 | Twilio integration for SMS alerts |
| Waste Forecasting ML | Month 6-7 | Predict tomorrow's waste using historical patterns |
| High Risk Student Prediction | Month 7 | ML model to predict students likely to cross thresholds |
| Food Optimization Engine | Month 8 | Predict required food quantities and reduce waste |
| Sustainability Gamification | Month 8 | Leaderboards, badges, achievements for students |
| Multi-Institution Support | Month 9 | SaaS model for deploying across institutions |
| API Rate Limiting Dashboard | Month 4 | Visual API usage monitoring |
| Custom Webhook System | Month 5 | Outgoing webhooks for third-party integrations |

---

*Document generated: May 9, 2026*
*Project: Smart Mess Waste Intelligence Platform (CleanPlates)*
*Architecture: API-First, Edge Computing, Real-Time Analytics*