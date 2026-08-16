# Implementation Plan: AI-Powered Restaurant Recommendation System

> **Project**: Zomato-Inspired Restaurant Recommendation Service  
> **Version**: 1.0  
> **Created**: 2026-08-16  
> **References**: [Problemstatement.md](./Problemstatement.md) | [Architecture.md](./Architecture.md)

---

## Phase Overview

| Phase | Name                          | Duration    | Key Deliverable                              |
| ----- | ----------------------------- | ----------- | -------------------------------------------- |
| 1     | Project Setup & Environment   | 1–2 days    | Repo structure, dependencies, configs        |
| 2     | Data Ingestion & Preprocessing| 2–3 days    | Cleaned Zomato dataset ready for querying    |
| 3     | Filtering & Query Engine      | 2–3 days    | User preference-based restaurant filtering   |
| 4     | LLM Integration & Prompting   | 3–4 days    | Working recommendation engine with LLM       |
| 5     | API Development               | 2–3 days    | FastAPI endpoints serving recommendations    |
| 6     | Frontend / UI                 | 3–4 days    | User-facing interface (Streamlit or Web)     |
| 7     | Testing & QA                  | 2–3 days    | Unit tests, integration tests, edge cases    |
| 8     | Deployment & Documentation    | 1–2 days    | Production-ready deployment + docs           |

**Total Estimated Duration**: 16–24 days

---

## Phase 1: Project Setup & Environment

> **Goal**: Establish the project foundation — repository structure, virtual environment, dependencies, and configuration management.

### Tasks

| #   | Task                                          | File(s)                          | Status |
| --- | --------------------------------------------- | -------------------------------- | ------ |
| 1.1 | Initialize project directory structure        | All folders under `src/`         | ☐      |
| 1.2 | Create Python virtual environment             | `venv/`                          | ☐      |
| 1.3 | Define `requirements.txt` with dependencies   | `requirements.txt`               | ☐      |
| 1.4 | Create `.gitignore` (venv, .env, __pycache__) | `.gitignore`                     | ☐      |
| 1.5 | Create `.env.example` with required API keys  | `.env.example`                   | ☐      |
| 1.6 | Set up `config/settings.py` for env management| `config/settings.py`             | ☐      |
| 1.7 | Create `README.md` with project overview      | `README.md`                      | ☐      |

### Dependencies to Install

```txt
fastapi==0.104.1
uvicorn==0.24.0
pandas==2.1.4
numpy==1.26.2
datasets==2.15.0           # HuggingFace datasets
openai==1.6.0              # or google-generativeai
langchain==0.0.350          # optional
python-dotenv==1.0.0
pydantic==2.5.3
streamlit==1.29.0           # if using Streamlit UI
requests==2.31.0
pytest==7.4.3
```

### Directory Structure to Create

```
My-project/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── schemas.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   ├── preprocessor.py
│   │   └── store.py
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── filter.py
│   │   ├── prompt_builder.py
│   │   └── recommender.py
│   └── ui/
│       ├── __init__.py
│       └── app.py
├── config/
│   └── settings.py
├── tests/
│   ├── test_loader.py
│   ├── test_filter.py
│   └── test_recommender.py
├── data/
│   └── (generated CSV will go here)
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

### Acceptance Criteria

- [ ] All directories and placeholder files exist
- [ ] Virtual environment activates without errors
- [ ] All dependencies install successfully via `pip install -r requirements.txt`
- [ ] `.env` is gitignored; `.env.example` is committed

---

## Phase 2: Data Ingestion & Preprocessing

> **Goal**: Load the Zomato dataset from Hugging Face, clean it, and store it locally for fast querying.

### Tasks

| #   | Task                                              | File(s)                       | Status |
| --- | ------------------------------------------------- | ----------------------------- | ------ |
| 2.1 | Implement HuggingFace dataset loader              | `src/data/loader.py`          | ☐      |
| 2.2 | Explore dataset — identify columns, types, nulls  | Jupyter notebook / script     | ☐      |
| 2.3 | Implement data preprocessor                       | `src/data/preprocessor.py`    | ☐      |
| 2.4 | Build data store (save/load cleaned CSV)          | `src/data/store.py`           | ☐      |
| 2.5 | Create data pipeline script (load → clean → save) | `src/data/loader.py`          | ☐      |
| 2.6 | Write unit tests for data loading & cleaning      | `tests/test_loader.py`        | ☐      |

### Preprocessing Steps

```
Raw Dataset
    │
    ├── 1. Drop rows with null restaurant_name or rating
    ├── 2. Remove duplicate entries
    ├── 3. Normalize cuisine labels (lowercase, strip whitespace)
    ├── 4. Map cost_for_two to budget categories (low/medium/high)
    ├── 5. Standardize location names
    ├── 6. Convert ratings to float
    └── 7. Extract & flatten highlights field
    │
    ▼
Cleaned Dataset → data/zomato_cleaned.csv
```

### Key Fields to Extract

| Field              | Type    | Example                      |
| ------------------ | ------- | ---------------------------- |
| `restaurant_name`  | String  | `"Olive Bar & Kitchen"`      |
| `location`         | String  | `"Delhi"`                    |
| `cuisine`          | String  | `"Italian, Mediterranean"`   |
| `cost_for_two`     | Integer | `1200`                       |
| `rating`           | Float   | `4.6`                        |
| `votes`            | Integer | `3245`                       |
| `highlights`       | String  | `"Outdoor Seating, WiFi"`    |

### Acceptance Criteria

- [ ] Dataset loads from Hugging Face without errors
- [ ] Cleaned CSV is generated at `data/zomato_cleaned.csv`
- [ ] No null values in critical fields (name, location, cuisine, rating)
- [ ] Budget categories correctly mapped
- [ ] Unit tests pass for loader and preprocessor

---

## Phase 3: Filtering & Query Engine

> **Goal**: Build the filtering logic that matches restaurants to user preferences.

### Tasks

| #   | Task                                              | File(s)                     | Status |
| --- | ------------------------------------------------- | --------------------------- | ------ |
| 3.1 | Define `UserPreferences` Pydantic model           | `src/api/schemas.py`        | ☐      |
| 3.2 | Implement location filter                         | `src/engine/filter.py`      | ☐      |
| 3.3 | Implement budget filter (map to cost ranges)      | `src/engine/filter.py`      | ☐      |
| 3.4 | Implement cuisine filter                          | `src/engine/filter.py`      | ☐      |
| 3.5 | Implement rating filter                           | `src/engine/filter.py`      | ☐      |
| 3.6 | Combine filters into pipeline with fallback logic | `src/engine/filter.py`      | ☐      |
| 3.7 | Write unit tests for each filter                  | `tests/test_filter.py`      | ☐      |

### Filter Logic

```python
# Pseudocode
def filter_restaurants(df, preferences):
    results = df.copy()

    if preferences.location:
        results = results[results['location'] == preferences.location]

    if preferences.budget:
        low, high = BUDGET_MAP[preferences.budget]
        results = results[results['cost_for_two'].between(low, high)]

    if preferences.cuisine:
        results = results[results['cuisine'].str.contains(preferences.cuisine, case=False)]

    if preferences.min_rating:
        results = results[results['rating'] >= preferences.min_rating]

    # Fallback: if too few results, relax filters progressively
    if len(results) < 3:
        results = relax_filters(df, preferences)

    return results.head(TOP_N)  # Return top N candidates for LLM
```

### Budget Mapping

| Budget   | Cost Range (₹)  |
| -------- | ---------------- |
| `low`    | ₹0 – ₹500       |
| `medium` | ₹500 – ₹1,500   |
| `high`   | ₹1,500+          |

### Acceptance Criteria

- [ ] Each filter works correctly in isolation
- [ ] Combined pipeline returns relevant results
- [ ] Fallback logic activates when results < 3
- [ ] Pydantic model validates all input fields
- [ ] Unit tests pass for all filter scenarios

---

## Phase 4: LLM Integration & Prompt Engineering

> **Goal**: Connect to an LLM API and build the prompt pipeline that generates ranked, explained recommendations.

### Tasks

| #   | Task                                                 | File(s)                          | Status |
| --- | ---------------------------------------------------- | -------------------------------- | ------ |
| 4.1 | Set up LLM client (OpenAI / Gemini)                 | `src/engine/recommender.py`      | ☐      |
| 4.2 | Design system prompt (restaurant expert persona)     | `src/engine/prompt_builder.py`   | ☐      |
| 4.3 | Build dynamic prompt with user context + restaurant data | `src/engine/prompt_builder.py` | ☐      |
| 4.4 | Implement response parser (extract JSON from LLM)    | `src/engine/recommender.py`      | ☐      |
| 4.5 | Add error handling (timeouts, malformed responses)   | `src/engine/recommender.py`      | ☐      |
| 4.6 | Implement caching for identical queries              | `src/engine/recommender.py`      | ☐      |
| 4.7 | Write unit tests with mocked LLM responses           | `tests/test_recommender.py`      | ☐      |

### Prompt Template Design

```
┌─────────────────────────────────────────────────────────────────┐
│  SYSTEM PROMPT                                                   │
│  "You are an expert restaurant recommendation assistant.         │
│   Given a list of restaurants and user preferences, rank the     │
│   top 5 restaurants and explain why each is a great fit."        │
├─────────────────────────────────────────────────────────────────┤
│  USER CONTEXT                                                    │
│  "I'm looking for {cuisine} restaurants in {location} with a     │
│   {budget} budget. Minimum rating: {min_rating}.                 │
│   Additional: {preferences}"                                     │
├─────────────────────────────────────────────────────────────────┤
│  RESTAURANT DATA                                                 │
│  "Here are the matching restaurants:                             │
│   1. Name: ..., Cuisine: ..., Rating: ..., Cost: ..., ..."      │
├─────────────────────────────────────────────────────────────────┤
│  INSTRUCTIONS                                                    │
│  "Return a JSON array with fields: rank, restaurant_name,        │
│   cuisine, rating, cost_for_two, explanation.                    │
│   Rank by overall fit. Explain each recommendation."             │
└─────────────────────────────────────────────────────────────────┘
```

### Expected LLM Response Format

```json
{
  "recommendations": [
    {
      "rank": 1,
      "restaurant_name": "Olive Bar & Kitchen",
      "cuisine": "Italian, Mediterranean",
      "rating": 4.6,
      "cost_for_two": 1200,
      "explanation": "Perfect match for your Italian cuisine preference..."
    }
  ],
  "summary": "Based on your preferences, here are the top picks..."
}
```

### Acceptance Criteria

- [ ] LLM client connects and returns responses successfully
- [ ] Prompt produces consistently structured JSON output
- [ ] Response parser handles valid and malformed responses
- [ ] Caching prevents redundant API calls for identical queries
- [ ] Graceful fallback when LLM is unavailable
- [ ] Unit tests pass with mocked LLM responses

---

## Phase 5: API Development

> **Goal**: Expose the recommendation system through a RESTful API using FastAPI.

### Tasks

| #   | Task                                              | File(s)                     | Status |
| --- | ------------------------------------------------- | --------------------------- | ------ |
| 5.1 | Set up FastAPI application                        | `src/main.py`               | ☐      |
| 5.2 | Define request/response Pydantic schemas          | `src/api/schemas.py`        | ☐      |
| 5.3 | Implement `GET /api/health` endpoint              | `src/api/routes.py`         | ☐      |
| 5.4 | Implement `GET /api/cuisines` endpoint            | `src/api/routes.py`         | ☐      |
| 5.5 | Implement `GET /api/locations` endpoint           | `src/api/routes.py`         | ☐      |
| 5.6 | Implement `POST /api/recommend` endpoint          | `src/api/routes.py`         | ☐      |
| 5.7 | Add CORS middleware                               | `src/main.py`               | ☐      |
| 5.8 | Add request validation & error responses          | `src/api/routes.py`         | ☐      |
| 5.9 | Test all endpoints with Swagger UI                | Manual testing              | ☐      |

### API Endpoints

| Method | Endpoint          | Description                     | Request Body                | Response                  |
| ------ | ----------------- | ------------------------------- | --------------------------- | ------------------------- |
| `GET`  | `/api/health`     | Health check                    | —                           | `{ "status": "healthy" }` |
| `GET`  | `/api/cuisines`   | List all available cuisines     | —                           | `{ "cuisines": [...] }`   |
| `GET`  | `/api/locations`  | List all available locations    | —                           | `{ "locations": [...] }`  |
| `POST` | `/api/recommend`  | Get AI recommendations          | `UserPreferences` (JSON)    | `RecommendationResponse`  |

### Request/Response Schemas

```python
# Request
class UserPreferences(BaseModel):
    location: str
    budget: Literal["low", "medium", "high"]
    cuisine: str
    min_rating: float = Field(ge=1.0, le=5.0, default=3.0)
    preferences: Optional[str] = None

# Response
class RecommendationItem(BaseModel):
    rank: int
    restaurant_name: str
    cuisine: str
    rating: float
    cost_for_two: int
    explanation: str

class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationItem]
    summary: str
```

### Acceptance Criteria

- [ ] All 4 endpoints return correct responses
- [ ] Swagger docs accessible at `/docs`
- [ ] Input validation rejects invalid requests with clear errors
- [ ] CORS allows frontend connections
- [ ] `/api/recommend` returns LLM-generated results end-to-end

---

## Phase 6: Frontend / UI

> **Goal**: Build a user-friendly interface for collecting preferences and displaying recommendations.

### Tasks

| #   | Task                                                | File(s)               | Status |
| --- | --------------------------------------------------- | --------------------- | ------ |
| 6.1 | Set up Streamlit app (or HTML/JS frontend)          | `src/ui/app.py`       | ☐      |
| 6.2 | Build user input form (location, budget, cuisine, etc.) | `src/ui/app.py`   | ☐      |
| 6.3 | Add dropdown options populated from API             | `src/ui/app.py`       | ☐      |
| 6.4 | Display recommendation cards with all fields        | `src/ui/app.py`       | ☐      |
| 6.5 | Add loading spinner during LLM processing           | `src/ui/app.py`       | ☐      |
| 6.6 | Style the UI (colors, layout, typography)           | `src/ui/app.py`       | ☐      |
| 6.7 | Add error state handling in UI                      | `src/ui/app.py`       | ☐      |

### UI Layout

```
┌─────────────────────────────────────────────────────────┐
│  🍽️  Zomato AI Restaurant Recommender                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  📍 Location:   [ Delhi         ▼ ]                     │
│  💰 Budget:     [ Medium        ▼ ]                     │
│  🍕 Cuisine:    [ Italian       ▼ ]                     │
│  ⭐ Min Rating: [ ====●======== ] 4.0                   │
│  📝 Other:      [ family-friendly, outdoor      ]       │
│                                                         │
│           [ 🔍 Get Recommendations ]                    │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  📊 AI Summary:                                         │
│  "Based on your preferences, here are the top picks..." │
│                                                         │
│  ┌───────────────────────────────────────────┐          │
│  │ 🥇 #1 — Olive Bar & Kitchen              │          │
│  │    Cuisine: Italian, Mediterranean        │          │
│  │    Rating: ⭐ 4.6  |  Cost: ₹1,200       │          │
│  │    💡 "Perfect for a family outing..."    │          │
│  └───────────────────────────────────────────┘          │
│                                                         │
│  ┌───────────────────────────────────────────┐          │
│  │ 🥈 #2 — Tonino                           │          │
│  │    Cuisine: Italian                       │          │
│  │    Rating: ⭐ 4.4  |  Cost: ₹1,100       │          │
│  │    💡 "Great value with authentic..."     │          │
│  └───────────────────────────────────────────┘          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Acceptance Criteria

- [ ] User can select all preference fields
- [ ] Dropdowns populate dynamically from API
- [ ] Recommendations display in card format with all fields
- [ ] Loading state shown during API call
- [ ] Error messages display gracefully
- [ ] UI is visually polished and responsive

---

## Phase 7: Testing & Quality Assurance

> **Goal**: Ensure system reliability through comprehensive testing.

### Tasks

| #   | Task                                              | File(s)                       | Status |
| --- | ------------------------------------------------- | ----------------------------- | ------ |
| 7.1 | Unit tests — data loader & preprocessor           | `tests/test_loader.py`        | ☐      |
| 7.2 | Unit tests — all filter functions                 | `tests/test_filter.py`        | ☐      |
| 7.3 | Unit tests — prompt builder & response parser     | `tests/test_recommender.py`   | ☐      |
| 7.4 | Integration test — full pipeline (input → output) | `tests/test_integration.py`   | ☐      |
| 7.5 | API endpoint tests (FastAPI TestClient)           | `tests/test_api.py`           | ☐      |
| 7.6 | Edge case testing (no results, bad input, etc.)   | All test files                | ☐      |
| 7.7 | Performance test — measure response times         | Manual / script               | ☐      |

### Test Scenarios

| Category        | Scenario                                    | Expected Outcome                     |
| --------------- | ------------------------------------------- | ------------------------------------ |
| **Happy Path**  | Valid preferences → recommendations         | 3–5 ranked restaurants returned      |
| **No Results**  | Very niche filters → empty dataset          | Relaxed filters or friendly message  |
| **Bad Input**   | Invalid rating (6.0) or missing location    | 422 validation error with details    |
| **LLM Failure** | API timeout or error response               | Fallback results or error message    |
| **Empty Query** | No preferences provided                     | Default/popular recommendations      |

### Acceptance Criteria

- [ ] All unit tests pass (`pytest tests/`)
- [ ] Integration test covers full recommendation flow
- [ ] Edge cases handled without crashes
- [ ] Response time < 5 seconds for standard queries
- [ ] Test coverage > 80%

---

## Phase 8: Deployment & Documentation

> **Goal**: Prepare the application for production deployment and finalize documentation.

### Tasks

| #   | Task                                              | File(s) / Tool              | Status |
| --- | ------------------------------------------------- | --------------------------- | ------ |
| 8.1 | Create `Dockerfile` for containerization          | `Dockerfile`                | ☐      |
| 8.2 | Create `docker-compose.yml` (app + optional Redis)| `docker-compose.yml`        | ☐      |
| 8.3 | Finalize `README.md` with setup instructions      | `README.md`                 | ☐      |
| 8.4 | Document API endpoints (auto-generated Swagger)   | FastAPI `/docs`             | ☐      |
| 8.5 | Add environment variable documentation            | `.env.example`, `README.md` | ☐      |
| 8.6 | Deploy to cloud (Render / Railway / AWS)          | Cloud platform              | ☐      |
| 8.7 | Final review & code cleanup                       | All files                   | ☐      |

### Deployment Options

| Platform   | Pros                          | Best For               |
| ---------- | ----------------------------- | ---------------------- |
| **Render** | Free tier, easy setup         | Quick demos            |
| **Railway**| Git-based deploy, fast        | Small-medium projects  |
| **AWS EC2**| Full control, scalable        | Production workloads   |
| **Docker** | Portable, reproducible        | Any environment        |

### Acceptance Criteria

- [ ] App runs successfully in Docker container
- [ ] README has clear setup, run, and usage instructions
- [ ] All environment variables documented
- [ ] App deployed and accessible via public URL
- [ ] Final code review completed — no dead code, no hardcoded secrets

---

## Phase Dependencies

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (Data)
    │
    ▼
Phase 3 (Filters) ────────────┐
    │                          │
    ▼                          ▼
Phase 4 (LLM) ──────▶ Phase 5 (API)
                          │
                          ▼
                     Phase 6 (UI)
                          │
                          ▼
                     Phase 7 (Testing)
                          │
                          ▼
                     Phase 8 (Deploy)
```

---

## Risk Mitigation

| Risk                               | Impact | Mitigation                                               |
| ---------------------------------- | ------ | -------------------------------------------------------- |
| LLM API costs exceed budget        | High   | Cache responses, limit API calls, use smaller models     |
| Dataset schema changes on HF       | Medium | Pin dataset version, validate schema on load             |
| LLM returns inconsistent format    | Medium | Strict JSON parsing with retry + structured output mode  |
| Slow response times                | Medium | Pre-filter aggressively, cache frequent queries          |
| API key exposure                   | High   | `.env` + `.gitignore`, never commit secrets              |
