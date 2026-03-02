import os
from typing import TypedDict, Annotated, List
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_community.graphs import Neo4jGraph
from langchain_neo4j import GraphCypherQAChain
from langgraph.graph import StateGraph, END

# Define the state for our LangGraph
class AgentState(TypedDict):
    question: str
    cypher_result: str
    final_answer: str

# Load Env
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

# Initialize Neo4j Graph
# Note: we use our neo4j+ssc:// bypass for SSL proxy issues
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI").replace("neo4j+s://", "neo4j+ssc://"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
    database=os.getenv("NEO4J_DATABASE", "neo4j")
)

# Initialize Groq LLM
llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0)

# Build a specialized GraphCypherQAChain to query Neo4j
chain = GraphCypherQAChain.from_llm(
    cypher_llm=llm,
    qa_llm=llm,
    graph=graph,
    verbose=True,
    allow_dangerous_requests=True
)

def retrieve_from_graph(state: AgentState):
    """
    This node queries the Neo4j graph to find facts via Cypher.
    """
    print(f"---RETRIEVING FROM GRAPH FOR: {state['question']}---")
    
    try:
        # We ask LangChain to turn the question into a Cypher query and return the context
        result = chain.invoke({"query": state["question"]})
        fact_result = result.get("result", "")
    except Exception as e:
        fact_result = f"Failed to retrieve data from graph: {e}"
        
    return {"cypher_result": fact_result}

def generate_final_answer(state: AgentState):
    """
    Generate final natural language answer based on Knowledge Graph context
    """
    print("---GENERATING FINAL ANSWER---")
    question = state["question"]
    graph_context = state["cypher_result"]
    
    prompt = f"""You are a helpful culinary assistant powered by a Recipe Knowledge Graph.
You MUST answer the user's question based ONLY on the facts retrieved from the graph.
If the Graph Context is empty or doesn't have the answer, say you don't know based on the current database. Do not hallucinate.

User Question: {question}

Facts from Knowledge Graph:
{graph_context}

Provide a friendly, helpful answer:
"""
    response = llm.invoke(prompt)
    return {"final_answer": response.content}

# Create Graph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("GraphRetrieval", retrieve_from_graph)
workflow.add_node("AnswerGeneration", generate_final_answer)

# Define Edges
workflow.set_entry_point("GraphRetrieval")
workflow.add_edge("GraphRetrieval", "AnswerGeneration")
workflow.add_edge("AnswerGeneration", END)

# Compile the Graph
app = workflow.compile()

if __name__ == "__main__":
    print("\\n🤖 Welcome to GraphRAG Recipe Assistant!")
    print("Database connected. Running test query...\\n")
    while(True):
        user_input = input("Chef, what is your question? > ")
        if(user_input.lower() == "exit"):
            break
        
        # Run graph
        state_input = {"question": user_input}
        try:
            result = app.invoke(state_input)
            print("\\n=== ANSWER ===")
            print(result["final_answer"])
            print("================\\n")
        except Exception as e:
            print(f"Error during execution: {e}")
