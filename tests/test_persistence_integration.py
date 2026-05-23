"""Integration tests for ChittyScore persistence.

Hits a real Neon Postgres (no mocks). Skipped unless TEST_DATABASE_URL is set.
The target DB must have `public.identities` and the `chittyscore` schema applied
(see schema.sql).

Run:
    TEST_DATABASE_URL='postgresql://...' python3 -m unittest tests.test_persistence_integration
"""

import os
import unittest
from datetime import datetime, timezone
from uuid import uuid4

from src.chitty_score import persistence
from src.chitty_score.models import TrustEntity, TrustEvent

DSN = os.getenv("TEST_DATABASE_URL", "")


@unittest.skipUnless(DSN, "TEST_DATABASE_URL not set; skipping live Neon tests")
class PersistenceIntegrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        persistence.init_pool(DSN, minconn=1, maxconn=2)
        cls.did = f"did:chitty:test:itest-{uuid4().hex[:12]}"
        # Seed an identity row (FK target). chitty_id is VARCHAR(50).
        with persistence._conn() as c, c.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.identities
                    (did, biometric_hash, public_key, status, chitty_id,
                     entity_type, lifecycle_stage, trust_level)
                VALUES (%s, %s, %s, 'active', %s, 'P', 'L2', 'L2')
                RETURNING id
                """,
                (cls.did, f"sha256:{uuid4().hex}", f"pk:{uuid4().hex}",
                 f"07-T-CHI-{uuid4().hex[:4]}-P-26-A-9"),
            )
            cls.identity_id = cur.fetchone()[0]

    @classmethod
    def tearDownClass(cls):
        if persistence.enabled():
            with persistence._conn() as c, c.cursor() as cur:
                cur.execute("DELETE FROM public.identities WHERE id = %s",
                            (str(cls.identity_id),))

    def test_resolve_identity_by_did(self):
        resolved = persistence.resolve_identity_id(self.did)
        self.assertEqual(str(resolved), str(self.identity_id))

    def test_resolve_unknown_returns_none(self):
        self.assertIsNone(
            persistence.resolve_identity_id("did:chitty:test:does-not-exist-xyz")
        )

    def test_persist_result_and_fetch_history(self):
        result = {
            "composite_score": 72.45,
            "trust_level": "L2_ENHANCED",
            "dimension_scores": {
                "source": 78.0, "temporal": 60.5, "channel": 88.0,
                "outcome": 65.0, "network": 70.0, "justice": 75.5,
            },
            "output_scores": {
                "people": 71.2, "legal": 73.4, "state": 74.0, "chitty": 72.45,
            },
            "confidence": 85.0,
            "insights": [
                {"category": "strength", "title": "Verified API usage",
                 "description": "All events via verified_api",
                 "impact": 4.0, "confidence": 0.9}
            ],
            "calculation_details": {"engine_version": "6d-v1"},
        }
        row_id = persistence.persist_result(self.identity_id, result)
        self.assertIsNotNone(row_id)

        history = persistence.fetch_history(self.identity_id, limit=5)
        self.assertGreaterEqual(len(history), 1)
        latest = history[0]
        self.assertEqual(latest["trust_level"], "L2_ENHANCED")
        self.assertAlmostEqual(latest["chitty_score"], 72.45, places=2)
        self.assertAlmostEqual(latest["composite_score"], 72.45, places=2)

    def test_persist_events_round_trip(self):
        events = [
            TrustEvent(
                id="e-itest-1",
                entity_id=self.did,
                event_type="verification",
                timestamp=datetime.now(timezone.utc),
                channel="verified_api",
                outcome="positive",
                impact_score=5.0,
                tags=["identity", "onboarding"],
                metadata={"verifier": "ChittyAuth"},
            ),
            TrustEvent(
                id="e-itest-2",
                entity_id=self.did,
                event_type="endorsement",
                timestamp=datetime.now(timezone.utc),
                channel="blockchain",
                outcome="positive",
                impact_score=4.0,
            ),
        ]
        inserted = persistence.persist_events(self.identity_id, events)
        self.assertEqual(inserted, 2)

        with persistence._conn() as c, c.cursor() as cur:
            cur.execute(
                "SELECT event_type, outcome FROM chittyscore.events "
                "WHERE identity_id = %s ORDER BY event_type",
                (str(self.identity_id),),
            )
            rows = cur.fetchall()
        types = sorted(r[0] for r in rows)
        self.assertIn("verification", types)
        self.assertIn("endorsement", types)
        for _, outcome in rows:
            self.assertEqual(outcome, "positive")


if __name__ == "__main__":
    unittest.main()
