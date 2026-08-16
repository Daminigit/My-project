# AI-Powered Restaurant Recommendation System 🍽️

> An intelligent restaurant recommendation service inspired by Zomato, powered by Large Language Models.

---

## Overview

This system ingests real-world restaurant data from the [Zomato Hugging Face dataset](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation), filters it based on user preferences (location, budget, cuisine, rating), and uses an LLM to generate personalized, human-like restaurant recommendations with explanations.

## Features

- 🔍 **Smart Filtering** — Filter restaurants by location, budget, cuisine, and rating
- 🤖 **AI-Powered Recommendations** — LLM ranks and explains why each restaurant fits
- ⚡ **Fast API** — RESTful endpoints built with FastAPI
- 🎨 **User-Friendly UI** — Interactive interface via Streamlit
- 💾 **Caching** — Avoid redundant LLM calls for identical queries
- 🛡️ **Input Validation** — Pydantic models with security-first design

## Tech Stack

| Component        | Technology                    |
| ---------------- | ----------------------------- |
| Backend API      | FastAPI + Uvicorn             |
| Data Processing  | Pandas, NumPy                 |
| Dataset          | Hugging Face `datasets`       |
| LLM              | OpenAI GPT / Google Gemini    |
| Frontend         | Streamlit                     |
| Configuration    | python-dotenv + Pydantic      |
| Testing          | pytest                        |

## Project Structure

```
My-project/
├── Documents/              # Project documentation
├── src/
│   ├── main.py             # FastAPI application entry point
│   ├── api/                # API routes and schemas
│   ├── data/               # Data loading and preprocessing
│   ├── engine/             # Filtering, prompts, and recommendation logic
│   └── ui/                 # Streamlit frontend
├── config/
│   └── settings.py         # Configuration management
├── tests/                  # Test suite
├── data/                   # Generated/cached data files
├── .env.example            # Environment variable template
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/Daminigit/My-project.git
cd My-project
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env and add your API keys
```

### 5. Run the API server

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Run the Streamlit UI (optional)

```bash
streamlit run src/ui/app.py
```

## API Endpoints

| Method | Endpoint           | Description                 |
| ------ | ------------------ | --------------------------- |
| GET    | `/api/health`      | Health check                |
| GET    | `/api/cuisines`    | List available cuisines     |
| GET    | `/api/locations`   | List available locations    |
| POST   | `/api/recommend`   | Get AI recommendations      |

## API Usage Example

```bash
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Delhi",
    "budget": "medium",
    "cuisine": "Italian",
    "min_rating": 4.0,
    "preferences": "family-friendly"
  }'
```

## Running Tests

```bash
pytest tests/ -v --cov=src
```

## Documentation

- [Problem Statement](Documents/Problemstatement.md)
- [Architecture](Documents/Architecture.md)
- [Implementation Plan](Documents/Implementation-plan.md)
- [Edge Cases](Documents/Edge-cases.md)
- [Evaluation Plan](Documents/Eval.md)

## License

This project is for educational purposes.
