# Worked SDD scenarios (behavioral calibration)

Nine scenarios drawn verbatim from the tesslio tile's evaluation set. They are gold examples of *judgment* — when to interview vs. write, what good gap analysis looks like, when the trivial-change exception applies, and how to handle drift and discovered requirements. Read these to calibrate behavior on real cases.

---

## 1. one-question-enforcement — interview prep, not a spec
**Context:** webhook system requirement gathering. **Task:** analyze an existing webhook spec and produce an interview-prep document.
**In scope:** external URL notification, customer-configurable endpoints, event types (user signup, payment success), basic delivery. **Unspecified:** complete event list, reliability guarantees, authentication, payload structure, event filtering, webhook management, scale, error handling.
**Behavior:** produce `webhook-interview-prep.md` with ~15 numbered, single-topic, self-contained questions spanning event triggering, subscription models, authentication, payload structure, retry behavior, customer notification, testing, logging, management, scale, size limits, synchronicity, HTTP methods, compliance. **Do NOT create a `.spec.md` at this stage** (scope enforcement). Questions ordered by importance, concrete language, no technical solutions baked in.

## 2. spec-from-vague-request — turn a complaint into questions
**Context:** PM says "Search is slow and doesn't find what they need." Existing search spec covers query interface, scope (title/body/tags), TF-IDF ranking, filtering, pagination (20/page), auto-indexing.
**Analysis:** "slow" → not addressed (no performance targets/SLAs/indexing latency); "doesn't find" → partially covered (defines what's searchable, not accuracy/quality metrics).
**Five interview questions:** (1) share 2–3 specific failing queries + expected results; (2) current avg response time + acceptable target; (3) fields beyond title/body/tags to search; (4) missing docs due to ranking or indexing?; (5) search frequency + typical project sizes for performance targets.

## 3. spec-authoring-structure-and-format — write the spec
**Task:** spec for an inventory reservation service. Module `src/inventory/reservation.py`; tests `tests/inventory/test_reservation.py`, `test_reservation_edge_cases.py`.
**API:** `reserve(product_id, quantity, order_id) -> Reservation`; `release(reservation_id) -> None`; `get_reserved(product_id) -> int`.
**Behaviors:** `reserve()` atomically reserves or raises `InsufficientStockError` (include requested/available); zero-stock products unavailable; `release()` idempotent — raises `ReservationNotFoundError` only for never-valid IDs, succeeds silently for expired; `get_reserved()` returns current reserved (0 if none).
**Business logic:** reservations auto-expire 15 min after creation unless confirmed; expired may be released without error; reserved never exceeds total inventory. **Non-functional:** thread-safe, no external network calls, consistent under concurrent access. **Output:** `specs/inventory-reservation.spec.md` with frontmatter, headings per functional area, inline `[@test]` links, API contracts.

## 4. spec-drift-after-refactor — detect & fix drift
**Issues found vs. code:** target paths outdated (`../src/auth/` → `src/identity/`); test paths wrong (`../tests/auth/` → `tests/identity/`); session TTL drift (spec 24h, code 8h); lockout threshold drift (spec 5 attempts, code 3).
**Behavior:** update `specs/auth.spec.md` so `targets` and `[@test]` links resolve and the documented behavior (8h sessions, lock after 3 attempts, single-use refresh tokens that invalidate the session on reuse) matches the implementation. Specs are living documents — fix the spec to reflect reality (or fix the code if the spec is the intended truth), then re-verify.

## 5. spec-update-for-new-requirement — extend a spec
**Context:** add rate limiting to a REST API spec. **Behavior:** add a `## Rate Limiting` section — per-API-key Redis sliding window; standard 100 req/min; `/search` 20 req/min; admin keys 10× multiplier; exceeded → HTTP 429 with `Retry-After` (seconds); link `[@test] ../tests/api/test_rate_limiting.py`. Keep existing Endpoints/Authentication/Pagination/Error-handling sections coherent and test-linked.

## 6. skip-spec-pushback — refuse to merge undocumented behavior
**Issue:** a caching layer was implemented with no spec coverage in `specs/api.spec.md` (no caching/TTL/invalidation/scope).
**Behavior:** extract the de-facto requirements from code (reads cached + writes invalidate; default TTL 5 min, `list_projects` 60s; key = endpoint + SHA256 param hash; explicit purge on writes; in-memory, process lifetime) and surface unresolved gaps (cache in responses? race handling on invalidation? per-endpoint TTLs intentional? cache×auth user-isolation? env-controlled config? hit-rate monitoring?). **Next step:** formally document caching in the spec **before merging.** Embodies spec-before-code applied retroactively.

## 7. trivial-change-exception — when NOT to update the spec
**Change:** fix a typo in `src/validation.py` ("Invlaid email format" → "Invalid email format"). **Why no spec update:** `specs/registration.spec.md` says "Email must be a valid email format; invalid emails raise ValueError" — it describes *what* happens (raising the error), not the exact message text. A behavior-preserving maintenance fix needs only the code change. This is the trivial-change exception in action.

## 8. requirements-gap-analysis-from-existing-specs — analyze before building
**Context:** bulk-export feature for user data. Existing: user-management spec (`list_users()` filtering by role/status, pagination 100/page, admin access) + auth spec (admin-only, session validation).
**Gap analysis:** performance/scale (50k+ users? respects pagination or streams all? rate limit/timeout?); export specifics (CSV schema/column order? real-time vs eventual consistency? file naming/storage/delivery? sync download vs async email link?); scope (which fields? filter combinations? audit logging? retention? concurrency limits?).
**Ten interview questions** covering sync/async, max size + acceptable generation time, fields, multiple filters, consistency, retention, audit logging, concurrency limits, which admin roles, filename convention. **Preliminary scope:** likely CSV + role/status filtering + admin-only + standard fields; out of scope JSON/XML/scheduled/custom columns/historical; unclear sync-vs-async, large-dataset handling, audit, retention.

## 9. work-review-with-discovered-requirements — review surfaces new truth
**Context:** review a notification-service implementation.
- **Issue 1 (High):** unsupported event — spec lists `account.created`, `password.reset`, `account.suspended`; code adds `account.reactivated` (email + SMS) with no spec entry or test coverage.
- **Issue 2 (Medium):** SMS error-handling mismatch — spec says "retry 3 times then raise `DeliveryError`"; code returns `None` silently when no phone number exists.
- **Issue 3 (Medium):** missing SMS documentation — `password.reset` is email-only and code correctly skips SMS, but the "SMS intentionally not sent" behavior (return `None`? omit? exception?) is undefined.
**Recommendations:** clarify `account.reactivated` (add to spec with tests or remove from code); document SMS-unavailable behavior; update the spec to match implementation **before merge.** (Test files were placeholders, so actual execution was unavailable — note that honestly rather than claiming tests passed.)
