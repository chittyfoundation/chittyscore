"""
ChittyScore Flask Application
6D Behavioral Trust Scoring Engine
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import Dict, Any

from flask import Flask, request, jsonify
from flask_cors import CORS

from src.chitty_score.models import TrustEntity, TrustEvent, Credential, Connection
from src.chitty_score.dimensions import (
    SourceDimension, TemporalDimension, ChannelDimension,
    OutcomeDimension, NetworkDimension, JusticeDimension
)
from src.chitty_score.analytics import TrustAnalytics

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['JSON_SORT_KEYS'] = False
DATABASE_URL = os.getenv('DATABASE_URL', '')
PORT = int(os.getenv('PORT', 5000))


def utc_now_iso() -> str:
    """Return a timezone-aware UTC ISO timestamp."""
    return datetime.now(timezone.utc).isoformat()

# Dimension weights (must sum to 100%)
DIMENSION_WEIGHTS = {
    'source': 0.15,      # 15%
    'temporal': 0.10,    # 10%
    'channel': 0.15,     # 15%
    'outcome': 0.20,     # 20%
    'network': 0.15,     # 15%
    'justice': 0.25,     # 25%
}


class TrustEngine:
    """Core trust calculation engine."""

    def __init__(self):
        self.dimensions = {
            'source': SourceDimension(),
            'temporal': TemporalDimension(),
            'channel': ChannelDimension(),
            'outcome': OutcomeDimension(),
            'network': NetworkDimension(),
            'justice': JusticeDimension(),
        }
        self.analytics = TrustAnalytics()

    async def calculate_trust(
        self,
        entity: TrustEntity,
        events: list[TrustEvent]
    ) -> Dict[str, Any]:
        """Calculate 6D trust score and generate insights."""

        # Calculate each dimension
        dimension_scores = {}
        for name, dimension in self.dimensions.items():
            score = await dimension.calculate(entity, events)
            dimension_scores[name] = round(score, 2)

        # Calculate composite score (weighted average)
        composite_score = sum(
            dimension_scores[dim] * weight
            for dim, weight in DIMENSION_WEIGHTS.items()
        )

        # Calculate output scores
        people_score = self._calculate_people_score(dimension_scores)
        legal_score = self._calculate_legal_score(dimension_scores)
        state_score = self._calculate_state_score(dimension_scores)
        chitty_score = self._calculate_chitty_score(dimension_scores)

        # Determine trust level
        trust_level = self._get_trust_level(composite_score)

        # Generate insights
        insights = await self.analytics.generate_insights(
            entity, events, dimension_scores
        )

        # Calculate confidence based on data quality
        confidence = self._calculate_confidence(entity, events)

        return {
            'composite_score': round(composite_score, 2),
            'trust_level': trust_level,
            'dimension_scores': dimension_scores,
            'output_scores': {
                'people': round(people_score, 2),
                'legal': round(legal_score, 2),
                'state': round(state_score, 2),
                'chitty': round(chitty_score, 2),
            },
            'confidence': round(confidence, 2),
            'insights': [
                {
                    'category': i.category,
                    'title': i.title,
                    'description': i.description,
                    'impact': i.impact,
                    'confidence': i.confidence
                }
                for i in insights[:5]  # Top 5 insights
            ],
            'calculated_at': utc_now_iso()
        }

    def _calculate_people_score(self, scores: Dict[str, float]) -> float:
        """Interpersonal trust assessment."""
        return (scores['outcome'] * 0.4 +
                scores['network'] * 0.35 +
                scores['source'] * 0.25)

    def _calculate_legal_score(self, scores: Dict[str, float]) -> float:
        """Legal system alignment."""
        return (scores['justice'] * 0.5 +
                scores['outcome'] * 0.3 +
                scores['temporal'] * 0.2)

    def _calculate_state_score(self, scores: Dict[str, float]) -> float:
        """Institutional trust level."""
        return (scores['source'] * 0.4 +
                scores['justice'] * 0.35 +
                scores['temporal'] * 0.25)

    def _calculate_chitty_score(self, scores: Dict[str, float]) -> float:
        """Overall ChittyOS trust rating."""
        return sum(scores[dim] * weight for dim, weight in DIMENSION_WEIGHTS.items())

    def _get_trust_level(self, score: float) -> str:
        """Map score to ChittyID lifecycle level."""
        if score >= 90:
            return 'L4_INSTITUTIONAL'
        elif score >= 75:
            return 'L3_PROFESSIONAL'
        elif score >= 50:
            return 'L2_ENHANCED'
        elif score >= 25:
            return 'L1_BASIC'
        else:
            return 'L0_ANONYMOUS'

    def _calculate_confidence(self, entity: TrustEntity, events: list[TrustEvent]) -> float:
        """Calculate confidence in the trust score."""
        confidence = 50.0  # Base confidence

        # More events = higher confidence
        if len(events) > 100:
            confidence += 30
        elif len(events) > 50:
            confidence += 20
        elif len(events) > 10:
            confidence += 10

        # Identity verification increases confidence
        if entity.identity_verified:
            confidence += 15

        # Credentials increase confidence
        confidence += min(len(entity.credentials) * 2, 10)

        return min(confidence, 100)


# Initialize engine
engine = TrustEngine()


# Routes
@app.route('/')
def index():
    """API information."""
    return jsonify({
        'service': 'ChittyScore API',
        'version': '1.0.0',
        'description': '6D Behavioral Trust Scoring Engine',
        'endpoints': {
            'health': '/api/health',
            'calculate': '/api/trust/calculate',
            'demo_personas': '/api/trust/demo/<persona_id>'
        }
    })


@app.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'chittyscore',
        'timestamp': utc_now_iso()
    })


@app.route('/api/trust/calculate', methods=['POST'])
def calculate_trust():
    """Calculate trust score for an entity."""
    try:
        data = request.get_json()

        # Parse entity
        entity = TrustEntity(**data['entity'])

        # Parse events
        events = [TrustEvent(**e) for e in data.get('events', [])]

        # Calculate trust (async)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(engine.calculate_trust(entity, events))
        loop.close()

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'CALCULATION_ERROR',
                'message': str(e)
            }
        }), 400


@app.route('/api/trust/demo/<persona_id>')
def demo_persona(persona_id: str):
    """Get trust score for demo persona (alice, bob, charlie)."""
    demo_data = get_demo_persona_data(persona_id)

    if not demo_data:
        return jsonify({
            'success': False,
            'error': {
                'code': 'PERSONA_NOT_FOUND',
                'message': f'Demo persona {persona_id} not found'
            }
        }), 404

    # Calculate trust
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(
        engine.calculate_trust(demo_data['entity'], demo_data['events'])
    )
    loop.close()

    return jsonify({
        'success': True,
        'data': {
            'persona_id': persona_id,
            'name': demo_data['entity'].name,
            'description': demo_data['description'],
            'trust_score': result
        }
    })


def get_demo_persona_data(persona_id: str) -> Dict[str, Any] | None:
    """Get demo persona data."""
    personas = {
        'alice': {
            'description': 'High-trust community leader',
            'entity': TrustEntity(
                id='alice',
                entity_type='person',
                name='Alice Chen',
                created_at=datetime(2020, 1, 1),
                identity_verified=True,
                credentials=[
                    Credential(
                        type='government_id',
                        issuer='US Government',
                        issued_at=datetime(2020, 1, 1)
                    ),
                    Credential(
                        type='professional',
                        issuer='State Bar Association',
                        issued_at=datetime(2020, 6, 1)
                    )
                ],
                connections=[
                    Connection(
                        entity_id='bob',
                        connection_type='professional',
                        established_at=datetime(2021, 1, 1),
                        trust_score=85,
                        interaction_count=50
                    )
                ],
                transparency_level=0.9
            ),
            'events': [
                TrustEvent(
                    id='e1',
                    entity_id='alice',
                    event_type='verification',
                    timestamp=datetime(2020, 1, 15),
                    channel='verified_api',
                    outcome='positive',
                    impact_score=5.0
                ),
                TrustEvent(
                    id='e2',
                    entity_id='alice',
                    event_type='endorsement',
                    timestamp=datetime(2021, 3, 10),
                    channel='blockchain',
                    outcome='positive',
                    impact_score=4.0
                )
            ]
        },
        'bob': {
            'description': 'Mixed business history',
            'entity': TrustEntity(
                id='bob',
                entity_type='person',
                name='Bob Martinez',
                created_at=datetime(2019, 6, 1),
                identity_verified=True,
                credentials=[
                    Credential(
                        type='government_id',
                        issuer='US Government',
                        issued_at=datetime(2019, 6, 1)
                    )
                ],
                connections=[],
                transparency_level=0.6
            ),
            'events': [
                TrustEvent(
                    id='e3',
                    entity_id='bob',
                    event_type='transaction',
                    timestamp=datetime(2020, 2, 1),
                    channel='bank_transfer',
                    outcome='positive',
                    impact_score=3.0
                ),
                TrustEvent(
                    id='e4',
                    entity_id='bob',
                    event_type='dispute',
                    timestamp=datetime(2021, 8, 15),
                    channel='email',
                    outcome='negative',
                    impact_score=2.0
                )
            ]
        },
        'charlie': {
            'description': 'Shitty to Chitty transformation story',
            'entity': TrustEntity(
                id='charlie',
                entity_type='person',
                name='Charlie Williams',
                created_at=datetime(2022, 1, 1),
                identity_verified=False,
                credentials=[],
                connections=[],
                transparency_level=0.4
            ),
            'events': [
                TrustEvent(
                    id='e5',
                    entity_id='charlie',
                    event_type='dispute',
                    timestamp=datetime(2022, 2, 1),
                    channel='email',
                    outcome='negative',
                    impact_score=3.0
                ),
                TrustEvent(
                    id='e6',
                    entity_id='charlie',
                    event_type='achievement',
                    timestamp=datetime(2023, 10, 1),
                    channel='verified_api',
                    outcome='positive',
                    impact_score=8.0,
                    tags=['rehabilitation', 'transformation']
                )
            ]
        }
    }

    return personas.get(persona_id)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=PORT)
