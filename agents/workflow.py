from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from agents.state import AgentState
from agents.tools import execute_sql_query, retrieve_knowledge_base
from dotenv import load_dotenv
import os

load_dotenv()
# Use Groq model for the complex reasoning (Query Generation)
llm_main = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1, api_key=os.getenv("GROQ_API_KEY"))
# Use a faster/smaller simple routing/pruning
llm_pruner = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, api_key=os.getenv("GROQ_API_KEY"))


# Intent Agent (Router)
def route_to_workspace(state: AgentState) -> dict:
    """Classifies the user question to a 'Workspace' (Domain Routing)."""
    question = state["user_question"]
    print(f"\n[Agent: Router] Routing question: {question}")
    
    # Prompt to force structured output for routing
    prompt_str = f"""You are an Intent Agent. Classify the user question into one of the following workspaces:
    - 'Mobility': Questions about trips, drivers, fares, and cities.
    - 'Core Services': Questions about driver licensing, HR, and long-term retention.
    
    Your output MUST be a single word, the name of the workspace. Do not add any other text or punctuation.
    Question: {question}
    Workspace:"""

    response = llm_pruner.invoke(prompt_str).content.strip()
    workspace = response.replace("'", "").replace('"', '').strip()
    
    # Fallback to the default/most common workspace if routing fails
    if workspace not in ["Mobility", "Core Services"]:
        workspace = "Mobility"
        
    print(f"[Agent: Router] Routed to: {workspace}")
    return {"workspace_name": workspace}


# Table/RAG Agent (Pruning Step 1)
def table_prune_agent(state: AgentState) -> dict:
    """Uses LLM to select only the relevant tables from the full schema/context."""
    context_schema = state["context_schema"]
    question = state["user_question"]
    print(f"\n[Agent: Table Pruner] Context Size: {len(context_schema)} chars.")
    
    # Prompt to select tables based on question
    prompt_str = f"""
    You are a Table Selection Agent. Your goal is to identify ALL necessary tables from the provided context to answer the user's question.
    
    CONTEXT (Schema, Rules, Tables):
    {context_schema}
    
    User Question: {question}
    
    Your output MUST be a comma-separated list of table names, and nothing else. Example: 'trips,drivers'.
    Relevant Tables:
    """
    
    response = llm_pruner.invoke(prompt_str).content.strip().lower()
    relevant_tables = [t.strip() for t in response.split(',') if t.strip()]
    
    # This is critical for the next step to work correctly
    # we can manually ensure the tables are valid
    valid_tables = [t for t in relevant_tables if t in ['trips', 'drivers']]
    
    print(f"[Agent: Table Pruner] Selected Tables: {valid_tables}")
    return {"relevant_tables": valid_tables}


# Column Prune Agent (Pruning Step 2: Creates the Final, Minimized Schema)
def column_prune_agent(state: AgentState) -> dict:
    """Filters the schema to only include necessary columns."""
    context_schema = state["context_schema"] # Full knowledge base
    question = state["user_question"]
    relevant_tables = state["relevant_tables"]
    
    # Filter context_schema down to only the relevant tables
    pruned_schema = f"WORKSPACE: {state['workspace_name']}\n"
    for table in relevant_tables:
        if table == 'trips':
            pruned_schema += "\nTABLE: trips\nSCHEMA: trip_id (INT), driver_id (INT), city (VARCHAR), distance_miles (FLOAT), fare_usd (FLOAT), trip_status (VARCHAR), trip_date (DATE)\nRULES: The column `trip_status` must be 'completed' to count a successful trip. Always filter by `trip_date` when a time frame is provided."
        elif table == 'drivers':
            pruned_schema += "\nTABLE: drivers\nSCHEMA: driver_id (INT), name (VARCHAR), license_status (VARCHAR), vehicle_make (VARCHAR), hire_date (DATE), current_rating (FLOAT)\nRULES: To check for an active driver, filter on `license_status` = 'active'."
            # NOTE: We deliberately left out 'annual_bonus_target' and 'long_term_retention_score' 
            # to demonstrate *pruning* of irrelevant or low-value columns!
            
    print(f"[Agent: Column Pruner] Pruned Schema Size: {len(pruned_schema)} chars.")
    return {"pruned_schema": pruned_schema}


# Query Generation Agent
def query_generation_agent(state: AgentState) -> dict:
    """Generates the final SQL query using the minimized context (Groq llama3-70b)."""
    pruned_schema = state["pruned_schema"]
    question = state["user_question"]
    
    print(f"\n[Agent: Query Generator] Generating query...")
    
    SYSTEM_PROMPT = f"""
    You are an expert SQL engineer. Your task is to generate a syntactically correct DuckDB SQL query to answer the user's question, based *only* on the provided database schema and rules.
    
    DATABASE CONTEXT:
    {pruned_schema}
    
    CRITICAL INSTRUCTIONS:
    1. Only use the tables and columns provided in the context.
    2. Adhere strictly to the 'RULES' for each table.
    3. Use the 'completed' status rule for trip counting.
    4. For exploratory queries, limit the result to 5 rows (use LIMIT 5).
    5. Return ONLY the raw SQL query, no explanations, no markdown block (```sql).
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", f"User Question: {question}\nSQL Query:"),
    ])
    
    chain = prompt | llm_main
    
    # Generate the query using the powerful LLM
    sql_query = chain.invoke({"pruned_schema": pruned_schema, "question": question}).content.strip()
    
    # Simple post-processing to ensure clean output
    sql_query = sql_query.split(';')[0].strip() + ';'
    print(f"[Agent: Query Generator] Generated SQL: {sql_query}")
    return {"sql_query": sql_query}


# Final Answer Agent (Synthesis)
def final_answer_agent(state: AgentState) -> dict:
    """Analyzes the DB result and synthesizes the final answer for the user."""
    # Retrieve all necessary keys from the current state
    question = state["user_question"]
    sql_query = state["sql_query"]
    db_result = state["db_result"]
    
    print(f"\n[Agent: Final Answer] Synthesizing final response...")
    
    if db_result.startswith("SQL ERROR"):
        final_answer = f"I encountered an error executing the query. The generated query was:\n\n`{sql_query}`\n\n**Error:** {db_result}"
    else:
        # Prompt to turn the data into a natural language response
        prompt_str = f"""
        You are a friendly data analyst. Convert the SQL query result into a concise, natural language answer for the user.
        
        User Question: {question}
        Generated SQL: {sql_query}
        SQL Result (Markdown Table):
        {db_result}
        
        Final Answer (Summary of the data):
        """
        # Using llm_pruner for faster synthesis
        response = llm_pruner.invoke(prompt_str).content
        final_answer = response.strip()
    
    # This ensures 'sql_query' remains in the state for the final log step.
    return {
        "final_answer": final_answer,
        "sql_query": sql_query, # Pass through the SQL query
        "db_result": db_result  # Pass through the DB result
        # Note: LangGraph automatically merges this output with the existing state based on the TypedDict structure
    }


# Conditional Edges
def check_for_error(state: AgentState) -> str:
    """Checks if the query execution resulted in an error."""
    if state["db_result"].startswith("SQL ERROR"):
        # For a more advanced system, you could route to a "Query Rewriter" agent here
        return "error"
    return "success"


# Build the Graph
def build_query_graph():
    """Defines and compiles the LangGraph workflow."""
    workflow = StateGraph(AgentState)
    
    # Define Nodes (Agents/Tools)
    workflow.add_node("router", route_to_workspace)
    workflow.add_node("rag_retrieval", retrieve_knowledge_base)
    workflow.add_node("table_pruner", table_prune_agent)
    workflow.add_node("column_pruner", column_prune_agent)
    workflow.add_node("query_gen", query_generation_agent)
    workflow.add_node("query_exec", execute_sql_query)
    workflow.add_node("final_synth", final_answer_agent)

    # Define the Workflow Edges
    workflow.add_edge(START, "router")
    workflow.add_edge("router", "rag_retrieval")
    workflow.add_edge("rag_retrieval", "table_pruner")
    workflow.add_edge("table_pruner", "column_pruner")
    workflow.add_edge("column_pruner", "query_gen")
    workflow.add_edge("query_gen", "query_exec")
    
    # Conditional Edge: If successful, go to synthesis. If error, go straight to synthesis with error.
    workflow.add_conditional_edges(
        "query_exec",
        check_for_error,
        {"success": "final_synth", "error": "final_synth"}
    )

    workflow.add_edge("final_synth", END)

    return workflow.compile()