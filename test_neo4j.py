import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# Force BOLT instead of NEO4J to bypass cluster routing table fetch
URI_BOLT = os.getenv("NEO4J_URI").replace("neo4j+s://", "bolt+s://")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))

print(f"Testing connection to {URI_BOLT} with username {AUTH[0]}")
try:
    with GraphDatabase.driver(URI_BOLT, auth=AUTH) as driver:
        # verify_connectivity or just run a simple query
        session = driver.session(database=os.getenv("NEO4J_DATABASE", "neo4j"))
        res = session.run("RETURN 1 as test")
        print(f"Result: {res.single()['test']}")
        print("Connection successful!")
except Exception as e:
    import traceback
    traceback.print_exc()
