#!/usr/bin/env python3
"""
inbox_metrics.py - deterministic inbox metrics for the Intercom Inbox Coach.

Why this exists: Intercom timestamps are Unix epoch seconds. Converting and
subtracting them by hand produces confident, wrong numbers. This script does
the arithmetic; the model interprets the result.

Standard library only, so it runs anywhere Python 3.8+ runs.

Usage:
    python3 inbox_metrics.py records.jsonl [options]
    python3 inbox_metrics.py --self-test

Input: JSONL (one record per line), a JSON array, or a JSON object with a
"conversations" (or "records") list and an optional "reference_now".
Only "id" is required per record. Flat fields and raw Intercom shapes are
both accepted. See references/intercom-mcp.md section 6 for the schema.
"""

import argparse
import json
import sys
from collections import Counter, OrderedDict
from datetime import datetime, timezone
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python < 3.9
    ZoneInfo = None

_MISSING = object()

WAIT_BUCKETS = [("< 4h", 0, 4), ("4-24h", 4, 24), ("1-3d", 24, 72), ("3-7d", 72, 168), ("> 7d", 168, None)]
AGE_BUCKETS = [("< 1d", 0, 1), ("1-3d", 1, 3), ("3-7d", 3, 7), ("7-14d", 7, 14), ("14-30d", 14, 30), ("> 30d", 30, None)]


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

def parse_ts(value):
    """Return epoch seconds (float) or None. Accepts epoch s/ms, numeric strings, ISO 8601."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        v = float(value)
        if v <= 0:
            return None
        return v / 1000.0 if v > 1e12 else v
    if isinstance(value, str):
        s = value.strip()
        try:
            return parse_ts(float(s))
        except ValueError:
            pass
        try:
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except ValueError:
            return None
    return None


def _dig(d, *keys):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def _norm_tags(raw):
    if raw is None:
        return []
    if isinstance(raw, dict):
        raw = raw.get("tags", [])
    out = []
    if isinstance(raw, str):
        raw = [t for t in raw.split(",")]
    for t in raw or []:
        if isinstance(t, dict):
            name = t.get("name")
        else:
            name = t
        if name is not None and str(name).strip():
            out.append(str(name).strip())
    return out


def _norm_author(raw):
    if raw is None:
        return None
    s = str(raw).strip().lower()
    if s in ("customer", "user", "lead", "contact", "visitor"):
        return "customer"
    if s in ("admin", "teammate", "agent", "operator"):
        return "admin"
    if s in ("bot", "fin", "ai", "ai_agent", "workflow"):
        return "bot"
    return "unknown"


def _norm_priority(raw):
    if isinstance(raw, bool):
        return raw
    if raw is None:
        return False
    return str(raw).strip().lower() in ("priority", "true", "yes", "1", "high")


def _to_int(raw, default=0):
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def normalize(rec):
    """Turn a flat or raw-Intercom-shaped record into the internal shape."""
    r = {}
    r["id"] = str(rec.get("id", "")).replace("conversation_", "").strip()
    r["inbox"] = str(rec.get("inbox") or "unspecified")

    state = rec.get("state")
    if state is None and isinstance(rec.get("open"), bool):
        state = "open" if rec["open"] else "closed"
    r["state"] = str(state or "unknown").strip().lower()

    r["created_at"] = parse_ts(rec.get("created_at"))
    r["updated_at"] = parse_ts(rec.get("updated_at"))
    r["snoozed_until"] = parse_ts(rec.get("snoozed_until"))
    last_close = rec.get("last_close_at", _dig(rec, "statistics", "last_close_at"))
    r["last_close_at"] = parse_ts(last_close)

    # waiting_since: key absent (unknown) is different from explicit null (ball with customer)
    ws_raw = rec.get("waiting_since", _MISSING)
    r["waiting_since_known"] = ws_raw is not _MISSING
    r["waiting_since"] = None if ws_raw is _MISSING else parse_ts(ws_raw)

    r["tags"] = _norm_tags(rec.get("tags"))
    tier = rec.get("tier")
    r["tier"] = str(tier).strip() if tier not in (None, "") else None
    r["priority"] = _norm_priority(rec.get("priority"))
    reopens = rec.get("count_reopens", _dig(rec, "statistics", "count_reopens"))
    r["count_reopens"] = _to_int(reopens, 0)
    r["last_author_type"] = _norm_author(rec.get("last_author_type"))
    sla = rec.get("sla_status", _dig(rec, "sla_applied", "sla_status"))
    r["sla_status"] = str(sla).strip().lower() if sla else None
    rating = rec.get("rating", _dig(rec, "conversation_rating", "rating"))
    r["rating"] = _to_int(rating, None) if rating is not None else None

    r["first_name"] = (str(rec.get("first_name")).strip() if rec.get("first_name") else "")
    r["title"] = (str(rec.get("title")).strip() if rec.get("title") else "")
    r["url"] = (str(rec.get("url")).strip() if rec.get("url") else "")
    r["admin_assignee_id"] = rec.get("admin_assignee_id")
    r["team_assignee_id"] = rec.get("team_assignee_id")
    return r


def load_records(path):
    """Return (records, reference_now or None)."""
    text = Path(path).read_text(encoding="utf-8").strip()
    if not text:
        return [], None
    reference_now = None
    records = None
    try:
        data = json.loads(text)
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            reference_now = parse_ts(data.get("reference_now"))
            for key in ("conversations", "records", "data", "results"):
                if isinstance(data.get(key), list):
                    records = data[key]
                    break
            if records is None:
                records = [data]
    except json.JSONDecodeError:
        records = []
        for n, line in enumerate(text.splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit("Line %d is not valid JSON: %s" % (n, exc))
            if isinstance(obj, dict):
                records.append(obj)
    return [x for x in records if isinstance(x, dict)], reference_now


# --------------------------------------------------------------------------
# Computation
# --------------------------------------------------------------------------

def bucket_label(value, buckets):
    for label, lo, hi in buckets:
        if value >= lo and (hi is None or value < hi):
            return label
    return buckets[-1][0]


def human_duration(hours):
    if hours is None:
        return "?"
    if hours < 1:
        return "%dm" % max(1, int(round(hours * 60)))
    if hours < 10:
        whole = int(hours)
        minutes = int(round((hours - whole) * 60))
        if minutes == 60:
            whole, minutes = whole + 1, 0
        return "%dh %dm" % (whole, minutes) if minutes else "%dh" % whole
    if hours < 48:
        return "%dh" % int(round(hours))
    days = hours / 24.0
    if days < 14:
        whole = int(days)
        rest = int(round((days - whole) * 24))
        return "%dd %dh" % (whole, rest) if rest else "%dd" % whole
    return "%dd" % int(round(days))


def enrich(r, now, th):
    """Add derived fields, flags, reasons and the attention score to one record."""
    flags = []
    reasons = []
    score = 0.0
    is_open = r["state"] == "open"
    is_snoozed = r["state"] == "snoozed"
    is_closed = r["state"] == "closed"

    r["age_days"] = (now - r["created_at"]) / 86400.0 if r["created_at"] else None
    r["idle_days"] = (now - r["updated_at"]) / 86400.0 if r["updated_at"] else None

    # Who has the ball (open conversations only)
    r["ball"] = None
    r["waiting_hours"] = None
    r["waiting_is_proxy"] = False
    if is_open:
        if r["waiting_since"] is not None:
            r["ball"] = "us"
            r["waiting_hours"] = max(0.0, (now - r["waiting_since"]) / 3600.0)
        elif r["waiting_since_known"]:
            r["ball"] = "customer"
        elif r["last_author_type"] == "customer":
            r["ball"] = "us"
            if r["updated_at"]:
                r["waiting_hours"] = max(0.0, (now - r["updated_at"]) / 3600.0)
                r["waiting_is_proxy"] = True
        elif r["last_author_type"] in ("admin", "bot"):
            r["ball"] = "customer"
        else:
            r["ball"] = "unknown"

    if r["ball"] == "us" and r["waiting_hours"] is not None:
        wh = r["waiting_hours"]
        if wh >= th["breach_hours"]:
            flags.append("breach")
            reasons.append("customer waiting %s (breach at %dh)" % (human_duration(wh), th["breach_hours"]))
            score += 50
        elif wh >= th["risk_hours"]:
            flags.append("at_risk")
            reasons.append("customer waiting %s (at risk at %dh)" % (human_duration(wh), th["risk_hours"]))
            score += 30
        else:
            reasons.append("customer waiting %s" % human_duration(wh))
        score += min(20.0, wh / 4.0)

    if r["sla_status"] == "missed" and not is_closed:
        flags.append("sla_missed")
        reasons.append("SLA missed")
        score += 25
    elif r["sla_status"] == "active" and not is_closed:
        flags.append("sla_active")
        score += 5

    if r["priority"] and not is_closed:
        flags.append("priority")
        reasons.append("marked priority")
        score += 20

    if r["count_reopens"] >= 1:
        flags.append("reopened")
        if not is_closed:
            reasons.append("reopened %dx" % r["count_reopens"])
            score += min(20, 10 * r["count_reopens"])

    if is_snoozed and r["snoozed_until"] is not None:
        if r["snoozed_until"] < now:
            flags.append("snooze_overdue")
            reasons.append("snooze expired %s ago" % human_duration((now - r["snoozed_until"]) / 3600.0))
            score += 15
        elif r["snoozed_until"] < now + 86400:
            flags.append("snooze_waking_24h")

    if is_open and r["idle_days"] is not None and r["idle_days"] >= th["stale_days"]:
        flags.append("stale")
        reasons.append("no update for %s" % human_duration(r["idle_days"] * 24))
        score += 10

    if (is_open and r["ball"] == "customer" and r["idle_days"] is not None
            and r["idle_days"] >= th["customer_silent_days"]):
        flags.append("customer_silent")
        reasons.append("customer silent for %s" % human_duration(r["idle_days"] * 24))
        score += 5

    if (is_open or is_snoozed) and r["age_days"] is not None:
        if r["age_days"] >= 30:
            score += 15
            reasons.append("open for %s" % human_duration(r["age_days"] * 24))
        elif r["age_days"] >= 14:
            score += 10
            reasons.append("open for %s" % human_duration(r["age_days"] * 24))
        elif r["age_days"] >= 7:
            score += 5

    r["closed_in_lookback"] = False
    if is_closed:
        closed_ts = r["last_close_at"] or r["updated_at"]
        if closed_ts is not None and closed_ts >= now - th["lookback_days"] * 86400:
            r["closed_in_lookback"] = True
    if r["rating"] is not None and r["rating"] <= 2:
        flags.append("bad_rating")

    r["flags"] = flags
    r["reasons"] = reasons
    r["score"] = round(score, 1) if not is_closed else 0.0
    return r


def compute(records, now, th, top=25):
    rows = [enrich(normalize(x), now, th) for x in records]
    rows = [r for r in rows if r["id"]]
    seen = set()
    unique = []
    duplicates = 0
    for r in rows:
        key = r["id"]
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        unique.append(r)
    rows = unique

    inboxes = sorted({r["inbox"] for r in rows})
    out = OrderedDict()
    out["record_count"] = len(rows)
    out["duplicates_dropped"] = duplicates
    out["inboxes"] = inboxes

    totals = OrderedDict()
    for ib in inboxes + ["ALL"]:
        sub = rows if ib == "ALL" else [r for r in rows if r["inbox"] == ib]
        totals[ib] = OrderedDict([
            ("open", sum(1 for r in sub if r["state"] == "open")),
            ("snoozed", sum(1 for r in sub if r["state"] == "snoozed")),
            ("closed_in_lookback", sum(1 for r in sub if r["closed_in_lookback"])),
            ("closed_older", sum(1 for r in sub if r["state"] == "closed" and not r["closed_in_lookback"])),
            ("other", sum(1 for r in sub if r["state"] not in ("open", "snoozed", "closed"))),
        ])
    out["totals"] = totals

    ball = OrderedDict()
    for ib in inboxes + ["ALL"]:
        sub = [r for r in rows if r["state"] == "open" and (ib == "ALL" or r["inbox"] == ib)]
        ball[ib] = OrderedDict([
            ("us", sum(1 for r in sub if r["ball"] == "us")),
            ("customer", sum(1 for r in sub if r["ball"] == "customer")),
            ("unknown", sum(1 for r in sub if r["ball"] == "unknown")),
        ])
    out["ball"] = ball

    waiting = [r for r in rows if r["ball"] == "us" and r["waiting_hours"] is not None]
    wb = OrderedDict((label, 0) for label, _, _ in WAIT_BUCKETS)
    for r in waiting:
        wb[bucket_label(r["waiting_hours"], WAIT_BUCKETS)] += 1
    out["waiting_on_us_buckets"] = wb
    out["at_risk"] = sum(1 for r in rows if "at_risk" in r["flags"])
    out["breach"] = sum(1 for r in rows if "breach" in r["flags"])
    out["waiting_proxy_used"] = sum(1 for r in waiting if r["waiting_is_proxy"])
    longest = max(waiting, key=lambda r: r["waiting_hours"], default=None)
    out["longest_wait"] = (
        {"id": longest["id"], "hours": round(longest["waiting_hours"], 1), "human": human_duration(longest["waiting_hours"])}
        if longest else None
    )

    active = [r for r in rows if r["state"] in ("open", "snoozed")]
    ab = OrderedDict((label, 0) for label, _, _ in AGE_BUCKETS)
    for r in active:
        if r["age_days"] is not None:
            ab[bucket_label(r["age_days"], AGE_BUCKETS)] += 1
    out["age_buckets_open_and_snoozed"] = ab

    out["stale"] = sum(1 for r in rows if "stale" in r["flags"])
    out["customer_silent"] = sum(1 for r in rows if "customer_silent" in r["flags"])
    out["snooze_overdue"] = sum(1 for r in rows if "snooze_overdue" in r["flags"])
    out["snooze_waking_24h"] = sum(1 for r in rows if "snooze_waking_24h" in r["flags"])
    out["priority_active"] = sum(1 for r in active if r["priority"])
    out["sla_missed_active"] = sum(1 for r in active if r["sla_status"] == "missed")
    out["sla_active"] = sum(1 for r in active if r["sla_status"] == "active")
    out["reopened_active"] = sum(1 for r in active if r["count_reopens"] >= 1)

    closed_lb = [r for r in rows if r["closed_in_lookback"]]
    out["closed_lookback"] = OrderedDict([
        ("count", len(closed_lb)),
        ("with_reopens", sum(1 for r in closed_lb if r["count_reopens"] >= 1)),
        ("bad_rating", sum(1 for r in closed_lb if "bad_rating" in r["flags"])),
        ("rated", sum(1 for r in closed_lb if r["rating"] is not None)),
    ])
    out["closed_to_review"] = [
        {"id": r["id"], "inbox": r["inbox"], "first_name": r["first_name"], "title": r["title"],
         "reopens": r["count_reopens"], "rating": r["rating"], "url": r["url"]}
        for r in closed_lb if r["count_reopens"] >= 1 or "bad_rating" in r["flags"]
    ]

    tag_counter = Counter()
    for r in active:
        if r["tags"]:
            tag_counter.update(set(r["tags"]))
        else:
            tag_counter["(untagged)"] += 1
    out["top_tags_active"] = tag_counter.most_common(20)

    tier_counter = Counter((r["tier"] or "(no tier)") for r in active)
    out["tiers_active"] = sorted(tier_counter.items(), key=lambda kv: (-kv[1], kv[0]))

    ranked = sorted(
        [r for r in active if r["score"] > 0],
        key=lambda r: (-r["score"], -(r["waiting_hours"] or 0), -(r["age_days"] or 0), r["id"]),
    )
    out["attention_total"] = len(ranked)
    out["attention"] = [
        {"rank": i, "score": r["score"], "id": r["id"], "inbox": r["inbox"], "first_name": r["first_name"],
         "state": r["state"], "ball": r["ball"],
         "waiting": human_duration(r["waiting_hours"]) if r["waiting_hours"] is not None else "",
         "age": human_duration(r["age_days"] * 24) if r["age_days"] is not None else "",
         "tier": r["tier"] or "", "flags": r["flags"], "reasons": r["reasons"],
         "title": r["title"], "url": r["url"]}
        for i, r in enumerate(ranked[:top], 1)
    ]

    out["data_quality"] = OrderedDict([
        ("missing_created_at", sum(1 for r in rows if r["created_at"] is None)),
        ("missing_updated_at", sum(1 for r in rows if r["updated_at"] is None)),
        ("open_with_unknown_ball", sum(1 for r in rows if r["ball"] == "unknown")),
        ("waiting_time_from_updated_at_proxy", out["waiting_proxy_used"]),
        ("active_untagged", tag_counter.get("(untagged)", 0)),
        ("active_without_tier", tier_counter.get("(no tier)", 0)),
        ("unknown_state", sum(1 for r in rows if r["state"] not in ("open", "snoozed", "closed"))),
        ("timestamps_in_future", sum(1 for r in rows if r["updated_at"] and r["updated_at"] > now + 3600)),
    ])
    return out


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def fmt_time(epoch, tzname):
    tz = timezone.utc
    label = "UTC"
    if tzname and ZoneInfo is not None:
        try:
            tz = ZoneInfo(tzname)
            label = tzname
        except Exception:
            pass
    return datetime.fromtimestamp(epoch, tz).strftime("%Y-%m-%d %H:%M") + " " + label


def _cell(text):
    return str(text).replace("|", "/").replace("\n", " ")


def render_md(m, now, tzname, th):
    L = []
    L.append("# Inbox metrics")
    L.append("")
    L.append("Generated for: %s | Records: %d | Thresholds: at risk %dh, breach %dh, stale %dd, customer silent %dd, lookback %dd"
             % (fmt_time(now, tzname), m["record_count"], th["risk_hours"], th["breach_hours"],
                th["stale_days"], th["customer_silent_days"], th["lookback_days"]))
    if m["duplicates_dropped"]:
        L.append("")
        L.append("Note: %d duplicate record(s) dropped (same id)." % m["duplicates_dropped"])

    L += ["", "## Totals by inbox and state", "",
          "| Inbox | Open | Snoozed | Closed in lookback | Closed older | Other |", "|---|---|---|---|---|---|"]
    for ib, t in m["totals"].items():
        L.append("| %s | %d | %d | %d | %d | %d |" % (_cell(ib), t["open"], t["snoozed"], t["closed_in_lookback"], t["closed_older"], t["other"]))

    L += ["", "## Open conversations: who has the ball", "",
          "| Inbox | Waiting on us | Waiting on customer | Unknown |", "|---|---|---|---|"]
    for ib, b in m["ball"].items():
        L.append("| %s | %d | %d | %d |" % (_cell(ib), b["us"], b["customer"], b["unknown"]))

    L += ["", "## Waiting on us: for how long", "", "| Bucket | Count |", "|---|---|"]
    for label, n in m["waiting_on_us_buckets"].items():
        L.append("| %s | %d |" % (label, n))
    L.append("")
    L.append("At risk: **%d** | Breach: **%d**" % (m["at_risk"], m["breach"]))
    if m["longest_wait"]:
        L.append("Longest wait: %s (conversation %s)" % (m["longest_wait"]["human"], m["longest_wait"]["id"]))

    L += ["", "## Age of open and snoozed conversations (since created)", "", "| Bucket | Count |", "|---|---|"]
    for label, n in m["age_buckets_open_and_snoozed"].items():
        L.append("| %s | %d |" % (label, n))

    L += ["", "## Other signals", "",
          "- Stale (open, no update for %dd or more): %d" % (th["stale_days"], m["stale"]),
          "- Customer silent (ball with customer for %dd or more): %d" % (th["customer_silent_days"], m["customer_silent"]),
          "- Snoozes overdue: %d | waking within 24h: %d" % (m["snooze_overdue"], m["snooze_waking_24h"]),
          "- Priority (open or snoozed): %d" % m["priority_active"],
          "- SLA missed (open or snoozed): %d | SLA running: %d" % (m["sla_missed_active"], m["sla_active"]),
          "- Reopened at least once (open or snoozed): %d" % m["reopened_active"]]

    c = m["closed_lookback"]
    L += ["", "## Closed in the lookback window", "",
          "- Closed: %d | with reopens: %d | rated: %d | rating of 2 or lower: %d" % (c["count"], c["with_reopens"], c["rated"], c["bad_rating"])]
    if m["closed_to_review"]:
        L += ["", "| Conversation | Inbox | Customer | Reopens | Rating | Title |", "|---|---|---|---|---|---|"]
        for r in m["closed_to_review"]:
            ref = r["url"] or r["id"]
            L.append("| %s | %s | %s | %d | %s | %s |" % (_cell(ref), _cell(r["inbox"]), _cell(r["first_name"]), r["reopens"],
                                                      r["rating"] if r["rating"] is not None else "", _cell(r["title"])))

    L += ["", "## Tags on open and snoozed conversations (top 20)", "", "| Tag | Count |", "|---|---|"]
    for tag, n in m["top_tags_active"]:
        L.append("| %s | %d |" % (_cell(tag), n))

    L += ["", "## Tiers on open and snoozed conversations", "", "| Tier | Count |", "|---|---|"]
    for tier, n in m["tiers_active"]:
        L.append("| %s | %d |" % (_cell(tier), n))

    L += ["", "## Attention ranking (top %d of %d with a score)" % (len(m["attention"]), m["attention_total"]), "",
          "A sorting aid for what to read first, not a verdict.", "",
          "| # | Score | Conversation | Inbox | Customer | State | Ball | Waiting | Age | Tier | Why | Title |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for a in m["attention"]:
        ref = a["url"] or a["id"]
        L.append("| %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            a["rank"], a["score"], _cell(ref), _cell(a["inbox"]), _cell(a["first_name"]), a["state"], a["ball"] or "",
            a["waiting"], a["age"], _cell(a["tier"]), _cell("; ".join(a["reasons"])), _cell(a["title"])))

    L += ["", "## Data quality", ""]
    for k, v in m["data_quality"].items():
        L.append("- %s: %d" % (k.replace("_", " "), v))
    if m["data_quality"]["waiting_time_from_updated_at_proxy"]:
        L.append("")
        L.append("Some waiting times were estimated from updated_at because waiting_since was not provided. Treat them as upper-level approximations.")
    L.append("")
    return "\n".join(L)


# --------------------------------------------------------------------------
# Self-test
# --------------------------------------------------------------------------

def self_test():
    sample = Path(__file__).resolve().parent.parent / "assets" / "sample_inbox.json"
    if not sample.exists():
        print("SELF-TEST FAIL: %s not found" % sample)
        return 1
    records, ref_now = load_records(sample)
    if ref_now is None:
        print("SELF-TEST FAIL: sample has no reference_now")
        return 1
    th = dict(risk_hours=24, breach_hours=48, stale_days=5, customer_silent_days=5, lookback_days=7)
    m = compute(records, ref_now, th, top=25)
    expected = json.loads(sample.read_text(encoding="utf-8")).get("expected", {})
    checks = []

    def check(name, actual, want):
        ok = actual == want
        checks.append(ok)
        print("  [%s] %s: got %r, expected %r" % ("ok" if ok else "FAIL", name, actual, want))

    check("record_count", m["record_count"], expected.get("record_count"))
    check("open", m["totals"]["ALL"]["open"], expected.get("open"))
    check("snoozed", m["totals"]["ALL"]["snoozed"], expected.get("snoozed"))
    check("closed_in_lookback", m["totals"]["ALL"]["closed_in_lookback"], expected.get("closed_in_lookback"))
    check("ball_us", m["ball"]["ALL"]["us"], expected.get("ball_us"))
    check("ball_customer", m["ball"]["ALL"]["customer"], expected.get("ball_customer"))
    check("at_risk", m["at_risk"], expected.get("at_risk"))
    check("breach", m["breach"], expected.get("breach"))
    check("snooze_overdue", m["snooze_overdue"], expected.get("snooze_overdue"))
    check("stale", m["stale"], expected.get("stale"))
    check("top_attention_id", m["attention"][0]["id"] if m["attention"] else None, expected.get("top_attention_id"))
    check("closed_to_review", len(m["closed_to_review"]), expected.get("closed_to_review"))

    # parser sanity
    check("parse epoch ms", parse_ts(1790000000000), 1790000000.0)
    check("parse ISO Z", parse_ts("2026-09-21T16:00:00Z"), datetime(2026, 9, 21, 16, 0, tzinfo=timezone.utc).timestamp())
    check("parse null", parse_ts(None), None)

    if all(checks):
        print("SELF-TEST PASS (%d checks)" % len(checks))
        return 0
    print("SELF-TEST FAIL (%d of %d checks failed)" % (checks.count(False), len(checks)))
    return 1


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(description="Deterministic inbox metrics for the Intercom Inbox Coach.")
    p.add_argument("records", nargs="?", help="Path to records (JSONL, JSON array, or JSON object with a conversations list)")
    p.add_argument("--now", help="Pin the clock: epoch seconds or ISO 8601. Default: system time, or reference_now in the file.")
    p.add_argument("--tz", default="UTC", help="IANA time zone for display, e.g. Europe/Rome")
    p.add_argument("--risk-hours", type=float, default=24)
    p.add_argument("--breach-hours", type=float, default=48)
    p.add_argument("--stale-days", type=float, default=5)
    p.add_argument("--customer-silent-days", type=float, default=5)
    p.add_argument("--lookback-days", type=float, default=7)
    p.add_argument("--top", type=int, default=25, help="Rows in the attention ranking")
    p.add_argument("--format", choices=["md", "json"], default="md")
    p.add_argument("--out", help="Write output to this file as well as stdout")
    p.add_argument("--self-test", action="store_true", help="Run against assets/sample_inbox.json and verify")
    args = p.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.records:
        p.error("records path is required (or use --self-test)")
    if args.breach_hours < args.risk_hours:
        p.error("--breach-hours must be greater than or equal to --risk-hours")

    records, ref_now = load_records(args.records)
    if args.now:
        now = parse_ts(args.now)
        if now is None:
            p.error("could not parse --now value: %r" % args.now)
    elif ref_now is not None:
        now = ref_now
    else:
        now = datetime.now(timezone.utc).timestamp()

    th = dict(risk_hours=args.risk_hours, breach_hours=args.breach_hours, stale_days=args.stale_days,
              customer_silent_days=args.customer_silent_days, lookback_days=args.lookback_days)
    m = compute(records, now, th, top=args.top)

    if args.format == "json":
        payload = OrderedDict([("generated_for_epoch", now), ("generated_for", fmt_time(now, args.tz)),
                               ("thresholds", th), ("metrics", m)])
        text = json.dumps(payload, indent=2, ensure_ascii=False)
    else:
        text = render_md(m, now, args.tz, th)

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    try:
        print(text)
        sys.stdout.flush()
    except BrokenPipeError:  # output piped into head or similar
        try:
            sys.stdout.close()
        except Exception:
            pass
        return 0
    if not records:
        print("\nWarning: no records found in %s" % args.records, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
