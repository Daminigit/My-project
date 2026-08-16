# Architecture: AI-Powered Restaurant Recommendation System

> **Project**: Zomato-Inspired Restaurant Recommendation Service  
> **Version**: 1.0  
> **Last Updated**: 2026-08-16

---

## 1. Overview

This document describes the end-to-end architecture for an AI-powered restaurant recommendation system. The system ingests real-world restaurant data from the [Zomato Hugging Face dataset](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation), filters it based on user preferences, and uses a Large Language Model (LLM) to generate personalized, human-like restaurant recommendations.

---

## 2. High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                  │
│                                                                         │
│   ┌─────────────┐     ┌──────────────┐     ┌────────────────────┐      │
│   │  Web UI /    │     │  User Input  │     │  Recommendation    │      │
│   │  Frontend    │────▶│  Form        │────▶│  Results Display   │      │
│   └─────────────┘     └──────────────┘     └────────────────────┘      │
│                                                                         │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │  REST API / HTTP
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         APPLICATION LAYER                               │
│                                                                         │
│   ┌──────────────┐    ┌───────────────┐    ┌────────────────────┐      │
│   │  API Server  │───▶│  Filter &     │───▶│  Prompt Builder    │      │
│   │  (FastAPI)   │    │  Query Engine │    │  (Integration)     │      │
│   └──────────────┘    └───────────────┘    └────────┬───────────┘      │
│                                                      │                  │
│                                            ┌─────────▼──────────┐      │
│                                            │  LLM Recommendation│      │
│                                            │  Engine             │      │
│                                            └─────────┬──────────┘      │
│                                                      │                  │
└──────────────────────────────┬───────────────────────┘──────────────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
┌──────────────────┐ ┌─────────────────┐ ┌──────────────────┐
│   DATA LAYER     │ │   LLM SERVICE   │ │   CACHE LAYER    │
│                  │ │                 │ │                  │
│  Zomato Dataset  │ │  OpenAI / Gemini│ │  Redis / Local   │
│  (HuggingFace)   │ │  API            │ │  Cache           │
│  + Local Store   │ │                 │ │                  │
└──────────────────┘ └─────────────────┘ └──────────────────┘
```

---

## 3. Component Architecture

### 3.1 Data Ingestion Layer

Responsible for loading, cleaning, and storing the restaurant dataset.

| Component              | Responsibility                                                   | Technology           |
| ---------------------- | ---------------------------------------------------------------- | -------------------- |
| **Dataset Loader**     | Fetch Zomato dataset from Hugging Face                           | `datasets` (HF lib)  |
| **Data Preprocessor**  | Clean, normalize, and transform raw data                         | `pandas`             |
| **Data Store**         | Persist processed data for fast querying                         | CSV / SQLite / PostgreSQL |

**Key Fields Extracted:**

```
restaurant_name | location | cuisine | cost_for_two | rating | votes | highlights
```

**Data Pipeline Flow:**

```
HuggingFace API ──▶ Raw Dataset ──▶ Preprocessor ──▶ Cleaned Data ──▶ Data Store
                                        │
                                        ├── Remove nulls/duplicates
                                        ├── Normalize cost ranges
                                        ├── Standardize cuisine labels
                                        └── Map locations to regions
```

---

### 3.2 User Input Layer

Collects and validates user preferences before passing them to the backend.

| Input Field              | Type        | Validation                          | Example              |
| ------------------------ | ----------- | ----------------------------------- | -------------------- |
| **Location**             | String      | Must match available cities         | `"Delhi"`            |
| **Budget**               | Enum        | `low` / `medium` / `high`          | `"medium"`           |
| **Cuisine**              | String      | Must match available cuisines       | `"Italian"`          |
| **Minimum Rating**       | Float       | Range: `1.0 – 5.0`                 | `4.0`                |
| **Additional Preferences** | Free Text | Optional; parsed by LLM            | `"family-friendly"`  |

**Input Schema (JSON):**

```json
{
  "location": "Delhi",
  "budget": "medium",
  "cuisine": "Italian",
  "min_rating": 4.0,
  "preferences": "family-friendly, outdoor seating"
}
```

---

### 3.3 Integration Layer (Filter & Prompt Builder)

Bridges user input with the LLM by filtering data and constructing optimized prompts.

**Filtering Pipeline:**

```
User Input
    │
    ▼
┌──────────────────────┐
│  Location Filter     │──▶ Match city/region
├──────────────────────┤
│  Budget Filter       │──▶ Map to cost_for_two range
├──────────────────────┤
│  Cuisine Filter      │──▶ Match cuisine type
├──────────────────────┤
│  Rating Filter       │──▶ rating >= min_rating
└──────────────────────┘
    │
    ▼
Filtered Restaurant List (Top N candidates)
    │
    ▼
┌──────────────────────┐
│  Prompt Builder      │
│                      │
│  • System prompt     │
│  • User context      │
│  • Restaurant data   │
│  • Ranking criteria  │
└──────────────────────┘
    │
    ▼
Structured LLM Prompt
```

**Budget Mapping:**

| Budget Level | Cost for Two (₹) |
| ------------ | ----------------- |
| Low          | ₹0 – ₹500        |
| Medium       | ₹500 – ₹1500     |
| High         | ₹1500+            |

---

### 3.4 Recommendation Engine (LLM Layer)

The core AI component that ranks restaurants and generates human-like explanations.

**LLM Interaction Flow:**

```
┌────────────────────┐      ┌──────────────────────┐
│  Structured Prompt │─────▶│  LLM API Call        │
│                    │      │  (OpenAI / Gemini)   │
└────────────────────┘      └──────────┬───────────┘
                                       │
                                       ▼
                            ┌──────────────────────┐
                            │  Response Parser     │
                            │                      │
                            │  • Extract rankings  │
                            │  • Parse explanations│
                            │  • Validate output   │
                            └──────────┬───────────┘
                                       │
                                       ▼
                            ┌──────────────────────┐
                            │  Recommendation      │
                            │  Objects             │
                            │                      │
                            │  List[Restaurant +   │
                            │       Explanation]   │
                            └──────────────────────┘
```

**Prompt Design Strategy:**

| Prompt Section     | Purpose                                              |
| ------------------ | ---------------------------------------------------- |
| **System Prompt**  | Define the AI's role as a restaurant expert           |
| **User Context**   | Inject user preferences and constraints               |
| **Restaurant Data**| Provide filtered candidates with structured details   |
| **Instructions**   | Ask for ranked list with explanations per restaurant  |

---

### 3.5 Output / Presentation Layer

Displays the AI-generated recommendations in a clean, user-friendly format.

**Response Schema (JSON):**

```json
{
  "recommendations": [
    {
      "rank": 1,
      "restaurant_name": "Olive Bar & Kitchen",
      "cuisine": "Italian, Mediterranean",
      "rating": 4.6,
      "cost_for_two": 1200,
      "explanation": "Perfect for a family outing with its spacious outdoor seating, diverse Italian menu, and consistently high ratings."
    }
  ],
  "summary": "Based on your preferences for Italian cuisine in Delhi with a medium budget, here are the top picks..."
}
```

---

## 4. Technology Stack

| Layer                | Technology                    | Purpose                          |
| -------------------- | ----------------------------- | -------------------------------- |
| **Frontend**         | Streamlit / HTML + JS         | User interface                   |
| **Backend API**      | FastAPI (Python)              | REST API server                  |
| **Data Processing**  | Pandas, NumPy                 | Data cleaning & filtering        |
| **Dataset Source**    | Hugging Face `datasets`       | Load Zomato dataset              |
| **LLM Integration**  | OpenAI API / Google Gemini    | AI-powered recommendations       |
| **Prompt Framework** | LangChain (optional)          | Prompt templating & chaining     |
| **Data Storage**     | SQLite / CSV                  | Local data persistence           |
| **Caching**          | Redis / `functools.lru_cache` | Cache frequent queries           |
| **Environment**      | Python 3.10+, venv            | Runtime environment              |

---

## 5. Project Directory Structure

```
My-project/
├── Documents/
│   ├── Problemstatement.txt        # Original problem statement
│   ├── Problemstatement.md         # Formatted problem statement
│   └── Architecture.md             # This file
├── src/
│   ├── __init__.py
│   ├── main.py                     # Application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py               # API endpoint definitions
│   │   └── schemas.py              # Pydantic request/response models
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py               # HuggingFace dataset loader
│   │   ├── preprocessor.py         # Data cleaning & transformation
│   │   └── store.py                # Data persistence layer
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── filter.py               # User preference filtering
│   │   ├── prompt_builder.py       # LLM prompt construction
│   │   └── recommender.py          # LLM interaction & response parsing
│   └── ui/
│       ├── __init__.py
│       └── app.py                  # Streamlit / frontend app
├── config/
│   └── settings.py                 # App configuration & env vars
├── tests/
│   ├── test_loader.py
│   ├── test_filter.py
│   └── test_recommender.py
├── data/
│   └── zomato_cleaned.csv          # Preprocessed dataset (generated)
├── .env                            # API keys (gitignored)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 6. API Endpoints

| Method | Endpoint               | Description                          | Request Body         |
| ------ | ---------------------- | ------------------------------------ | -------------------- |
| `GET`  | `/api/health`          | Health check                         | —                    |
| `GET`  | `/api/cuisines`        | List available cuisines              | —                    |
| `GET`  | `/api/locations`       | List available locations             | —                    |
| `POST` | `/api/recommend`       | Get AI-powered recommendations       | `UserPreferences`    |

---

## 7. Data Flow (End-to-End)

```
┌──────┐    ┌──────────┐    ┌──────────┐    ┌─────────┐    ┌──────────┐    ┌──────────┐
│ User │───▶│ Frontend │───▶│ API      │───▶│ Filter  │───▶│ Prompt   │───▶│ LLM API  │
│      │    │          │    │ Server   │    │ Engine  │    │ Builder  │    │          │
└──────┘    └──────────┘    └──────────┘    └─────────┘    └──────────┘    └─────┬────┘
                                                                                │
┌──────┐    ┌──────────┐    ┌──────────┐                                        │
│ User │◀───│ Frontend │◀───│ Response │◀───────────────────────────────────────┘
│      │    │ Display  │    │ Parser   │
└──────┘    └──────────┘    └──────────┘
```

---

## 8. Non-Functional Requirements

| Requirement       | Target                                                        |
| ----------------- | ------------------------------------------------------------- |
| **Response Time** | < 5 seconds for recommendation generation                     |
| **Scalability**   | Support 100+ concurrent users with caching                    |
| **Reliability**   | Graceful fallback if LLM API is unavailable                   |
| **Security**      | API keys stored in `.env`, never committed to version control |
| **Data Freshness**| Dataset refreshed periodically from Hugging Face              |
| **Cost Control**  | Cache LLM responses for identical queries                     |

---

## 9. Error Handling Strategy

| Error Scenario               | Handling Approach                                      |
| ---------------------------- | ------------------------------------------------------ |
| LLM API timeout / failure    | Return cached results or rule-based fallback ranking   |
| No matching restaurants      | Relax filters progressively; inform user               |
| Invalid user input           | Pydantic validation with clear error messages          |
| Dataset loading failure      | Use local cached copy of the dataset                   |
| Rate limiting (LLM API)      | Implement exponential backoff + request queuing        |

---

## 10. Future Enhancements

- **Vector Search**: Embed restaurant descriptions using sentence transformers for semantic similarity search
- **User Profiles**: Store past preferences and recommendation history for personalization
- **Multi-language Support**: Generate recommendations in the user's preferred language
- **Review Summarization**: Use LLM to summarize user reviews per restaurant
- **Real-time Data**: Integrate live Zomato API for up-to-date menus and availability
- **Feedback Loop**: Allow users to rate recommendations to improve future suggestions
