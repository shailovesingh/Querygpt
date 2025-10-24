import duckdb
import json
from agents.state import AgentState
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_FILE = "uber_trips.db"
KNOWLEDGE_BASE_FILE = "knowledge_base.json"

# --- LLM Setup for Tools ---
# Use a fast, small model for internal tool/routing decisions
llm_tools = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, api_key=os.getenv("GROQ_API_KEY"))

# --- Database Tool ---
def get_db_connector():
    """Initializes the DuckDB connector."""
    return duckdb.connect(database=DATABASE_FILE)

def execute_sql_query(state: AgentState) -> dict:
    """Executes the generated SQL query and updates the state."""
    query = state["sql_query"]
    print(f"\n--- Executing SQL: {query} ---")
    
    try:
        con = get_db_connector()
        # Use fetchall for non-SELECT (like PRAGMA) and fetchdf for SELECT
        if query.strip().upper().startswith("SELECT"):
            result_df = con.execute(query).fetchdf()
            db_result = result_df.to_markdown(index=False)
        else:
            con.execute(query)
            db_result = "Query executed successfully (non-SELECT)."
        con.close()
        
    except Exception as e:
        db_result = f"SQL ERROR: {str(e)}"
        
    print(f"--- DB Result: {db_result[:100]}... ---")
    return {"db_result": db_result}

# --- RAG/Knowledge Base Tool ---
def retrieve_knowledge_base(state: AgentState) -> dict:
    """Retrieves relevant schema and rules (RAG) based on the workspace."""
    
    workspace_name = state.get("workspace_name")
    
    if not workspace_name:
        return {"context_schema": "Error: No workspace identified."}

    with open(KNOWLEDGE_BASE_FILE, 'r') as f:
        kb = json.load(f)

    # Simple lookup based on workspace and all its tables/rules
    if workspace_name in kb:
        context = f"WORKSPACE: {workspace_name}\n"
        
        # Combine all table schemas and rules for the initial context
        for table, details in kb[workspace_name]['tables'].items():
            context += f"\nTABLE: {table}\n"
            context += f"SCHEMA: {details['schema']}\n"
            context += f"RULES: {details['rules']}\n"
        
        # This context is sent to the LLM for the Table/Column Prune steps
        return {"context_schema": context}

    return {"context_schema": "Error: Workspace not found in knowledge base."}