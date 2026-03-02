# Recipe GraphRAG Assistant

This project implements a Graph Retrieval-Augmented Generation (GraphRAG) system designed to answer questions about recipes. It leverages a Neo4j knowledge graph to store recipe and ingredient relationships and uses Groq's Large Language Models (LLMs) via LangChain and LangGraph to provide intelligent, context-aware answers.

## Architecture

The system consists of two main components:

1.  **Data Ingestion (`ingest.py`)**: Reads recipe data from a CSV file (`RAW_recipes.csv`) and constructs a knowledge graph in Neo4j. It creates `Recipe` and `Ingredient` nodes and links them with `HAS_INGREDIENT` relationships.
2.  **Conversational Agent (`graph_agent.py`)**: A LangGraph-based agent that accepts natural language questions from the user. It uses LangChain's `GraphCypherQAChain` to translate these questions into Cypher queries, retrieves relevant facts from the Neo4j database, and generates a final, natural language response using the Groq LLM.

## Prerequisites

*   Python 3.8 or higher
*   A Neo4j AuraDB instance (Free tier is sufficient for the sample data)
*   A Groq API Key

## Setup and Installation

1.  **Install Dependencies**:
    Install the required Python packages using pip:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Configuration**:
    Create a `.env` file in the root directory of the project and populate it with your Neo4j and Groq credentials:
    ```env
    NEO4J_URI=neo4j+ssc://<your-db-id>.databases.neo4j.io
    NEO4J_USERNAME=neo4j
    NEO4J_PASSWORD=<your-neo4j-password>
    NEO4J_DATABASE=neo4j
    GROQ_API_KEY=<your-groq-api-key>
    ```
    *Note: The URI scheme `neo4j+ssc://` is used to bypass strict SSL verification which can sometimes cause issues in certain network environments.*

## Usage

1.  **Ingest Data**:
    Run the ingestion script to populate your Neo4j database with a sample of the recipe data.
    ```bash
    python ingest.py
    ```
    Wait for the script to confirm that the ingestion is complete.

2.  **Run the Agent**:
    Start the interactive conversational agent.
    ```bash
    python graph_agent.py
    ```
    Once the application starts, you can ask questions such as "What are some recipes that contain bacon?" or "How long does it take to make [Recipe Name]?". Type `exit` to terminate the session.

## Notes

*   The ingestion script currently samples the first 200 recipes from the dataset to accommodate the limits of free Neo4j AuraDB instances. You can adjust the `SAMPLE_SIZE` variable in `ingest.py` to load more data.
*   Ensure that the `RAW_recipes.csv` file is present in the project directory before running the ingestion script.
