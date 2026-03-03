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
    chat_history: str
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

CYPHER_GENERATION_TEMPLATE = """Task: Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Schema:
{schema}
Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.
IMPORTANT: When searching for names of recipes or ingredients, ALWAYS use case-insensitive partial matching using toLower() and CONTAINS. For example: `MATCH (r:Recipe) WHERE toLower(r.title) CONTAINS toLower('ribs') RETURN r LIMIT 3`. NEVER use strict equality like `r.title = 'ribs'`. Note that recipe names are stored in the `title` property.
IMPORTANT: If the user asks for a FULL recipe or the cooking directions of a recipe, you MUST traverse the graph to get its ingredients, directions, and the full ingredient list! Do not just return the Recipe node. Example: `MATCH (r:Recipe)-[:HAS_INGREDIENT]->(i:Ingredient) WHERE toLower(r.title) CONTAINS toLower('cherry') RETURN r.title, r.ingredients_list, r.directions, collect(i.name) AS searchable_ingredients LIMIT 3`
IMPORTANT CONTEXT OVERFLOW RULE: If your query returns COMPLETE RECIPES (with directions and lists), you MUST use `LIMIT 3`. NEVER return more than 3 full recipes under any circumstances!
IMPORTANT INGREDIENT LIST RULE: If the user ONLY asks for a list of ingredient items (e.g. "what items use beef"), you must prevent database traversal timeouts. You MUST add `LIMIT 100` directly after the MATCH clause before returning distinct names. Example: 
`MATCH (r:Recipe)-[:HAS_INGREDIENT]->(i:Ingredient) WHERE toLower(r.ingredients_list) CONTAINS 'beef' WITH i LIMIT 100 RETURN DISTINCT i.name LIMIT 25`
IMPORTANT PAGINATION RULE: Graph Queries DO NOT support generic pagination/SKIP well. If the user asks for "different" or "other" recipes, you MUST read the chat history above, extract the titles of the exact recipes you already provided, and EXCLUDE them using a `WHERE NOT toLower(r.title) IN ['dish 1', 'dish 2']` clause. Example substitution logic: `MATCH (r:Recipe) WHERE toLower(r.title) CONTAINS 'beef' AND NOT toLower(r.title) IN ['beef stroganoff', 'beef and bacon casserole'] RETURN r`

The question is:
{question}"""
CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE
)

# Build a specialized GraphCypherQAChain to query Neo4j
chain = GraphCypherQAChain.from_llm(
    cypher_llm=llm,
    qa_llm=llm,
    graph=graph,
    verbose=True,
    allow_dangerous_requests=True,
    cypher_prompt=CYPHER_GENERATION_PROMPT,
    return_direct=True
)

def retrieve_from_graph(state: AgentState):
    """
    This node queries the Neo4j graph to find facts via Cypher.
    """
    print(f"---RETRIEVING FROM GRAPH FOR: {state['question']}---")
    
    try:
        # We ask LangChain to turn the question into a Cypher query and return the context
        query_text = state["question"]
        if state.get("chat_history"):
            query_text = f"Chat History:\n{state['chat_history']}\n\nLatest Question: {state['question']}"
        result = chain.invoke({"query": query_text})
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
    graph_context = str(state.get("cypher_result", ""))
    
    # Hard truncation to prevent LLM Token Rate Limit errors (6000 TPM limit on Groq)
    if len(graph_context) > 12000:
        print(f"Truncating massive graph context from {len(graph_context)} chars to 12000 chars...")
        graph_context = graph_context[:12000] + "\\n...[TRUNCATED TO PREVENT TOKEN OVERFLOW]"

    chat_history = state.get("chat_history", "")
    
    prompt = f"""You are a helpful culinary assistant powered by a Recipe Knowledge Graph.
You MUST answer the user's question based ONLY on the facts retrieved from the graph.
If the Graph Context is empty or doesn't have the answer, say you don't know based on the current database. Do not hallucinate.

Chat History:
{chat_history}

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
    
    chat_history_str = ""
    while(True):
        user_input = input("Chef, what is your question? > ")
        if(user_input.lower() == "exit"):
            break
        
        # Run graph
        state_input = {"question": user_input, "chat_history": chat_history_str}
        try:
            result = app.invoke(state_input)
            answer = result["final_answer"]
            print("\\n=== ANSWER ===")
            print(answer)
            print("================\\n")
            
            # Update chat history for the next iteration
            chat_history_str += f"User: {user_input}\\nAssistant: {answer}\\n\\n"
        except Exception as e:
            print(f"Error during execution: {e}")
