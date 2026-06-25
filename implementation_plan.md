# KRI - KPI Production AI Evaluation Project Plan

## Project Goal
Build an HR policy assistant with:
- a Django backend
- a Nuxt 3 + TypeScript dashboard
- a weekly RAGAS evaluation pipeline
- LangSmith and Langfuse observability
- a local/free LLM path for generation

## Phase 1: Project Foundation
- Create a monorepo with `backend/` and `frontend/`.
- Set up Django, Django REST Framework, Postgres, and environment config.
- Set up Nuxt 3 + TypeScript dashboard shell.
- Add Docker Compose for local development.
- Define the core database models early.

## Phase 2: HR Document Ingestion
- Read all PDFs from the `HR docs/` folder.
- Extract text from each policy document.
- Chunk the text into policy sections.
- Store chunks with metadata: document name, section, page number, policy type.
- Save an inventory of documents in the database.

## Phase 3: Baseline RAG Pipeline
- Build the retrieval pipeline using embeddings.
- Use a vector store for semantic search.
- Implement the question-answer flow:
  - user question
  - retrieve relevant chunks
  - send question + context to the LLM
  - return answer with source citations
- Add strict prompts so the model answers only from policy content.

## Phase 4: Evaluation Pipeline
- Load the `question.json` test set.
- Run the RAG pipeline against each test question.
- Store model answer, retrieved chunks, and metadata.
- Run RAGAS scoring on:
  - context precision
  - faithfulness
  - answer relevance
- Save weekly evaluation runs to the database.

## Phase 5: Observability Integration
- Add LangSmith traces for every query and evaluation run.
- Add Langfuse tracking for tokens, latency, and cost.
- Store external trace IDs in the database.
- Build links from the dashboard to trace tools.

## Phase 6: Nuxt Dashboard
- Build an overview page with latest score summary.
- Build trend charts for weekly RAGAS scores.
- Build trace inspection views.
- Build token and latency graphs.
- Build a regression page to compare weekly runs.
- Add a simple alert view for score drops.

## Recommended Build Order
1. Set up Django backend and Nuxt frontend.
2. Ingest the HR docs and store chunks.
3. Build a basic RAG question-answer API.
4. Run the first evaluation on the 30-question set.
5. Add LangSmith and Langfuse.
6. Build the dashboard charts.
7. Polish UI and prepare the demo video.

## MVP Definition
The first usable version should include:
- HR policy documents ingested
- one working Q&A endpoint
- 30-question evaluation set
- one evaluation run saved
- basic dashboard showing scores and traces

## Success Criteria
- The assistant answers only from HR policy docs.
- Weekly eval scores are saved and visible.
- Traces can be inspected for each response.
- Token usage is visible.
- The dashboard clearly shows quality trends.

