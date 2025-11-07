from typing import TypedDict, List
from langgraph.graph.message import AnyMessage, MessagesState
from typing_extensions import Annotated
import operator

# Define the state that will be passed between nodes in the graph
class AgentState(TypedDict):
    """Represents the state of the conversation and query generation."""
    
    user_question: str 
    workspace_name: str # 1. Intent Agent Output
    # 2. Table/RAG Agent Output
    relevant_tables: List[str]
    context_schema: Annotated[str, operator.add] # Full schema/rules from KB
    
    # 3. Column Prune Agent Output
    pruned_schema: str # Minimized schema for final prompt
    
    # 4. Query Generation Agent Output
    sql_query: str 
    
    # 5. Executor/Validator Output
    db_result: str
    final_answer: str