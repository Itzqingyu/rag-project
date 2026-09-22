# DASH (Decision, Activity, Schedule, History)

> **Event Management and Knowledge Base Decision Support System**  
> Integrates event preparation dashboards, LLM-based document retrieval-augmented generation (RAG), and structured meeting minutes extraction with database storage.

[English](README.md) | [繁體中文](README.zh-TW.md)

---

## Key Features (User Guide)

DASH consists of three core functional modules to assist teams in managing event workflows, meeting records, and associated documentation.

### Core Architecture

- **1. Event Management Dashboard**: Event overview, preparation progress, meeting logs, action items, key decisions, schedule timeline, and incident logs.
- **2. AI Chat & Knowledge Retrieval (RAG)**: Dual conversation modes (General Chat / Knowledge Retrieval), source citation, context isolation, and centralized multi-format document management.
- **3. AI Structured Meeting Minutes Extraction (Preview & Commit)**: Full-text structured extraction, inline field editing, and database persistence linked with the event dashboard.

---

### 1. Control Dashboard: Activities, Meetings, Decisions, Schedules & Tasks

Provides a management interface for the event lifecycle, organizing information and records across all stages:

- **Event Overview & Progress Tracking (Overview)**:
  - Displays preparation completion status and lifecycle stages (`Created` -> `In Preparation` -> `In Progress` -> `Post-Event Review`).
  - Consolidates key details (dates, venues, coordinators, budget, expected attendance) and next steps.
- **Preparation Meeting Management (Meetings)**:
  - Records time, venue, attendees, and discussion notes across preparation meetings.
  - Supports linking to uploaded source documents (`source_document_id`) to view original files.
- **Key Decision Records (Decisions)**:
  - Captures problem statements, considered options, final decisions, and reasons.
  - Tracks confirmation status (`Pending` / `Confirmed`) and document sources.
- **Action Task List (Tasks)**:
  - Supports status filtering (`All` / `Pending` / `Completed`) with priority markers (`High` / `Medium` / `Low`).
  - Tasks can be assigned to owners, set with deadlines, and linked to corresponding events and meetings.
- **Schedule Timeline & Incident Logs (Schedule & Incidents)**:
  - Detailed agenda schedules (owners, categories, remarks), along with incident tracking and response recommendations during event execution.

---

### 2. LLM + RAG Historical Records & Knowledge Retrieval

Provides document-based search and question-answering capabilities:

- **Document Conversion & Centralized Storage**:
  - Supports `.md`, `.txt`, `.pdf`, and `.docx` file formats.
  - Automatically parses and standardizes documents into Markdown files, decoupled from original local files once uploaded.
- **Vector Retrieval**:
  - Documents are chunked semantically, vectorized through an embedding model, and stored in a Chroma vector database.
- **Dual Chat Modes**:
  - **Knowledge Q&A Mode (`RAG`)**: Retrieves relevant document chunks based on user queries and injects them into the context for LLM responses, with collapsible source citation cards.
  - **General Chat Mode (`Chat`)**: Interacts directly with the LLM using conversational context without querying the document repository.
- **Context Isolation Mechanism (Clean Context Isolation)**:
  - The chat database stores only user questions and model replies, keeping retrieved document chunks in isolated metadata.
  - Multi-turn conversations avoid re-injecting historical document chunks, preventing context length inflation.
- **Confirmation Safeguard**:
  - Prompts a confirmation dialog when deleting chat sessions or removing knowledge base files to prevent accidental deletion.

---

### 3. AI Structured Meeting Minutes Extraction (Preview & Commit)

Provides structured extraction and database persistence workflows for meeting minutes:

- **Document Structured Extraction**:
  - Select uploaded meeting minutes from the document repository.
  - Utilizes a System Prompt to guide the LLM in analyzing the text and extracting meeting summaries, key decisions, and action items.
- **Preview and Confirmation Workflow (Preview-Commit)**:
  1. **Preview Stage**: Extracted results are presented in structured tables for inspection.
  2. **Field Editing**: Users can edit meeting titles, dates, venues, decisions, and task details directly in the interface.
  3. **Commit to Database**: After verification, clicking "Commit to Database" writes data to SQLite and updates the event management dashboard.

---

## Technical Architecture & Developer Guide

### System Layered Architecture

- **Frontend Layer (Desktop Client)**
  - **Core Technologies**: React 19 + TypeScript + Vite + Electron Forge.
  - **Design Conventions**: Component-isolated CSS styles, strict Design Tokens (`:root`) inheritance, strictly zero Emojis.
  - **Service Communication**: Centralized HTTP REST wrapper via `apiClient` with unified error handling.
- **Backend Service Layer (Python / FastAPI)**
  - **Interface**: Local HTTP RESTful API (defaulting to `http://127.0.0.1:8000`).
  - **Entrypoint**: `python/src/rag_project/main.py`.
  - **Core Modules**:
    - `activity_services/`: Implements SQLite CRUD operations for Activity, Meeting, Task, Decision, Schedule, and Incident.
    - `document_processing/`: File format conversion (`converter`) and semantic chunking with vectorization (`rag_engine`).
    - `llm_service`: Connects to LLMs via LiteLLM and loads System Prompts from `prompts/` for structured extraction.
- **Local Storage Layer (`python/data/`)**
  - **SQLite Database (`rag_database.sqlite`)** : Stores document metadata, chat sessions, message logs, and event records.
  - **ChromaDB Vector Store (`chroma_db/`)**: Stores document chunks and feature vectors for semantic search.
  - **Hosted Markdown Store (`markdown/`)**: Central storage for converted standard Markdown texts.

### Technology Stack

| Domain | Technology / Package | Description |
| :--- | :--- | :--- |
| **Frontend App** | React, TypeScript, Electron, Vite | Cross-platform desktop application framework |
| **Icons & Aesthetics** | Lucide React | Unified icon system (strictly zero Emojis) |
| **Markdown Rendering** | react-markdown | Message formatting and list hierarchy rendering |
| **Backend Framework** | Python 3.10+, FastAPI, Uvicorn | Asynchronous RESTful API service |
| **Package Manager** | uv | Python package and dependency manager |
| **RAG & Retrieval** | LangChain, FastEmbed, ChromaDB | Text chunking, vectorization, and semantic search supporting CPU execution |
| **LLM Interface** | LiteLLM | Unified calling interface for large language models |
| **Document Conversion** | PyPDF, python-docx, markdown | Parses common formats and converts them to Markdown text |
| **Database** | SQLite3, ChromaDB Persistent | Local relational and vector database storage |

---

### Local Installation & Deployment

#### 1. Prerequisites
- **Node.js**: v18+ and npm
- **Python**: 3.10+ (recommended: install [uv](https://github.com/astral-sh/uv))
- **LLM API Key (.env)**: API key for the corresponding model service

#### 2. Environment Configuration
Create a `.env` file in the `python/` directory or project root:
```env
# Set the corresponding API key and model name according to LiteLLM specifications
API_KEY=your_api_key_here
MODEL_NAME=your_model_name_here
```

#### 3. Backend Setup & Startup

Use `uv` for dependency synchronization and execution:

```powershell
# Navigate to the backend directory
cd python

# Install dependencies
uv sync

# Launch FastAPI backend server (default: http://127.0.0.1:8000)
uv run python src/rag_project/main.py
```
> After starting, visit `http://127.0.0.1:8000/docs` in your browser to test all APIs via the Swagger UI.

#### 4. Frontend Setup & Startup

Open another terminal window and navigate to the `react/` directory:

```powershell
# Navigate to the frontend directory
cd react

# Install dependencies
npm install

# Run tests to verify code integrity
npm run test

# Start Electron development environment
npm run start
```

---

### Testing Conventions & Project Guidelines

- **Python Backend Tests**:
  - Test scripts must be located in `python/tests/`.
  - `python/tests/test_main.py`: Interactive CLI tool for end-to-end testing of document conversion, event operations, meeting extraction, and multi-turn conversations.
- **React Frontend Tests**:
  - Unit and integration tests are located in `react/tests/`, run with Vitest: `npm run test`.
- **Code & Naming Style**:
  - Files and directories: Lowercase letters with hyphens `-` (except code scripts, which follow language conventions).
  - CSS guidelines: Color schemes strictly inherited from `:root` in `index.css`; one CSS file per component.
  - Iconography: Strictly zero Emojis; all icons use `lucide-react`.

---

## License

This project is licensed under the [MIT License](LICENSE).
