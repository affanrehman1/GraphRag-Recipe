# Recipe Graph RAG (Retrieval-Augmented Generation) 

A powerful, AI-driven culinary assistant built with **Neo4j** and **LangGraph**. This project ingests a massive recipe dataset into a Knowledge Graph and uses Groq's **Llama 3.1** to answer natural language questions about recipes, ingredients, and cooking methods.

##  System Architecture

The system operates in two distinct phases:

1. **Knowledge Graph Construction (`ingest.py`)**: 
   Reads from the RecipeNLG dataset and builds a Neo4j Graph Database. 
   - **Nodes**: `(Recipe)` containing the title, raw ingredient list, and step-by-step directions. `(Ingredient)` containing isolated, clean ingredient names (e.g., "brown sugar").
   - **Relationships**: `(Recipe)-[:HAS_INGREDIENT]->(Ingredient)`.
   - *Optimization*: Uses batched transactions (1,000 queries per batch) to ensure high-performance ingestion without connection timeouts.

2. **Conversational AI Agent (`graph_agent.py`)**: 
   An interactive LangGraph agent that translates human questions into precise Cypher graph queries using a specialized `GraphCypherQAChain`. It traverses the graph to find connected recipes and ingredients, then uses those strict facts to provide a helpful, natural language response.

##  Technologies Used
- **Python 3.8+**
- **Neo4j AuraDB**: Cloud graph database.
- **LangChain & LangGraph**: Agentic workflow orchestration.
- **Groq API**: High-speed LLM inference running `llama-3.1-8b-instant`.
- **Pandas**: Efficient CSV data processing.

##  Dataset Requirement
This project requires the **RecipeNLG** dataset (a massive dataset of ~2.2M recipes and NER-extracted ingredients).

1. Download the dataset from Kaggle: [RecipeNLG Dataset](https://www.kaggle.com/datasets/paultimothymooney/recipenlg)
2. Extract the archive and place `RecipeNLG_dataset.csv` directly in the root of this project folder.

##  Setup & Installation

**1. Clone the repository and navigate to the folder:**
```bash
git clone https://github.com/affanrehman1/GraphRag-Recipe.git
cd GraphRag-Recipe
```

**2. Create a virtual environment and attach dependencies:**
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

**3. Environment Configuration:**
Create a `.env` file in the root directory. You will need a **Groq API Key** and a **Neo4j AuraDB** instance (the Free Tier works perfectly).

```env
NEO4J_URI=neo4j+ssc://<your-db-id>.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<your-neo4j-password>
NEO4J_DATABASE=neo4j
GROQ_API_KEY=<your-groq-api-key>
```
*(Note: We use `neo4j+ssc://` to bypass strict SSL verification which can block connections in certain terminal environments).*

##  Usage Guide

### Phase 1: Ingest Data
Before you can chat with the AI, you must build the graph!
```bash
python ingest.py
```
**Important AuraDB Note:** Neo4j Free Tier instances have a hard limit of ~50,000 nodes and 175,000 relationships. The ingest script will process recipes rapidly in batches of 1,000 until your free database quota is full. The script will automatically halt gracefully when limits are reached, and your graph will be perfectly usable for those ingested recipes!

### Phase 2: Run the Agent
Start the interactive Graph RAG terminal:
```bash
python graph_agent.py
```
**Example Questions to ask the Chef:**
- *"What is the method to create Rhubarb Coffee Cake?"*
- *"Give me the recipe for Double Cherry Delight."*
- *"What are some recipes that contain bacon and eggs?"*

Type `exit` to end the session.
