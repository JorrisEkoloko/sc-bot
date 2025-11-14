# MCP Verification Server - Crypto Intelligence Rebuild

## Purpose

This MCP (Model Context Protocol) server provides phase-by-phase verification and guidance for implementing the crypto intelligence system rebuild. Each phase has focused endpoints that verify understanding, validate implementation decisions, and ensure proper progression.

## Structure

```
mcp-verification-server/
├── README.md (this file)
├── phase-0-understanding.json
├── phase-1-environment.json
├── phase-2-planning.json
├── phase-3-core-foundation.json
├── phase-4-intelligence-layer.json
├── phase-5-supporting-systems.json
├── phase-6-integration.json
└── phase-7-deployment.json
```

## How It Works

1. **Before Starting a Phase**: AI must answer verification questionnaire
2. **During Phase**: Endpoints verify logic and implementation decisions
3. **After Phase**: Validation checklist confirms completion
4. **Progression Gate**: Must pass all checks before moving to next phase

## Phase Overview

- **Phase 0**: Understanding (verify comprehension of system and approach)
- **Phase 1**: Environment Setup (verify credentials and configuration)
- **Phase 2**: Planning (verify migration strategy and component mapping)
- **Phase 3**: Core Foundation (verify 6 core components)
- **Phase 4**: Intelligence Layer (verify 6 intelligence components)
- **Phase 5**: Supporting Systems (verify discovery, validation, utilities)
- **Phase 6**: Integration (verify configuration and orchestration)
- **Phase 7**: Deployment (verify production readiness)

## Usage

Each phase JSON file contains:

- **Pre-Phase Questionnaire**: Questions AI must answer before starting
- **Verification Endpoints**: Logic checks during implementation
- **Validation Checklist**: Completion criteria
- **Progression Gate**: Requirements to move to next phase

## Integration with AI Agent

The AI agent should:

1. Load the appropriate phase JSON
2. Answer all pre-phase questions
3. Use verification endpoints during implementation
4. Complete validation checklist
5. Pass progression gate before moving forward

This ensures systematic, verified implementation with no skipped steps or misunderstood requirements.
