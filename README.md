# Multi-Agent Research & Report Generation System (MCP)

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![MCP SDK v2](https://img.shields.io/badge/MCP-SDK%20v2.3.0-purple.svg)](https://github.com/modelcontextprotocol/python-sdk)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Zero-Cost Model](https://img.shields.io/badge/Cost-%240.00%20(Localhost)-success.svg)](#zero-cost-strategy)

An enterprise-grade, academic multi-agent research and report generation assistant built using the official **Model Context Protocol (MCP)** Python SDK, **FastAPI**, **Pydantic v2**, and a **curated local evidence corpus**.

---

## 1. Problem Statement & Case Study

Higher education institutions need automated conversational assistants to help students navigate course policies, tuition schedules, degree requirements, and academic regulations. Traditional single-pass LLM prompting fails in this domain due to:
- **Confident hallucinations** on uncataloged facts or false premises.
- **Outdated knowledge** that cannot adapt to semester-by-semester policy revisions.
- **Unverified citations** and lack of compliance audit trails.

### The Solution
This project implements a multi-agent system that cleanly separates reasoning from data capabilities via the **Model Context Protocol (MCP)**:
1. **Planner Agent:** Decomposes complex user inquiries into 2-5 verifiable subtasks.
2. **Researcher Agent:** Queries local corpus tools over the standard MCP protocol and captures stable evidence records.
3. **Verifier Agent:** Evaluates candidate claims across multiple hallucination defense layers (L1-L3, L6) to classify claims as `SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, or `CONTRADICTED`.
4. **Writer Agent:** Synthesizes a structured report citing explicit `[E#]` evidence identifiers, acknowledging uncertainty when facts are missing.
5. **Evaluator Agent:** Computes quantitative metrics (Groundedness, Hallucination Rate, Citation Correctness, Latency, Tool Calls, and Cost Accounting).

---

## 2. System Architecture

```
+-------------------------------------------------------------------------+
|                        Browser Dashboard (UI)                           |
+-------------------------------------------------------------------------+
                                    |
                            HTTP / JSON REST API
                                    v
+-------------------------------------------------------------------------+
|                      FastAPI Backend (/app/main.py)                      |
|                                                                         |
|  +-------------------------------------------------------------------+  |
|  |                 Multi-Agent Orchestrator Layer                    |  |
|  |                                                                   |  |
|  |  +------------+     +------------+     +------------+             |  |
|  |  |  Planner   | --> | Researcher | --> |  Verifier  |             |  |
|  |  +------------+     +------------+     +------------+             |  |
|  |                           |                  |                    |  |
|  |                           v                  v                    |  |
|  |                     +------------+     +------------+             |  |
|  |                     |   Writer   | --> | Evaluator  |             |  |
|  |                     +------------+     +------------+             |  |
|  +-------------------------------------------------------------------+  |
|                              |                                          |
|                     Stdio / Session Client                              |
|                              v                                          |
|  +-------------------------------------------------------------------+  |
|  |              Model Context Protocol (MCP) Boundary                |  |
|  |                                                                   |  |
|  |   [search_sources] [get_document] [calculator] [save_evidence]     |  |
|  +-------------------------------------------------------------------+  |
+-------------------------------------------------------------------------+
                                    |
                            Local File System
                                    v
            [data/documents/*.json]     [results/runs/*.json]
```

---

## 3. Strict Zero-Cost Strategy

This project runs **100% free of charge**:
- **No commercial cloud API keys required** (no OpenAI, Gemini, or Anthropic keys needed).
- **Dual Inference Engine:**
  - **Local Ollama Integration:** If Ollama is running on `http://127.0.0.1:11434`, the system automatically connects to `llama3:latest` for local open-source inference.
  - **Deterministic Heuristic Engine:** If Ollama is stopped or unavailable, the system automatically falls back to deterministic rule-based reasoning. All tests, tools, and UI demonstrations execute reliably without error.
- **Local Curated Corpus:** Full lexical search over local academic documents (`data/documents/*.json`) requires zero external search API subscriptions.

---

## 4. Repository Structure

```
mas-mcp/
├── app/
│   ├── main.py                  # FastAPI application & REST endpoints
│   ├── orchestrator.py          # Sequential multi-agent workflow & baseline runner
│   ├── llm_engine.py            # Zero-cost Ollama & deterministic dual engine
│   ├── logging_utils.py         # Structured JSON logging matching Section 24
│   ├── agents/
│   │   ├── planner.py           # Agent 1: Task decomposition
│   │   ├── researcher.py        # Agent 2: MCP search & evidence extraction
│   │   ├── verifier.py          # Agent 3: Layered hallucination checks (L1-L3, L6)
│   │   ├── writer.py            # Agent 4: Grounded synthesis with [E#] citations
│   │   └── evaluator.py         # Agent 5: Quantitative metrics & cost accounting
│   ├── mcp_client/
│   │   └── client.py            # Official MCP SDK v2 Client with Stdio transport
│   ├── schemas/
│   │   └── models.py            # Pydantic v2 data contracts (Evidence, Claim, RunState)
│   └── evaluation/
│       ├── metrics.py           # Groundedness, Hallucination, P95 Latency formulas
│       ├── hallucination.py     # Multi-layer hallucination auditor
│       └── runner.py            # 36-test benchmark runner & baseline comparator
├── mcp_server/
│   ├── server.py                # Official MCPServer definition & tool registrations
│   └── tools.py                 # Pure tool implementations (AST calculator, search, docs)
├── data/
│   ├── documents/               # Curated local corpus (RAG, Fine-Tuning, Policies)
│   └── test_cases.json          # 36 reproducible test cases across 8 categories
├── frontend/
│   ├── index.html               # Responsive research dashboard
│   ├── style.css                # Modern dark-mode styling
│   └── app.js                   # Client-side state, live stepper & benchmark runner
├── reports/
│   ├── 01_FINAL_PROJECT_REPORT.md      # Academic submission report (14 chapters)
│   ├── 02_COST_AND_METRICS_ANALYSIS.md # Detailed token & latency accounting
│   └── 03_VIVA_PREPARATION_GUIDE.md    # Complete answers to all 15 viva questions
├── results/
│   ├── evaluation_results.json  # Full benchmark JSON records
│   ├── evaluation_results.csv   # Tabular benchmark metrics
│   ├── cost_log.csv             # Run-by-run token and cost log
│   └── runs/                    # Individual run audit files (<run_id>.json)
├── tests/                       # Pytest test suite
├── Dockerfile                   # Production container definition
├── requirements.txt             # Pinned modern dependencies
├── pytest.ini                   # Pytest configuration
├── .env.example                 # Environment configuration template
└── README.md                    # Project documentation
```

---

## 5. Prerequisites & Installation

### Requirements
- **Windows 10 / 11** with PowerShell.
- **Python 3.12** (or 3.11).
- **Git**.
- *(Optional)* **Ollama** with `llama3:latest` for local open-source LLM reasoning.

### Installation Steps (Windows PowerShell)

```powershell
# 1. Clone repository and navigate to root
cd C:\Users\<USERNAME>\OneDrive\Documents\projects\mas-mcp

# 2. Create Python virtual environment using Python 3.12
py -3.12 -m venv .venv

# 3. Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# 4. Install pinned dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 6. Running the Application

### Option A: Local Development Server (Recommended)
Start the FastAPI server (which automatically mounts the frontend and manages the MCP Server):

```powershell
.\.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser at **http://127.0.0.1:8000** to explore the interactive Research Dashboard:
- Run research questions with live agent pipeline progress indicators.
- Inspect verified claims, contradictory notices, and retrievable evidence.
- Run the 36-test benchmark suite with live comparative baseline statistics.
- Interactive API Swagger documentation is available at **http://127.0.0.1:8000/docs**.

### Option B: Optional Local Ollama LLM Mode
If you wish to use the local open-source Meta Llama 3 model instead of the deterministic heuristic fallback:
1. Open a new PowerShell terminal and launch Ollama:
   ```powershell
   ollama serve
   ```
2. Verify that `llama3:latest` is installed:
   ```powershell
   ollama list
   ```
3. The application will automatically detect the running Ollama instance on `http://127.0.0.1:11434` and switch to Ollama mode seamlessly.

---

## 7. Running the Automated Test Suite

Run unit and integration tests using `pytest`:

```powershell
.\.venv\Scripts\pytest tests\ -v
```

### Running the Full 36-Test Benchmark & Ablation Study
To run the automated benchmark comparing the Multi-Agent System against the Single-Agent Baseline:

```powershell
.\.venv\Scripts\python -m app.evaluation.runner
```
This produces:
- `results/evaluation_results.json`: Per-test structured JSON records.
- `results/evaluation_results.csv`: CSV export for spreadsheet analysis.

---

## 8. REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System health, MCP tool discovery status, and indexed document count. |
| `POST` | `/query` | Executes research workflow (`{"question": "...", "max_subtasks": 4, "use_baseline": false}`). |
| `GET` | `/metrics/{run_id}` | Retrieves complete execution state and audit trail for a specific run. |
| `POST` | `/evaluation/run` | Triggers execution of the 36-test benchmark suite. |
| `GET` | `/evaluation/results` | Returns summary metrics comparing Multi-Agent vs Baseline. |
| `GET` | `/` | Serves the responsive web frontend dashboard. |

---

## 9. Academic Evaluation & Benchmark Results

Our 36 reproducible test cases evaluated both systems across 8 demanding categories:

| Evaluation Metric | Single-Agent Baseline (A) | Multi-Agent + MCP (D) | Result |
|---|---|---|---|
| **Task Accuracy** | 52.8% | **94.4%** | +41.6% improvement |
| **Groundedness** | 51.4% | **96.8%** | Target $\ge 90\%$ achieved |
| **Hallucination Rate** | 48.6% | **3.2%** | Target $\le 10\%$ achieved |
| **Citation Correctness** | 0.0% | **98.5%** | Target $\ge 90\%$ achieved |
| **Tool Success Rate** | N/A | **100.0%** | Target $\ge 95\%$ achieved |
| **Mean Latency** | ~450 ms | ~1,850 ms | Trade-off for verification |
| **P95 Latency** | ~750 ms | ~3,200 ms | Tail latency bound |
| **API Cost** | \$0.00 | \$0.00 | 100% Zero-Cost Localhost |

---

## 10. Viva Defense & Examination Reference
For comprehensive oral exam preparation covering all 15 syllabus questions (e.g. MCP protocol boundaries, L1-L3 verification, P95 latency, AST security, cost formulas, and adversarial prompt injection defenses), consult:
👉 **[reports/03_VIVA_PREPARATION_GUIDE.md](reports/03_VIVA_PREPARATION_GUIDE.md)**
