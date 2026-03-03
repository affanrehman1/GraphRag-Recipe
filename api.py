import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import the existing graph application from your script
from graph_agent import app as graph_app

# Define incoming request model
class ChatRequest(BaseModel):
    question: str
    chat_history: str = ""

app = FastAPI(title="GraphRAG Recipe API")

# Add CORS so Next.js frontend can communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Default Next.js port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Receives a question and history from the frontend, queries the graph,
    and returns the final answer.
    """
    state_input = {
        "question": request.question,
        "chat_history": request.chat_history
    }
    
    try:
        # Invoke the LangGraph app
        result = graph_app.invoke(state_input)
        
        return {
            "answer": result["final_answer"],
            "status": "success"
        }
    except Exception as e:
        return {
            "answer": f"I hit an error trying to search the recipe database: {str(e)}",
            "status": "error"
        }

if __name__ == "__main__":
    print("🚀 Starting Recipe GraphRAG API Server on port 8000...")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
