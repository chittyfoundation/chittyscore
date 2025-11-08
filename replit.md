# ChittyScore Trust Scoring Engine

## Overview

ChittyScore is a **6-dimensional behavioral trust scoring engine** built with Python/Flask. It serves as the root project in a multi-service monorepo containing several ChittyOS ecosystem services. The engine calculates trust scores across six dimensions (Source, Temporal, Channel, Outcome, Network, Justice) to provide a comprehensive 0-100 trust rating for entities.

This is part of the larger **ChittyOS ecosystem** - a suite of interconnected trust infrastructure services including ChittyFinance, ChittyVerify, ChittyPM, and others. Each service operates independently but shares common trust verification principles.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Application Structure

**Primary Stack:**
- **Backend Framework**: Python Flask with CORS enabled
- **Trust Engine**: Custom 6D scoring system (`src/chitty_score/`)
- **Database**: PostgreSQL (via `DATABASE_URL` environment variable)
- **Deployment Targets**: Replit (configured), Cloudflare Workers, Docker, Fly.io

**Design Pattern**: Monolithic Flask application with modular dimension calculators

### Trust Scoring Architecture

**Six Trust Dimensions** (weighted calculation):
1. **Source Dimension** (15%): Identity verification and credential assessment
2. **Temporal Dimension** (10%): Consistency over time, account age
3. **Channel Dimension** (15%): Multi-channel verification across platforms
4. **Outcome Dimension** (20%): Transaction success rates, dispute history
5. **Network Dimension** (15%): Connection quality and endorsement graph
6. **Justice Dimension** (25%): Legal compliance, ethical behavior

**Core Models** (`src/chitty_score/models.py`):
- `TrustEntity`: User/organization being evaluated
- `TrustEvent`: Actions affecting trust (transactions, verifications, disputes)
- `Credential`: Identity verification artifacts
- `Connection`: Network graph relationships

**Trust Engine** (`app.py`):
- Asynchronous dimension calculation
- Weighted score aggregation (dimensions must sum to 100%)
- Analytics and insights generation
- RESTful API endpoints for score queries

### Multi-Project Monorepo Structure

**Sub-Projects** (each with independent package.json and dependencies):

1. **chittyfinance/** - Financial tracking service (TypeScript/Node.js)
   - Dual deployment modes: standalone and system-integrated
   - Express backend with React/Vite frontend
   - PostgreSQL via Drizzle ORM

2. **chittyverify/** - Evidence verification service (TypeScript/Node.js)
   - ChittyChain blockchain integration for immutable evidence
   - 7-table evidence schema with chain-of-custody tracking
   - React frontend with blockchain minting capabilities

3. **chittypm/** - Project management and orchestration (TypeScript/Node.js)
   - Universal PM board replacing individual agent todo lists
   - WebSocket server for real-time collaboration
   - Claude Code SDK integration for AI agents

4. **chitty-frontend/** - React/Vite shared frontend application
   - Minimal setup with HMR and ESLint
   - Reusable UI components across services

5. **chittyassets/** - Asset management with AI capabilities
   - EXIF metadata extraction
   - Multi-provider vision API (OpenAI GPT-4V, Google Vision)
   - Real-time collaboration via WebSockets

### Database Strategy

**Per-Service Databases**:
- Each service manages its own PostgreSQL schema
- Drizzle ORM for TypeScript services
- psycopg2-binary for Python services
- Schema migrations tracked independently

**ChittyScore Tables**:
- `trust_scores`: Calculated scores per entity
- `evidence_records`: Supporting evidence for score calculations
- `verification_requests`: Identity verification tracking
- `trust_events`: Historical event log
- `ai_insights`: Automated analysis results
- `api_usage`: Rate limiting and usage tracking

### Deployment Architecture

**Multiple Deployment Paths**:

1. **Replit** (primary, pre-configured):
   - `.replit` file configured for instant deployment
   - Auto-deploys on code changes
   - Built-in PostgreSQL database

2. **Cloudflare Workers**:
   - Serverless deployment via Wrangler
   - Edge computing for low latency
   - D1 database option

3. **Docker**:
   - Containerized Flask application
   - Gunicorn WSGI server
   - Environment-based configuration

4. **Traditional VPS** (Fly.io):
   - Free tier with 3 VMs
   - Persistent storage
   - Auto-scaling capabilities

### API Design Patterns

**RESTful Endpoints**:
- `GET /api/trust/score/:entity_id` - Calculate trust score
- `POST /api/trust/event` - Record trust-affecting event
- `GET /api/trust/analytics/:entity_id` - Detailed analytics
- `POST /api/verify/credential` - Submit verification credential

**Response Format**:
```python
{
  "entity_id": "string",
  "trust_score": 0-100,
  "dimensions": {
    "source": 0-100,
    "temporal": 0-100,
    # ... other dimensions
  },
  "insights": ["string"],
  "risk_level": "low|medium|high"
}
```

### Cross-Service Integration Points

**ChittyTrust (Foundation)**:
- Root CA for cryptographic trust
- Certificate issuance for all services
- ChittyID integration for universal identity

**ChittyChain**:
- Immutable evidence recording
- Blockchain anchoring for trust events
- Cross-service audit trail

**Service Communication**:
- Shared ChittyID namespace for entity references
- Event-driven architecture via trust events
- Common authentication via ChittyTrust certificates

## External Dependencies

### Core Python Dependencies
- **Flask 3.0.0**: Web framework for API endpoints
- **Flask-CORS 4.0.0**: Cross-origin resource sharing
- **Pydantic 2.5.0**: Data validation and settings management
- **NumPy 1.24.3**: Numerical computations for scoring algorithms
- **psycopg2-binary 2.9.7**: PostgreSQL database adapter
- **python-dotenv 1.0.0**: Environment variable management
- **gunicorn 21.2.0**: Production WSGI server
- **email-validator**: Credential validation

### TypeScript Service Dependencies (chittyfinance, chittyverify, chittypm)
- **React 18**: UI framework
- **Vite**: Build tool and dev server
- **TanStack React Query**: Server state management
- **Drizzle ORM**: Type-safe database operations
- **@neondatabase/serverless**: Neon PostgreSQL client
- **Express**: Node.js web framework
- **Radix UI**: Accessible component primitives
- **Tailwind CSS**: Utility-first styling
- **shadcn/ui**: Component library

### Blockchain Dependencies (chittyverify)
- **Ethers.js**: Ethereum interaction library
- **Chainlink CCIP**: Cross-chain interoperability
- **IPFS**: Decentralized file storage

### AI/ML Dependencies (chittyassets)
- **OpenAI GPT-4V**: Vision API for asset analysis
- **Google Vision API**: Image metadata extraction
- **DOMPurify**: XSS prevention and input sanitization

### Infrastructure Services
- **Neon Database**: Serverless PostgreSQL hosting
- **Cloudflare Workers**: Edge computing platform
- **Replit**: Primary hosting and development environment
- **GitHub**: Version control and CI/CD
- **Clerk**: Authentication provider (enterprise features)
- **Stripe**: Payment processing (ChittyFinance)

### Development Tools
- **TypeScript**: Type safety across Node.js services
- **tsx**: TypeScript execution for development
- **esbuild**: Fast JavaScript bundler
- **drizzle-kit**: Database migration tool
- **Feather Icons**: Icon library for UI
- **Chart.js**: Data visualization

### Monitoring & Analytics
- **WebSocket Server**: Real-time collaboration (chittypm, chittyassets)
- **Jest + Supertest**: Testing framework (chittyassets)
- **Bootstrap 5**: UI framework (legacy templates)
- **Alpine.js**: Lightweight reactivity (some frontends)