# Veridical RAG: AI Quality Engineering & Observability Console

Veridical RAG is an enterprise-grade AI Quality Engineering platform designed for testing, monitoring, and auditing an HR policy retrieval-augmented generation (RAG) assistant. It features a Django REST Framework backend and a Nuxt 3 TypeScript dashboard showing RAGAS metrics, token graphs, query latencies, and trace histories.

---

## Repository Structure

```
├── backend/                  # Django REST Framework API
│   ├── api/                  # Django application logic (models, views, services)
│   ├── config/               # Settings & Django configuration
│   └── run_weekly_eval.sh    # Weekly automated evaluation cron script
│
├── frontend/                 # Nuxt 3 TypeScript Dashboard
│   ├── components/           # Custom SVG Charts and Trace Timelines
│   ├── pages/                # Overview, Evaluations, Regression compare, Ask Console
│   └── layouts/              # Brand theme and side navigation shell
│
├── HR docs/                  # Private company PDF policy files
├── question.json             # 30-question evaluation dataset
└── QUALITY_PATTERNS.md       # AI Quality Engineering patterns write-up
```

---

## Features

1. **RAGAS Evaluation Pipeline**: Scoring runs on *Context Precision*, *Faithfulness*, and *Answer Relevance* locally using Ollama.
2. **Dual Observability**: Integrated tracing using both **LangSmith** (developer runs and playgrounds) and **Langfuse** (production metrics, token tracking, and costing).
3. **Interactive Visual Dashboard**: Responsive Nuxt 3 frontend using custom-built SVG charts for historical RAGAS quality trends and query resource consumption.
4. **Regression Analytics**: Side-by-side comparison page comparing two evaluation runs to detect performance drops (>10%) on a per-question basis.
5. **Scheduled Automation**: A robust shell script wrapper configured for scheduling automated weekly evaluation evaluations via `cron`.

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- [Ollama](https://ollama.com/) running locally with models installed:
  ```bash
  ollama pull qwen2.5:3b
  ollama pull nomic-embed-text
  ```

---

### 1. Backend Setup (Django)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run migrations to initialize the database:
   ```bash
   python manage.py migrate
   ```
5. Run the bootstrap commands to load data:
   ```bash
   # Ingest HR PDFs from workspace
   python manage.py ingest_hr_docs
   
   # Embed all ingested chunks
   python manage.py embed_chunks
   
   # Load evaluation questions from question.json
   python manage.py load_questions
   ```
6. Start the Django development server on port `8000`:
   ```bash
   python manage.py runserver 127.0.0.1:8000
   ```

---

### 2. Frontend Setup (Nuxt 3)

1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install node dependencies:
   ```bash
   npm install
   ```
3. Run the Nuxt dev server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to `http://localhost:3000`.

---

## Running Evaluations

To trigger a RAG pipeline evaluation and score it using local RAGAS, run the custom management command:

```bash
# Evaluate all questions
python manage.py run_eval --name "Prompt V1 Test" --score-with-ragas

# Run a quick evaluation limited to 2 questions
python manage.py run_eval --name "Quick Test" --limit 2 --score-with-ragas
```

---

## Configuring Observability

Add credentials to `backend/.env` to enable online tracing:

- **LangSmith**: Set `LANGCHAIN_TRACING_V2=True` and fill in `LANGCHAIN_API_KEY`.
- **Langfuse**: Fill in `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY`.

*(The application defaults to safe offline/disabled logging fallbacks if variables are omitted)*.

---

## Automation (Weekly Jobs)

Configure a weekly cron job to run the automation script:
1. Edit crontab: `crontab -e`
2. Add weekly midnight execution:
   ```bash
   0 0 * * 0 /absolute/path/to/Veridical_RAG/backend/run_weekly_eval.sh
   ```
Logs will automatically rotate inside `backend/logs/evaluations/`.

For detailed architecture explanations and playbooks, refer to [QUALITY_PATTERNS.md](file:///Users/ztlab85/Desktop/KRI_KPI_Projects/QUALITY_PATTERNS.md).
