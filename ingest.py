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
SAMPLE_SIZE = 200

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
    df = pd.read_csv("RAW_recipes.csv")
    
    # Take a sample
    df_sample = df.head(SAMPLE_SIZE).copy()
    
    # Parse the ingredients column
    df_sample["parsed_ingredients"] = df_sample["ingredients"].apply(parse_ingredients)
    
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

        # 2. Ingest the data
        print(f"Ingesting {SAMPLE_SIZE} recipes...")
        
        for index, row in df_sample.iterrows():
            recipe_id = row['id']
            recipe_name = row['name']
            minutes = row['minutes']
            ingredients = row['parsed_ingredients']
            
            # Print progress every 50 recipes
            if index % 50 == 0:
                print(f"Processed {index} recipes...")

            query = """
            // Create or match Recipe
            MERGE (r:Recipe {id: $recipe_id})
            SET r.name = $recipe_name, r.minutes = $minutes
            
            WITH r
            // Unwind the ingredients list passed as a parameter
            UNWIND $ingredients AS ingredient_name
            
            // Create or match Ingredient
            MERGE (i:Ingredient {name: ingredient_name})
            
            // Create Relationship
            MERGE (r)-[:HAS_INGREDIENT]->(i)
            """
            
            try:
                session.run(query, recipe_id=recipe_id, recipe_name=recipe_name, 
                            minutes=minutes, ingredients=ingredients)
            except Exception as e:
                print(f"Failed to ingest recipe {recipe_id}: {e}")
                
        print("Ingestion complete!")
        
        # Verify
        result = session.run("MATCH (r:Recipe) RETURN count(r) as recipe_count")
        print(f"Total recipes in db: {result.single()['recipe_count']}")
        
        result = session.run("MATCH (i:Ingredient) RETURN count(i) as ingredient_count")
        print(f"Total ingredients in db: {result.single()['ingredient_count']}")

    driver.close()

if __name__ == "__main__":
    main()
