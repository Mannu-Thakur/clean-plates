# CleanPlates — Plans Index

This directory contains the complete implementation blueprint for the CleanPlates platform. All architectural decisions are finalized here. The coding phase should reference these docs exclusively — no design changes should be needed after this point.

---

## Document Index

| # | File | Contents | When to Read |
|---|------|----------|--------------|
| 01 | `01-models.md` | 23 SQLAlchemy models — all columns, types, constraints, indexes, and relationships | Before creating any model or migration |
| 02 | `02-controllers.md` | 18 controller modules + 3 internal services — every function with Input→Output→Work | Before implementing any route handler or service |
| 03 | `03-routes.md` | All ~110 API endpoints — method, path, roles, controller function mapping | Before creating any router file |
| 04 | `04-middlewares.md` | All middleware, auth dependencies, RBAC, rate limits, Pydantic Settings | Before setting up app core or any dependency |
| 05 | `05-schemas.md` | All Pydantic v2 schemas — every request body and response model (16 schema files) | Before writing any schema file |
| 06 | `06-phase-wise-plan.md` | 10 phases with exact files, functions, and migration references per phase | Primary coding guide — follow phase order strictly |
| 07 | `07-project-structure.md` | Complete directory tree for backend + frontend + Docker | Before creating any new file to know where it goes |

---

## Source Docs (Reference Only)

Located in `docs/praposed-imp/pages/`:

| File | Page |
|------|------|
| `01-login.md` | Auth flow, class diagram, state diagram |
| `02-overview-dashboard.md` | KPI structure, WebSocket events |
| `03-live-monitoring.md` | Real-time feed, alert panel |
| `04-analytics.md` | Dynamic filter system, chart types |
| `05-students-list.md` | ID-first mapping, CSV import |
| `06-student-intelligence.md` | Student profile, scoring, timeline |
| `07-warnings-penalties.md` | Warning lifecycle, escalation, penalty |
| `08-rule-engine.md` | Rule schema, condition matching, simulation |
| `09-notifications.md` | Channels, templates, broadcast |
| `10-reports.md` | Report types, scheduling, export formats |
| `11-devices.md` | Device health, heartbeat, remote commands |
| `12-configuration.md` | Config sections, template management |
| `13-settings.md` | User management, backup, maintenance |
| `14-audit-log.md` | Audit event types, filters, timeline |

---

## Key Architectural Decisions (Locked)

| Decision | Choice | Reason |
|----------|--------|--------|
| Backend | FastAPI (Python) | Native async, same runtime as ML, WebSocket built-in |
| ORM | SQLAlchemy 2.0 async | Type-safe, async-native, Alembic migrations |
| Database | SQLite (edge) | Zero-config, offline-capable, single file |
| Cache | Redis | Session store, rate limiting, pub/sub for event bus |
| Background jobs | ARQ | Async Redis Queue — lighter than Celery for Pi |
| Frontend | SvelteKit | Smallest bundle, built-in SSR, Vite-powered |
| Public access | Cloudflare Tunnel | Free, no open ports, DDoS protection |
| Student identity | ID-first mapping | device_id generated at edge, admin maps to student later |
| Rule storage | JSON columns | Dynamic conditions/actions without schema migrations |
| Config storage | `system_config` key-value table | No schema change needed to add config keys |
| Audit | Explicit service calls | Accurate before/after state capture vs. blanket middleware |

---

## Coding Agent Instructions

1. **Start at Phase 1** in `06-phase-wise-plan.md` and complete each phase fully before starting the next
2. For each file to create, find its spec in the referenced plan doc section
3. **Models first** in each phase → migration → routes → controller → service → schemas (in that order)
4. Wire audit logging in every service that modifies data (reference `02-controllers.md §14`)
5. After Phase 3, the rule engine event bus must be wired into `waste_service` before Phase 4 begins
6. Frontend (Phase 9) references each page's `docs/praposed-imp/pages/NN-*.md` for UI component details
7. Never hardcode threshold values — always read from `config_service.get_config("thresholds")`
8. Student status and sustainability score are **derived** — always recomputed via services, never set directly by routes
