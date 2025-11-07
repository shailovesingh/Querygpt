# app.py
import streamlit as st
import pandas as pd
from agents.workflow import build_query_graph
from agents.state import AgentState
from dotenv import load_dotenv
import time
import os

load_dotenv()
graph = build_query_graph()

st.set_page_config(layout="wide", page_title="QueryGPT: Multi-Agent Text-to-SQL")
st.title("🤖 QueryGPT: Multi-Agent Text-to-SQL")
st.markdown("A prototype demonstrating high-performance, contextual query generation using **LangGraph** (Orchestration) and **Groq** (Speed).")

if not os.getenv("GROQ_API_KEY"):
    st.error("Please set the `GROQ_API_KEY` in your `.env` file.")
else:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("1. User Input")
        initial_question = st.text_area(
            "Enter your natural language question:", 
            value="Find the name and current rating of active drivers who drove a trip in Seattle.",
            height=100
        )
        
        if st.button("Generate Query and Run", type="primary"):
            
            # Initialize State
            initial_state = AgentState(
                user_question=initial_question,
                workspace_name="",
                relevant_tables=[],
                context_schema="",
                pruned_schema="",
                sql_query="",
                db_result="",
                final_answer=""
            )
            
            # EXECUTION
            start_time = time.time()
            st.session_state['execution_log'] = []
            
            # Stream/Iterate through the LangGraph steps
            for step in graph.stream(initial_state):
                node_name, new_state = next(iter(step.items()))
                
                # Capture the state change for visualization
                st.session_state['execution_log'].append((node_name, new_state))

            total_time = time.time() - start_time
            # END EXECUTION
            
            st.subheader("Final Result")
            st.success(f"**Final Answer:** {st.session_state['execution_log'][-1][1]['final_answer']}")
            st.metric("Total Execution Time (with Groq)", f"{total_time:.2f} seconds")
            st.markdown(f"**Generated SQL:**\n```sql\n{st.session_state['execution_log'][-1][1]['sql_query']}\n```")

    with col2:
        st.header("2. Multi-Agent Workflow Execution (LangGraph)")
        
        if 'execution_log' in st.session_state:
            log_data = []
            
            for i, (node_name, state) in enumerate(st.session_state['execution_log']):
                
                step_data = {
                    "Step": i + 1,
                    "Agent/Tool": node_name,
                    "Details": ""
                }

                if node_name == "router":
                    step_data["Details"] = f"**Intent Classified:** {state.get('workspace_name', 'N/A')}"
                elif node_name == "rag_retrieval":
                    schema_len = len(state.get('context_schema', ''))
                    step_data["Details"] = f"**RAG Retrieval (Full Context):** {schema_len} characters of schema/rules."
                elif node_name == "table_pruner":
                    tables = state.get('relevant_tables', [])
                    step_data["Details"] = f"**Tables Selected:** {', '.join(tables)}"
                elif node_name == "column_pruner":
                    pruned_len = len(state.get('pruned_schema', ''))
                    step_data["Details"] = f"**Schema Pruned:** Final prompt context is {pruned_len} characters."
                elif node_name == "query_gen":
                    step_data["Details"] = f"**Query Generated (Groq 70b):** {state.get('sql_query', 'N/A')[:50]}..."
                elif node_name == "query_exec":
                    result = state.get('db_result', 'N/A')
                    step_data["Details"] = f"**SQL Executed:** {'Success' if not result.startswith('SQL ERROR') else 'Error'}"
                elif node_name == "final_synth":
                    step_data["Details"] = "**Answer Synthesized**"
                    
                log_data.append(step_data)

            # Display the log in a clear table
            df_log = pd.DataFrame(log_data)
            st.dataframe(df_log, use_container_width=True, hide_index=True)
            
            # Show the final DB result for full transparency
            final_db_result = st.session_state['execution_log'][-1][1]['db_result']
            st.subheader("Raw Database Result")
            st.text(final_db_result)