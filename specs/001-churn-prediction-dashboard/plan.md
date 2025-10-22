# Implementation Plan: Customer Churn Prediction Dashboard

**Branch**: `001-churn-prediction-dashboard` | **Date**: 2025-10-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-churn-prediction-dashboard/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a customer churn prediction system that analyzes customer data to generate risk scores (0-100) indicating likelihood of cancellation within 60-90 days. The system will provide a dashboard for account managers to identify high-risk customers with actionable retention recommendations, analyze which variables drive churn, and categorize historical churn events by reason. Data ingestion via CSV upload, weekly score refresh cycle, Python-based ML pipeline with AWS infrastructure.

## Technical Context

**Language/Version**: Python 3.12 (managed via uv)
**Primary Dependencies**: xgboost, scikit-learn, pandas, numpy, streamlit (dashboard), plotly (visualizations), boto3 (AWS)
**Storage**: S3 (CSV uploads, model artifacts) + DynamoDB (churn scores for fast dashboard queries)
**Testing**: pytest with pytest-cov for coverage
**Target Platform**: AWS Lambda (weekly ML batch pipeline) + AWS Fargate (Streamlit dashboard hosting)
**Project Type**: Web application (ML backend + dashboard frontend)
**Performance Goals**: Score generation for 10,000 customers within weekly refresh window; dashboard response <2 seconds for queries
**Constraints**: Weekly batch processing acceptable; CSV file size <100MB; dashboard must support 50 concurrent users
**Scale/Scope**: Initial deployment ~1,000-10,000 customers; 10-15 customer attributes; 3-5 dashboard views
**Infrastructure Cost**: ~$15-20/month total (Lambda ~$0.10/week, Fargate ~$15/month, DynamoDB ~$0.03/month, S3 negligible)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gates

- [x] **Ship It**: Feature has clear success criteria (SC-001 through SC-010) and measurable outcomes
- [x] **Developer Experience**: Will include quickstart.md with 5-minute setup goal
- [x] **Make It Work First**: Plan follows work→right→fast order; weekly batch processing chosen over real-time complexity
- [x] **README-Driven**: Will write usage examples before implementation (Phase 1)
- [x] **Fail Fast**: Error handling for missing data, incomplete CSVs identified in edge cases
- [x] **Test-First**: TDD workflow planned with pytest; focus on integration tests for ML pipeline
- [x] **Iteration Over Perfection**: Starting with CSV upload (simple) before considering API/DB integrations

**Status**: ✅ PASS - No violations. Approach prioritizes shipping working software with clear user value.

### Post-Design Review

*Completed after Phase 1 design artifacts*

- [x] **API design follows progressive disclosure (simple cases simple)**
  - CLI: Simple commands (`train`, `score`) with sensible defaults
  - Dashboard: Single-click navigation, minimal configuration
  - Python API: Simple functions with helpful defaults (e.g., `validate=True`)

- [x] **Error messages are actionable**
  - All exceptions include: what failed, why, how to fix
  - Example: `"CSV validation failed: Missing required columns ['account_id', 'month']. Expected 12 columns, found 10."`
  - Dashboard shows friendly messages with troubleshooting steps

- [x] **Real example application planned**
  - Quickstart.md provides working example from zero to dashboard in <5 minutes
  - Uses sample-data.csv included in repo
  - Step-by-step CLI commands provided

- [x] **No over-engineering detected**
  - Simple CSV upload (not complex data pipeline)
  - Weekly batch (not real-time streaming)
  - DynamoDB key-value (not complex relational DB)
  - Streamlit (not custom React app)
  - XGBoost (not deep learning)

- [x] **Complexity justified in documentation**
  - research.md explains all technology choices
  - XGBoost chosen for class imbalance handling
  - DynamoDB for <10ms dashboard queries
  - Lambda for cost efficiency ($0.10/week vs $30/month always-on)

**Status**: ✅ PASS - Design adheres to constitution principles. Ready for implementation.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
churn-prediction/
├── src/
│   ├── churn_predictor/
│   │   ├── __init__.py
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   ├── loader.py          # CSV ingestion
│   │   │   ├── validator.py       # Data validation
│   │   │   └── preprocessor.py    # Feature engineering
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── trainer.py         # Model training pipeline
│   │   │   ├── predictor.py       # Score generation
│   │   │   └── explainer.py       # Variable importance (SHAP/feature importance)
│   │   ├── analytics/
│   │   │   ├── __init__.py
│   │   │   ├── churn_reasons.py   # Churn reason categorization
│   │   │   └── recommendations.py # Actionable recommendation engine
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   ├── repositories.py    # Data access layer
│   │   │   └── aws_clients.py     # AWS service wrappers
│   │   └── cli/
│   │       ├── __init__.py
│   │       └── commands.py        # CLI for training, scoring
│   └── dashboard/
│       ├── __init__.py
│       ├── app.py                 # Dashboard entry point
│       ├── components/
│       │   ├── __init__.py
│       │   ├── high_risk.py       # P1: High-risk customer view
│       │   ├── drivers.py         # P2: Variable importance view
│       │   └── reasons.py         # P3: Churn reasons view
│       └── services/
│           ├── __init__.py
│           └── data_service.py    # Dashboard data queries
│
├── tests/
│   ├── unit/
│   │   ├── test_data_loader.py
│   │   ├── test_validator.py
│   │   ├── test_trainer.py
│   │   └── test_predictor.py
│   ├── integration/
│   │   ├── test_pipeline.py       # End-to-end ML pipeline
│   │   ├── test_storage.py        # AWS integration tests
│   │   └── test_dashboard.py      # Dashboard integration
│   └── fixtures/
│       └── sample_data.csv        # Test data
│
├── data/                          # Local development data
│   ├── raw/                       # Uploaded CSVs
│   ├── processed/                 # Preprocessed features
│   └── models/                    # Trained model artifacts
│
├── notebooks/                     # Exploratory analysis (optional)
│   └── churn_analysis.ipynb
│
├── pyproject.toml                 # uv project configuration
├── README.md                      # Quickstart guide
└── .python-version                # Python 3.12
```

**Structure Decision**: Web application structure selected due to separate ML backend and dashboard frontend. The `churn_predictor` package handles data processing, ML training, and scoring. The `dashboard` package provides the user interface. This separation enables independent development and testing of ML pipeline vs. visualization components.

## Complexity Tracking

**No violations detected.** Constitution check passed. All complexity is justified and documented in research.md.

---

## Phase 1 Artifacts Summary

### ✅ Completed Deliverables

1. **research.md** (659 lines)
   - Churn modeling best practices research
   - Technology stack decisions (Streamlit, XGBoost, DynamoDB, Lambda/Fargate)
   - AWS architecture recommendations
   - Data generation improvements
   - All decisions include rationale and alternatives considered

2. **data-model.md** (480 lines)
   - 6 core entities: Customer, ChurnScore, ChurnEvent, ActionableRecommendation, ModelMetadata, plus derived features
   - DynamoDB schema with GSI indexes
   - Data flow diagrams
   - Validation rules and error handling
   - Security and privacy considerations

3. **contracts/** (2 files)
   - **ml-pipeline-api.md** (580 lines): Python API contracts for 8 modules with examples, error handling, testing requirements
   - **dashboard-api.md** (520 lines): Streamlit dashboard components, 3 page views (P1/P2/P3), data service API, caching strategy

4. **quickstart.md** (425 lines)
   - Zero to working dashboard in <5 minutes
   - Step-by-step local development guide
   - AWS deployment instructions
   - Troubleshooting section
   - Real usage examples

5. **Agent Context Updated**
   - CLAUDE.md created with Python 3.12, XGBoost, Streamlit, DynamoDB, AWS Lambda/Fargate

### 📊 Planning Metrics

- **Total documentation**: ~2,664 lines across 6 files
- **Time to complete Phase 1**: ~15 minutes (automated research + documentation generation)
- **Constitution compliance**: 100% (no violations)
- **Success criteria mapped**: 10/10 (all SC-001 through SC-010 addressed in design)

### 🎯 Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| ML Framework | XGBoost | Best for class imbalance, built-in importance, proven churn performance |
| Dashboard | Streamlit | 5-minute setup, native multi-page, perfect for data apps |
| Storage | S3 + DynamoDB | S3 for blobs, DynamoDB for fast queries (<10ms), total cost ~$0.03/month |
| Compute | Lambda + Fargate | Lambda for batch ($0.10/week), Fargate for always-on dashboard ($15/month) |
| Data Format | CSV upload | Simplest MVP, can add API later |

### 🚀 Ready for Next Phase

**Phase 2 (tasks.md generation)** can begin immediately using `/speckit.tasks` command.

**Estimated Implementation Time**: 2-3 days for MVP
- Day 1: ML pipeline (data loading, training, prediction)
- Day 2: Dashboard (3 views + data service)
- Day 3: Testing, AWS deployment, polish

**Infrastructure Cost**: ~$15-20/month for 10,000 customers
