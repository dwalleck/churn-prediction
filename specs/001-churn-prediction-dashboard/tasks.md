# Tasks: Customer Churn Prediction Dashboard

**Feature**: 001-churn-prediction-dashboard
**Input**: Design documents from `/home/dwalleck/repos/churn-prediction/specs/001-churn-prediction-dashboard/`
**Prerequisites**: spec.md, plan.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure needed by all components

- [X] T001 Create project directory structure at /home/dwalleck/repos/churn-prediction/ per plan.md
- [X] T002 Initialize Python 3.12 project with uv and create pyproject.toml with dependencies (xgboost, scikit-learn, pandas, numpy, streamlit, plotly, boto3, pytest)
- [X] T003 [P] Create .python-version file specifying Python 3.12
- [X] T004 [P] Create .gitignore for Python project (venv, __pycache__, data/raw/, models/, .env)
- [X] T005 [P] Create data/ directory structure with subdirectories: raw/, processed/, models/, scores/
- [X] T006 [P] Create all source directories: src/churn_predictor/data/, src/churn_predictor/models/, src/churn_predictor/analytics/, src/churn_predictor/storage/, src/churn_predictor/cli/, src/dashboard/pages/, src/dashboard/services/
- [X] T007 [P] Create tests/ directory structure: tests/unit/, tests/integration/, tests/fixtures/
- [X] T008 [P] Create __init__.py files in all Python package directories

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

### Core Data Layer

- [X] T009 [P] Create custom exceptions in src/churn_predictor/exceptions.py (ChurnPredictorError, ValidationError, ModelError, StorageError)
- [X] T010 [P] Create ValidationResult dataclass in src/churn_predictor/data/validator.py
- [X] T011 Implement load_csv() function in src/churn_predictor/data/loader.py per ML Pipeline API contract
- [X] T012 Implement validate_schema() function in src/churn_predictor/data/validator.py per ML Pipeline API contract
- [X] T013 Implement preprocess() function in src/churn_predictor/data/preprocessor.py with feature engineering (tenure_months, transaction_change_pct, revenue_change_pct, days_since_last_touchbase, ticket_escalation_rate, revenue_per_transaction)

### Core ML Infrastructure

- [X] T014 Create TrainedModel dataclass in src/churn_predictor/models/trainer.py with save() and load() methods per ML Pipeline API contract
- [X] T015 Implement train_model() function in src/churn_predictor/models/trainer.py using XGBoost with class weighting, F2 score optimization, and default hyperparameters
- [X] T016 Implement predict_churn() function in src/churn_predictor/models/predictor.py with risk level mapping (0-30 low, 31-69 medium, 70-100 high)
- [X] T017 Implement explain_predictions() function in src/churn_predictor/models/explainer.py using SHAP TreeExplainer for top 3 risk factors

### Core Storage Layer

- [ ] T018 Create AWS client wrappers in src/churn_predictor/storage/aws_clients.py (S3Client, DynamoDBClient with connection pooling and error handling)
- [X] T019 Implement LocalStorage class in src/churn_predictor/storage/local_storage.py with save_scores(), load_scores(), get_high_risk_customers() methods (simplified for MVP)
- [ ] T020 [P] Implement ModelRepository class in src/churn_predictor/storage/repositories.py with save_model(), get_active_model(), list_models() methods
- [ ] T021 [P] Implement ChurnEventRepository class in src/churn_predictor/storage/repositories.py with save_events(), get_churn_events() methods

### CLI Foundation

- [X] T022 Create CLI entry point in src/churn_predictor/cli/__main__.py with command routing
- [X] T023 Implement CLI train command in src/churn_predictor/cli/commands.py with options: --data, --output (simplified for MVP)
- [X] T024 [P] Implement CLI score command in src/churn_predictor/cli/commands.py with options: --data, --model, --output (simplified for MVP)
- [X] T025 [P] Implement CLI validate command in src/churn_predictor/cli/commands.py with options: --data

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 4 - Generate Churn Scores (Priority: P1)

**Goal**: System administrators can process customer data to generate churn probability scores (0-100) so that dashboard can display current risk levels

**Independent Test**: Upload customer CSV and verify each customer receives a churn probability score between 0-100

**Why this blocks dashboard**: US1, US2, and US3 all require churn scores to exist. This is the foundational data generation capability.

### Implementation for User Story 4

- [X] T026 [US4] Create ChurnScore entity model class in src/churn_predictor/models/entities.py mapping to data-model.md ChurnScore entity (account_id, score_date, churn_probability, risk_level, confidence, model_version, top_risk_factors, created_at)
- [X] T027 [US4] Add model versioning logic to train_model() in src/churn_predictor/models/trainer.py (semantic versioning: major.minor.patch)
- [X] T028 [US4] Implement batch scoring via CLI (simplified: train and score commands combine the pipeline functionality)
- [ ] T029 [US4] Add DynamoDB table schema creation script in scripts/deploy/create_dynamodb_tables.py for churn-scores table with GSI (risk_level, churn_probability)
- [X] T030 [US4] Implement score persistence via LocalStorage.save_scores() (file-based for MVP, DynamoDB for production)
- [X] T031 [US4] Add error handling for incomplete customer data per FR-015 in src/churn_predictor/data/validator.py (graceful handling of missing values)
- [X] T032 [US4] sample-data.csv exists in repository root (provided)

**Checkpoint**: User Story 4 complete - can upload CSV and generate churn scores. This enables all dashboard features.

---

## Phase 4: User Story 1 - View High-Risk Customers (Priority: P1) - MVP Dashboard

**Goal**: Account managers identify customers most likely to churn in next 60-90 days with actionable recommendations

**Independent Test**: View dashboard showing high-risk customers with recommendations for each

**Why MVP**: This delivers immediate value - preventing customer loss through early identification (SC-001)

### Recommendation Engine for User Story 1

- [ ] T033 [P] [US1] Create ActionableRecommendation entity model class in src/churn_predictor/models/entities.py mapping to data-model.md (account_id, recommendation_id, action_type, priority, description, rationale, estimated_impact, created_at)
- [ ] T034 [US1] Implement generate_recommendations() function in src/churn_predictor/analytics/recommendations.py with rule-based logic per ML Pipeline API contract (days_since_last_touchbase > 60 → immediate_contact, revenue_change_pct < -30% → offer_discount, ticket_escalation_rate > 50% → review_service, tenure_months < 3 → schedule_training)
- [ ] T035 [US1] Add recommendation generation to scoring pipeline in src/churn_predictor/pipeline/scoring.py for high-risk customers (score >= 70)

### Dashboard Infrastructure for User Story 1

- [ ] T036 [P] [US1] Create DataService class in src/dashboard/services/data_service.py with caching decorators and repository injection
- [ ] T037 [P] [US1] Implement get_high_risk_customers() method in src/dashboard/services/data_service.py querying DynamoDB GSI with caching (ttl=300)
- [ ] T038 [P] [US1] Implement get_customer_details() method in src/dashboard/services/data_service.py
- [ ] T039 [P] [US1] Implement get_score() method in src/dashboard/services/data_service.py
- [ ] T040 [P] [US1] Implement get_recommendations() method in src/dashboard/services/data_service.py
- [ ] T041 [US1] Implement optimistic locking or last-write-wins strategy in src/dashboard/services/data_service.py to handle concurrent customer access by multiple account managers per edge case (spec.md:80)
- [ ] T042 [P] [US1] Implement get_summary_metrics() method in src/dashboard/services/data_service.py for homepage metrics

### Dashboard UI for User Story 1

- [X] T043 [US1] Create Streamlit main app in src/dashboard/app.py with page config, navigation, and summary metrics per Dashboard API contract
- [X] T044 [US1] Create high-risk customers page in src/dashboard/pages/1_High_Risk_Customers.py with score threshold slider (default 70), max results selector (20/50/100/200), and interactive dataframe per Dashboard API contract
- [X] T045 [US1] Implement customer_details display in src/dashboard/pages/1_High_Risk_Customers.py showing score, confidence, top risk factors, and placeholder recommendations
- [X] T046 [US1] Add error handling and empty state messages in src/dashboard/pages/1_High_Risk_Customers.py per Dashboard API contract error handling patterns
- [X] T047 [US1] Create Streamlit config in .streamlit/config.toml with theme, server settings, and security options

**Checkpoint**: User Story 1 (MVP) complete - Dashboard shows high-risk customers with actionable recommendations. Validates SC-001 (identify top 20 in <30 seconds) and SC-006 (recommendations for 100% of high-risk customers).

---

## Phase 5: User Story 2 - Understand Churn Drivers (Priority: P2)

**Goal**: Business leaders understand which factors most strongly predict churn to inform strategic decisions

**Independent Test**: View variable importance analysis showing top predictive features with relative impact scores

### Implementation for User Story 2

- [ ] T047 [P] [US2] Create ModelMetadata entity model class in src/churn_predictor/models/entities.py mapping to data-model.md (model_version, trained_at, training_data_path, model_artifact_path, algorithm, hyperparameters, performance_metrics, feature_importance, is_active)
- [ ] T048 [US2] Add feature importance extraction to train_model() in src/churn_predictor/models/trainer.py using XGBoost's get_score() with importance_type='gain'
- [ ] T049 [US2] Implement model metadata persistence in ModelRepository.save_model() to DynamoDB model-metadata table
- [ ] T050 [P] [US2] Implement get_active_model_metadata() method in src/dashboard/services/data_service.py with caching (ttl=3600)
- [ ] T051 [P] [US2] Implement get_feature_distribution() method in src/dashboard/services/data_service.py to analyze feature values by churn status with statistical insights
- [ ] T052 [US2] Create churn drivers page in src/dashboard/pages/2_Churn_Drivers.py showing model version, F2 score, top 10 feature importance bar chart using Plotly per Dashboard API contract
- [ ] T053 [US2] Add feature distribution analysis component in src/dashboard/pages/2_Churn_Drivers.py with feature selector, box plot by churn status, and statistical insight text
- [ ] T054 [US2] Add optional segment analysis in src/dashboard/pages/2_Churn_Drivers.py (segment by contract type or tenure bracket) showing comparative feature importance

**Checkpoint**: User Story 2 complete - Leaders can view variable importance and understand churn drivers. Validates SC-003 (understand top 5 variables in <1 minute) and SC-009 (explains ≥70% of factors).

---

## Phase 6: User Story 3 - Analyze Churn Reasons (Priority: P3)

**Goal**: Leadership groups historical churned customers by reason to identify patterns and prioritize improvements

**Independent Test**: View churn reason distribution with counts/percentages and trends over time

### Implementation for User Story 3

- [ ] T055 [P] [US3] Create ChurnEvent entity model class in src/churn_predictor/models/entities.py mapping to data-model.md (event_id, account_id, churn_date, churn_reason_category, churn_reason_detail, final_revenue, final_transactions, tenure_at_churn, created_at)
- [ ] T056 [US3] Implement churn event extraction in src/churn_predictor/analytics/churn_reasons.py to identify churned customers (churned=1) and categorize reasons
- [ ] T057 [US3] Add churn event persistence to scoring pipeline in src/churn_predictor/pipeline/scoring.py writing to DynamoDB churn-events table
- [ ] T058 [US3] Create DynamoDB churn-events table schema in scripts/deploy/create_dynamodb_tables.py with GSI (churn_reason_category, churn_date)
- [ ] T059 [P] [US3] Implement get_churn_events() method in src/dashboard/services/data_service.py with date range filtering and caching (ttl=3600)
- [ ] T060 [US3] Create churn reasons page in src/dashboard/pages/3_Churn_Reasons.py with date range filters (start_date, end_date), summary metrics (total churned, avg tenure, revenue lost)
- [ ] T061 [US3] Add churn reason breakdown visualizations in src/dashboard/pages/3_Churn_Reasons.py with pie chart, top 3 reasons list, and trend line chart over time
- [ ] T062 [US3] Add detailed churn event table in src/dashboard/pages/3_Churn_Reasons.py showing account_id, churn_date, churn_reason_category, tenure_at_churn, final_revenue

**Checkpoint**: User Story 3 complete - Leadership can analyze historical churn patterns by reason. Validates SC-002 (top 3 reasons in <2 minutes) and SC-010 (categorization covers ≥90% of churned customers).

---

## Phase 7: AWS Deployment Infrastructure

**Purpose**: Production deployment to AWS Lambda and Fargate per research.md and plan.md architecture

### Lambda Deployment (Weekly ML Pipeline)

- [ ] T063 [P] Create Lambda handler in lambda/scoring_pipeline/handler.py that triggers on S3 CSV upload, executes full pipeline (load → validate → preprocess → train/score → save to DynamoDB)
- [ ] T064 [P] Create Lambda requirements.txt in lambda/scoring_pipeline/ with minimal dependencies (xgboost, pandas, boto3, no heavy dev dependencies)
- [ ] T065 [P] Create Lambda deployment script in scripts/deploy/deploy_lambda.sh packaging code, uploading to S3, creating/updating Lambda function with 3GB memory, 900s timeout, Python 3.12 runtime
- [ ] T066 [P] Create S3 event trigger configuration in scripts/deploy/s3-trigger-config.json for Lambda invocation on CSV upload to uploads/ prefix

### Fargate Deployment (Always-On Dashboard)

- [ ] T067 [P] Create Dockerfile in dashboard/Dockerfile for Streamlit app with Python 3.12 base image, dependencies installation, health check endpoint
- [ ] T068 [P] Create ECS task definition in scripts/deploy/ecs-task-definition.json with 0.5 vCPU, 1GB RAM, environment variables for AWS resources
- [ ] T069 [P] Create Fargate deployment script in scripts/deploy/deploy_fargate.sh building Docker image, pushing to ECR, creating/updating ECS service with ALB
- [ ] T070 [P] Create CloudWatch monitoring script in scripts/deploy/setup_monitoring.py with dashboards for Lambda execution time, DynamoDB read/write units, Fargate CPU/memory, dashboard user count

### Infrastructure as Code

- [ ] T071 Create S3 bucket creation script in scripts/deploy/create_s3_buckets.sh for churn-data (raw uploads, processed, predictions) and churn-models buckets
- [ ] T072 Add IAM roles and policies in scripts/deploy/create_iam_roles.py for Lambda execution role (S3 read, DynamoDB write, CloudWatch logs) and Fargate task role (DynamoDB read)
- [ ] T073 Create environment configuration template in .env.template with all required AWS resource names (AWS_REGION, S3_DATA_BUCKET, S3_MODEL_BUCKET, DYNAMODB_SCORES_TABLE, DYNAMODB_EVENTS_TABLE, DYNAMODB_METADATA_TABLE)

---

## Phase 8: Data Quality & Model Improvements

**Purpose**: Enhanced synthetic data generation and model features per research.md recommendations

### Improved Synthetic Data

- [ ] T074 [P] Implement enhanced data generator in src/churn_predictor/data/synthetic.py with temporal trends (declining engagement 2-3 months before churn), RFM features, customer lifecycle features (tenure_months, contract_type, months_until_renewal)
- [ ] T075 [P] Add churn cohort simulation in src/churn_predictor/data/synthetic.py with realistic patterns (early churn months 1-3, renewal churn, gradual disengagement, service quality issues, competitive loss)
- [ ] T076 Add CLI generate-data command in src/churn_predictor/cli/commands.py with options: --output, --num-customers, --churn-rate, --include-temporal-trends
- [ ] T077 Create enhanced sample-data.csv with 10,000 customers, realistic churn cohorts, temporal patterns, RFM features for production-quality testing

### Model Enhancements

- [ ] T078 Add temporal validation split logic to train_model() in src/churn_predictor/models/trainer.py (train on months 1-6, validate on month 7, test on month 8+) to prevent data leakage
- [ ] T079 Add threshold optimization in src/churn_predictor/models/trainer.py to maximize F2 score instead of using default 0.5 threshold
- [ ] T080 Implement model comparison utility in scripts/compare_models.py to evaluate multiple model versions on F2 score, PR-AUC, lift at 10%, and recommend best model

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Finalization, documentation, and validation

### Documentation

- [ ] T081 [P] Create comprehensive README.md in repository root based on quickstart.md with setup instructions, usage examples, architecture overview
- [ ] T082 [P] Create CONTRIBUTING.md with development setup, code style guidelines, testing requirements, PR process
- [ ] T083 [P] Add inline code documentation (docstrings) to all public functions ensuring error messages follow contract requirements (what, why, how to fix)

### Performance & Monitoring

- [ ] T084 Add performance logging in src/churn_predictor/pipeline/scoring.py tracking: CSV load time, preprocessing time, model inference time, DynamoDB write time with CloudWatch metrics
- [ ] T085 Implement dashboard performance monitoring in src/dashboard/app.py tracking query execution times, cache hit rates, error rates
- [ ] T086 Verify Fargate auto-scaling configuration in infrastructure/fargate-task-definition.json supports 50 concurrent users with appropriate CPU/memory limits and scaling policies
- [ ] T087 Create load testing script in tests/load/locust_dashboard.py simulating 50 concurrent users per SC-008 with target <2 second p95 latency

### Validation & Testing

- [ ] T088 Create quickstart validation script in scripts/validate_quickstart.sh that runs through all quickstart.md steps (setup, train, score, launch dashboard) and verifies success in <5 minutes
- [ ] T089 Run constitution compliance check ensuring all features align with project principles (ship it, developer experience, make it work first, fail fast)
- [ ] T090 Validate all success criteria: SC-001 (top 20 in <30s), SC-002 (top 3 reasons in <2 min), SC-003 (top 5 variables in <1 min), SC-006 (100% recommendations for high-risk), SC-008 (50 concurrent users), SC-009 (≥70% factor explanation), SC-010 (≥90% categorization)
- [ ] T091 Create deployment checklist in docs/deployment-checklist.md verifying AWS resources, environment variables, IAM permissions, monitoring dashboards, cost alerts

### Security & Compliance

- [ ] T092 [P] Implement data encryption validation in scripts/verify_encryption.py checking S3 SSE-S3, DynamoDB encryption at rest, TLS 1.2+ for all connections
- [ ] T093 [P] Add input sanitization in src/churn_predictor/data/validator.py to prevent CSV injection attacks, validate file sizes (<100MB), check for malicious content
- [ ] T094 [P] Create data retention policy script in scripts/enforce_retention.py to delete customer data >2 years old, keep last 5 model versions, rotate logs after 90 days

### Testing (TDD per Constitution Section IX)

**Note**: Write tests FIRST, ensure they FAIL before implementation, then make them pass

#### Unit Tests

- [ ] T095 [P] Unit test for CSV loader in tests/unit/test_data_loader.py verifying load_csv() handles valid files, invalid formats, missing columns, file size limits
- [ ] T096 [P] Unit test for data validator in tests/unit/test_validator.py checking ValidationResult for all edge cases (missing data, outliers, class balance warnings)
- [ ] T097 [P] Unit test for preprocessor in tests/unit/test_preprocessor.py validating derived features (tenure_months, transaction_change_pct, days_since_last_touchbase) calculated correctly
- [ ] T098 [P] Unit test for model trainer in tests/unit/test_trainer.py verifying train_model() returns TrainedModel with valid metrics (f2_score, pr_auc), feature_importance, optimal_threshold
- [ ] T099 [P] Unit test for predictor in tests/unit/test_predictor.py checking predict_churn() generates scores 0-100, risk levels (low/medium/high), top_risk_factors
- [ ] T100 [P] Unit test for explainer (SHAP) in tests/unit/test_explainer.py validating explain_predictions() returns top N features with normalized importance
- [ ] T101 [P] Unit test for recommendation engine in tests/unit/test_recommendations.py verifying generate_recommendations() applies rules correctly (days_since_touchbase, revenue_change, ticket_escalation, tenure)
- [ ] T102 [P] Unit test for churn reasons analyzer in tests/unit/test_churn_reasons.py checking categorization logic and aggregation

#### Integration Tests

- [ ] T103 Integration test for end-to-end ML pipeline in tests/integration/test_pipeline.py: load CSV → validate → preprocess → train → predict → save to DynamoDB
- [ ] T104 Integration test for DynamoDB operations in tests/integration/test_storage.py: save_scores(), get_score(), get_high_risk_customers() with real DynamoDB Local
- [ ] T105 Integration test for dashboard data service in tests/integration/test_dashboard.py: verify queries return expected data structures for all 3 dashboard pages
- [ ] T106 Integration test for CSV → scores → dashboard workflow in tests/integration/test_workflow.py: upload sample-data.csv, generate scores, verify dashboard displays top 20 customers in <30s (SC-001)

#### Contract Tests

- [ ] T107 [P] Contract test for ChurnScore schema in tests/contract/test_churn_score_contract.py validating DynamoDB item structure matches data-model.md
- [ ] T108 [P] Contract test for ActionableRecommendation schema in tests/contract/test_recommendation_contract.py verifying recommendation format consistency
- [ ] T109 [P] Contract test for ChurnEvent schema in tests/contract/test_churn_event_contract.py checking churn reason categories match specification

### Success Criteria Validation

- [ ] T110 [P] Create recommendation feedback mechanism in src/dashboard/components/feedback.py allowing account managers to rate recommendations (Yes/No: "Was this helpful?")
- [ ] T111 [P] Add feedback analytics dashboard view in src/dashboard/pages/4_Recommendation_Analytics.py tracking SC-007 (80% relevance metric) with visualizations of feedback over time

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 4 (Phase 3)**: Depends on Foundational phase - BLOCKS dashboard (US1, US2, US3) because they need churn scores
- **User Story 1 (Phase 4)**: Depends on Foundational AND US4 completion - MVP dashboard
- **User Story 2 (Phase 5)**: Depends on Foundational AND US4 completion - Independent from US1
- **User Story 3 (Phase 6)**: Depends on Foundational AND US4 completion - Independent from US1/US2
- **AWS Deployment (Phase 7)**: Depends on US1/US2/US3/US4 completion - All features must work locally first
- **Data Quality (Phase 8)**: Can start after Foundational - Enhances existing features
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### Critical Path for MVP

```
Setup (Phase 1)
    ↓
Foundational (Phase 2) ← CRITICAL BLOCKER
    ↓
User Story 4 (Phase 3) ← GENERATES DATA FOR DASHBOARD
    ↓
User Story 1 (Phase 4) ← MVP DASHBOARD
    ↓
Deploy MVP (subset of Phase 7)
```

### User Story Independence

After Foundational (Phase 2) and US4 (Phase 3) are complete:

- **US1 (P1)**: Can proceed independently - builds dashboard for high-risk customers
- **US2 (P2)**: Can proceed in parallel with US1 - builds variable importance view (different dashboard page)
- **US3 (P3)**: Can proceed in parallel with US1/US2 - builds churn reasons view (different dashboard page)

### Within Each Phase

**Phase 2 (Foundational)**: Must be sequential
1. T009-T010 (exceptions/validation) first
2. T011-T013 (data layer) depends on T009-T010
3. T014-T017 (ML layer) depends on T011-T013
4. T018-T021 (storage layer) can run parallel with T014-T017
5. T022-T025 (CLI) depends on all above

**Phase 3 (US4)**: Sequential
1. T026-T027 (entity models)
2. T028 (pipeline) depends on T026-T027
3. T029-T030 (storage) depends on T028
4. T031-T032 (validation/sample data) can run in parallel

**Phase 4 (US1)**: Two parallel streams that merge
- Stream A: T033-T035 (recommendation engine)
- Stream B: T036-T041 (data service infrastructure)
- Merge: T042-T046 (dashboard UI) depends on both streams

**Phase 5 (US2)**: Can fully parallelize with US1/US3
- T047-T049 (model metadata)
- T050-T051 (data service additions)
- T052-T054 (dashboard page)

**Phase 6 (US3)**: Can fully parallelize with US1/US2
- T055-T058 (churn events infrastructure)
- T059 (data service additions)
- T060-T062 (dashboard page)

**Phase 7 (AWS)**: All tasks [P] can run in parallel
- T063-T066 (Lambda) independent stream
- T067-T070 (Fargate) independent stream
- T071-T073 (Infrastructure) independent stream

**Phase 8 (Data Quality)**: All tasks [P] can run in parallel

**Phase 9 (Polish)**: Most tasks [P] can run in parallel except:
- T089 depends on all features complete
- T090 depends on Phase 7 complete

### Parallel Opportunities

**Maximum Parallelization** (with 4 developers after Phase 2+3 complete):
- Developer 1: User Story 1 (T033-T046)
- Developer 2: User Story 2 (T047-T054)
- Developer 3: User Story 3 (T055-T062)
- Developer 4: Data Quality improvements (T074-T080)

All can work simultaneously without conflicts.

---

## Implementation Strategy

### MVP First (Fastest Path to Value)

**Goal**: Working dashboard showing high-risk customers with recommendations in 2-3 days

```
Day 1: Foundation
- Complete Phase 1: Setup (T001-T008)
- Complete Phase 2: Foundational (T009-T025)

Day 2: Data Generation + Core Dashboard
- Complete Phase 3: User Story 4 (T026-T032)
- Complete Phase 4: User Story 1 (T033-T046)

Day 3: Validation + Deploy
- Run quickstart validation (T087)
- Test locally with sample data
- Deploy to AWS (subset of Phase 7: T063-T069)
```

**Checkpoint**: MVP deployed - account managers can view high-risk customers with recommendations

### Incremental Delivery (Full Feature Set)

**Week 1**: MVP (Setup + Foundational + US4 + US1)
- Delivers: Dashboard showing high-risk customers with recommendations
- Validates: SC-001, SC-006

**Week 2**: Add Intelligence (US2 + US3)
- Delivers: Variable importance analysis + churn reason analytics
- Validates: SC-002, SC-003, SC-009, SC-010

**Week 3**: Production Polish (Phase 7-9)
- Delivers: AWS deployment, monitoring, enhanced data quality
- Validates: SC-008, all security/compliance requirements

### Parallel Team Strategy (4 Developers)

**Week 1**: All together
- Complete Phase 1 (Setup) together
- Complete Phase 2 (Foundational) together
- Complete Phase 3 (US4) together

**Week 2**: Split into features
- Dev 1: User Story 1 (T033-T046)
- Dev 2: User Story 2 (T047-T054)
- Dev 3: User Story 3 (T055-T062)
- Dev 4: AWS Infrastructure (T063-T073)

**Week 3**: Polish & deploy
- All: Phase 9 tasks in parallel
- Final validation and deployment

---

## Notes

- **[P] marker**: Tasks marked [P] touch different files with no dependencies - can run truly in parallel
- **[Story] labels**: Map tasks to user stories for traceability - enables incremental delivery
- **File paths**: All paths are absolute from repository root for clarity
- **Independent testing**: Each user story (US1, US2, US3, US4) can be tested independently once complete
- **Foundational blocking**: Phase 2 MUST complete before any user story work begins
- **US4 blocking dashboard**: Phase 3 (Generate Scores) MUST complete before dashboard features (US1/US2/US3) can display data
- **Commit strategy**: Commit after completing each task or logical group of parallel tasks
- **Constitution compliance**: All tasks align with "ship it", "developer experience", "work→right→fast" principles
- **Cost target**: Infrastructure designed for ~$15-20/month total per research.md (Lambda ~$0.10/week, Fargate ~$15/month, DynamoDB ~$0.03/month)
- **Performance targets**:
  - ML pipeline: <120 seconds for 10k customers (SC-005)
  - Dashboard queries: <2 seconds p95 (implicit in SC-001, SC-002, SC-003)
  - 50 concurrent users supported (SC-008)
- **Test-First per Constitution**: Following TDD workflow per constitution Section IX ("TDD is mandatory"), test tasks are included in Phase 2 and Phase 9. Write tests FIRST, verify they FAIL, then implement.
