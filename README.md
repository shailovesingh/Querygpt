## QueryGPT: Multi-Agent Text-to-SQL Engine

**QueryGPT** is an open-source, high-performance **Text-to-SQL agent** built with **LangGraph** and **Groq**, inspired by Uber’s internal data query tool.  
This prototype demonstrates **advanced LLM orchestration**, **Retrieval-Augmented Generation (RAG)** for schema-aware context, and **enterprise-grade data access** — all with extreme performance.

---

## ✨ Key Features & Business Value

| **Feature** | **Engineering Principle** | **Business Value Demonstrated** |
|--------------|---------------------------|----------------------------------|
| **Multi-Agent Orchestration** | Implemented using **LangGraph** to manage a stateful, multi-step workflow. | Demonstrates expertise in building resilient, complex, and debuggable AI systems (the “Uber-Style” architecture). |
| **Extreme Performance** | Powered by **Groq’s Llama 3 API** for sub-second, multi-step inference. | Solves the primary LLM latency issue — achieving up to **70% faster query generation**. |
| **Contextual RAG & Pruning** | Uses **RAG** for domain routing and schema pruning. | Reduces context size, saves token cost, and improves accuracy by removing irrelevant schema data. |
| **Database Interaction** | Connects to **DuckDB** for fast, scalable SQL execution. | Enables complete end-to-end query validation and result synthesis. |
| **Interactive UI** | Built with **Streamlit** for real-time reasoning visualization. | Offers transparency and debuggability — users can see how each agent contributes to the final answer. |

---

## ⚙️ Architecture Overview: The 7-Step LangGraph Workflow

QueryGPT is built as a **directed graph** of specialized AI Agents, each performing a focused task in a robust, explainable pipeline.

| **Step** | **Agent / Tool** | **QueryGPT Equivalent** | **Function** |
|-----------|------------------|--------------------------|---------------|
| 1 | `router` | Intent Agent | Classifies the user’s question to a specific domain (e.g., *Mobility* or *Core Services*). |
| 2 | `rag_retrieval` | Metadata Gateway | Retrieves schema and business context from the Knowledge Base (RAG). |
| 3 | `table_pruner` | Table Agent | Selects only the necessary tables for the query. |
| 4 | `column_pruner` | Column Prune Agent | Filters columns to create a minimal, accurate schema context. |
| 5 | `query_gen` | Query Generation Agent | Uses **Groq Llama 3 70B** to generate the final SQL query. |
| 6 | `query_exec` | SQL Execution Gateway | Executes the SQL on **DuckDB**. |
| 7 | `final_synth` | Query Explanation Agent | Synthesizes the database results into a natural-language answer. |

---

## 🛠️ Setup & Installation

### **Prerequisites**
- Python **3.10+**
- A **Groq API Key**

---

### **1. Clone the Repository**
"""bash
git clone [YOUR_GITHUB_REPO_LINK]
cd uber-query-agent"""


## 2. Create a Virtual Environment & Install Dependencies
python -m venv venv

# On Windows:
.\venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt

## 3. Configure API Keys
Create a .env file in the root directory and add your Groq API Key:

GROQ_API_KEY="your_groq_api_key_here"

## 4. Initialize Database and Knowledge Base

Run the setup script to generate:

uber_trips.db (DuckDB with sample data)

knowledge_base.json (RAG context)

python create_db.py

## 5. Launch the Streamlit Application
streamlit run app.py

## 📂 Project Structure
query-GPT/
├── .env                  # Environment variables (API Key)
├── requirements.txt      # Project dependencies
├── create_db.py          # Creates DuckDB database & RAG context
├── agents/
│   ├── state.py          # Shared memory definition (AgentState) for LangGraph
│   ├── tools.py          # SQL executor, RAG retriever, Groq LLM config
│   └── workflow.py       # Core LangGraph workflow (7-step multi-agent flow)
└── app.py                # Streamlit front-end for visualization


## 🧠 Tech Stack

LangGraph — Multi-agent orchestration

Groq Llama 3 70B — High-speed text-to-SQL inference

DuckDB — Embedded, high-performance SQL engine

Streamlit — Interactive UI for agent introspection

Python 3.10+ — Core runtime

## 🧩 Future Enhancements

 Add natural language follow-up queries (session memory)

 Integrate with live data warehouses (e.g., BigQuery, Snowflake)

 Schema auto-sync with enterprise databases

 Support for multi-domain schema fusion

 Fine-tuning RAG for domain-specific accuracy

## 👨‍💻 Maintainer

Developed by Shailove Singh
Built for experimentation, learning, and performance benchmarking of LLM-based data systems.