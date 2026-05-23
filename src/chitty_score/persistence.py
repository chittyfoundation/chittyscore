"""ChittyScore persistence layer.

Writes scoring results and input events to `chittyscore.results` /
`chittyscore.events` in the ChittyOS-Core Neon DB. All writes are FK-bound to
`public.identities.id` (the internal UUID, not the ChittyID DID string).

If `DATABASE_URL` is unset, the module degrades to no-op so the API still
serves /api/trust/calculate without a DB.
"""

from __future__ import annotations

import json
import logging
import os
from contextlib import contextmanager
from typing import Any, Iterable, Optional
from uuid import UUID

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool

from .models import TrustEvent

log = logging.getLogger(__name__)

_pool: Optional[ThreadedConnectionPool] = None


def init_pool(dsn: Optional[str] = None, minconn: int = 1, maxconn: int = 5) -> bool:
    """Initialize the connection pool. Returns True if pool is usable."""
    global _pool
    dsn = dsn or os.getenv("DATABASE_URL", "")
    if not dsn:
        log.info("DATABASE_URL unset; persistence disabled")
        _pool = None
        return False
    _pool = ThreadedConnectionPool(minconn, maxconn, dsn=dsn)
    return True


def enabled() -> bool:
    return _pool is not None


@contextmanager
def _conn():
    if _pool is None:
        raise RuntimeError("persistence pool not initialized")
    conn = _pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)


def resolve_identity_id(entity_id: str) -> Optional[UUID]:
    """Resolve an external entity_id (DID or chitty_id) to internal identities.id.

    Accepts either a `did:chitty:*` DID, a `chitty_id` (e.g. `07-T-CHI-...`),
    or a stringified UUID. Returns None if the identity does not exist.
    """
    try:
        return UUID(entity_id)
    except (ValueError, AttributeError):
        pass

    with _conn() as c, c.cursor() as cur:
        cur.execute(
            "SELECT id FROM public.identities WHERE did = %s OR chitty_id = %s LIMIT 1",
            (entity_id, entity_id),
        )
        row = cur.fetchone()
        return row[0] if row else None


def persist_result(identity_id: UUID, result: dict[str, Any]) -> UUID:
    """Insert a scoring result. Returns the new row's id."""
    dims = result["dimension_scores"]
    outs = result["output_scores"]
    insights = result.get("insights", [])
    details = result.get("calculation_details", {})

    sql = """
        INSERT INTO chittyscore.results (
            identity_id,
            source_dimension, temporal_dimension, channel_dimension,
            outcome_dimension, network_dimension, justice_dimension,
            people_score, legal_score, state_score, chitty_score,
            composite_score, trust_level, confidence,
            insights, calculation_details
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb
        ) RETURNING id
    """
    params = (
        str(identity_id),
        dims["source"], dims["temporal"], dims["channel"],
        dims["outcome"], dims["network"], dims["justice"],
        outs["people"], outs["legal"], outs["state"], outs["chitty"],
        result["composite_score"], result["trust_level"], result["confidence"],
        json.dumps(insights), json.dumps(details),
    )
    with _conn() as c, c.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()[0]


def persist_events(identity_id: UUID, events: Iterable[TrustEvent]) -> int:
    """Insert input events. Returns count inserted."""
    def _val(x):
        return x.value if hasattr(x, "value") else x

    rows = [
        (
            str(identity_id),
            _val(e.event_type),
            e.timestamp,
            e.channel,
            _val(e.outcome),
            float(e.impact_score),
            list(e.tags or []),
            json.dumps(e.metadata or {}),
        )
        for e in events
    ]
    if not rows:
        return 0
    sql = """
        INSERT INTO chittyscore.events (
            identity_id, event_type, event_timestamp, channel,
            outcome, impact_score, tags, metadata
        ) VALUES %s
    """
    with _conn() as c, c.cursor() as cur:
        psycopg2.extras.execute_values(
            cur, sql, rows,
            template="(%s, %s, %s, %s, %s, %s, %s, %s::jsonb)",
        )
        return len(rows)


def fetch_history(identity_id: UUID, limit: int = 20) -> list[dict[str, Any]]:
    """Return recent scoring results for an identity, newest first."""
    sql = """
        SELECT id, chitty_score, composite_score, trust_level, confidence,
               calculated_at
        FROM chittyscore.results
        WHERE identity_id = %s
        ORDER BY calculated_at DESC
        LIMIT %s
    """
    with _conn() as c, c.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (str(identity_id), limit))
        rows = cur.fetchall()
    for r in rows:
        r["id"] = str(r["id"])
        r["chitty_score"] = float(r["chitty_score"])
        r["composite_score"] = float(r["composite_score"])
        r["confidence"] = float(r["confidence"])
        r["calculated_at"] = r["calculated_at"].isoformat()
    return rows
