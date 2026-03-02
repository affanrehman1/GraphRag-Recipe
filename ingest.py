import os
import ast
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables (NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Number of recipes to sample so we don't blow up the free instance
SAMPLE_SIZE = 267784

def parse_ingredients(ingredients_str):
    try:
        # Convert string representation of list to actual Python list
        return ast.literal_eval(ingredients_str)
    except (ValueError, SyntaxError):
        return []

def main():
    if not NEO4J_URI or not NEO4J_PASSWORD:
        print("Error: Neo4j credentials not found in .env file.")
        return

    print("Loading recipes dataset...")
    df = pd.read_csv("RecipeNLG_dataset.csv")
    
    # Take a sample
    df_sample = df.head(SAMPLE_SIZE).copy()
    
    # Parse the ingredients column using NER for the relationship graph
    df_sample["parsed_ingredients"] = df_sample["NER"].apply(parse_ingredients)
    
    # The actual readable ingredients and directions strings
    df_sample["ingredients_list"] = df_sample["ingredients"].astype(str)
    df_sample["directions"] = df_sample["directions"].astype(str)
    
    print(f"Connecting to Neo4j at {NEO4J_URI}...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    with driver.session() as session:
        # 1. Create constraints for fast lookup and to avoid duplicates
        try:
            session.run("CREATE CONSTRAINT recipe_id IF NOT EXISTS FOR (r:Recipe) REQUIRE r.id IS UNIQUE")
            session.run("CREATE CONSTRAINT ingredient_name IF NOT EXISTS FOR (i:Ingredient) REQUIRE i.name IS UNIQUE")
            print("Constraints created.")
        except Exception as e:
            print(f"Warning on constraints: {e}")

        # 2. Ingest the data in batches for better performance and stability
        batch_size = 1000
        batch = []
        total_recipes = len(df_sample)
        print(f"Ingesting {total_recipes} recipes in batches of {batch_size}...")
        
        def insert_recipes(tx, batch_data):
            query = """
            UNWIND $batch AS row
            MERGE (r:Recipe {id: row.id})
            SET r.title = row.title,
                r.ingredients_list = row.ingredients_list,
                r.directions = row.directions
            
            WITH r, row
            UNWIND row.ingredients AS ingredient_name
            MERGE (i:Ingredient {name: ingredient_name})
            MERGE (r)-[:HAS_INGREDIENT]->(i)
            """
            tx.run(query, batch=batch_data)

        for index, row in df_sample.iterrows():
            batch.append({
                'id': str(index),
                'title': row['title'],
                'ingredients': row['parsed_ingredients'],
                'ingredients_list': row['ingredients_list'],
                'directions': row['directions']
            })
            
            if len(batch) >= batch_size:
                try:
                    session.execute_write(insert_recipes, batch)
                except Exception as e:
                    print(f"Failed to ingest batch ending at recipe {index}: {e}")
                batch = []
                print(f"Processed {index+1}/{total_recipes} recipes...")
                
        # Ingest any remaining recipes
        if batch:
            try:
                session.execute_write(insert_recipes, batch)
                print(f"Processed {total_recipes}/{total_recipes} recipes...")
            except Exception as e:
                print(f"Failed to ingest final batch: {e}")

        print("Ingestion complete!")
        
        # Verify
        result = session.run("MATCH (r:Recipe) RETURN count(r) as recipe_count")
        print(f"Total recipes in db: {result.single()['recipe_count']}")
        
        result = session.run("MATCH (i:Ingredient) RETURN count(i) as ingredient_count")
        print(f"Total ingredients in db: {result.single()['ingredient_count']}")

    driver.close()

if __name__ == "__main__":
    main()
