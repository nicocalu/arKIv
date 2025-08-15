import os
import json
import requests
import networkx as nx
from tqdm import tqdm
import time

# Import configuration from config.py
# NOTE: We will ignore the API key from config and use a local endpoint instead.
from src.config import EXTRACTION_PROMPT_TEMPLATE

# --- Configuration ---
METADATA_DIR = "metadata"
GRAPH_OUTPUT_PATH = "knowledge_graph.gexf"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# --- NEW: Local LLM Configuration ---
LOCAL_LLM_ENDPOINT = "http://localhost:11434/api/chat" # Default for Ollama
LOCAL_MODEL_NAME = "llama3.1:8b" # The model you have installed

def call_llm_api(abstract, existing_topics):
    """
    Calls a LOCAL LLM API (like Ollama) to extract entities from the abstract.
    """
    topics_str = ", ".join(f'"{t}"' for t in sorted(list(existing_topics))) if existing_topics else "None"
    
    prompt = EXTRACTION_PROMPT_TEMPLATE.format(
        abstract=abstract,
        existing_topics=topics_str
    )

    # The payload structure for Ollama is slightly different
    payload = {
        "model": LOCAL_MODEL_NAME, 
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "format": "json", # Ollama's way of ensuring JSON output
        "stream": False   # We want the full response at once
    }

    for attempt in range(MAX_RETRIES):
        try:
            # Note: No headers needed for a local, unsecured endpoint
            response = requests.post(LOCAL_LLM_ENDPOINT, json=payload, timeout=120) # Increased timeout for local model
            response.raise_for_status()
            
            # Ollama nests the JSON content differently
            response_data = response.json()
            content = response_data['message']['content']
            return json.loads(content)

        except requests.exceptions.RequestException as e:
            print(f" - Local server error: {e}. Is Ollama running? Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
        except (json.JSONDecodeError, KeyError) as e:
            print(f" - Error decoding JSON or parsing response from local model: {e}. Retrying...")
            time.sleep(RETRY_DELAY)
    
    print(" - Failed to get a valid response from the local model after multiple retries.")
    return None


def main():
    """
    Main function to build the knowledge graph from paper metadata.
    """
    if not os.path.exists(METADATA_DIR):
        print(f"Directory '{METADATA_DIR}' not found. Please run main.py to download papers and metadata first.")
        return

    G = nx.Graph()
    metadata_files = [f for f in os.listdir(METADATA_DIR) if f.endswith('.json')]

    if not metadata_files:
        print(f"No metadata files found in '{METADATA_DIR}'.")
        return

    print(f"Found {len(metadata_files)} metadata files. Starting knowledge graph construction...")

    # Set to keep track of topics already in the graph
    existing_topics = set()

    for filename in tqdm(metadata_files, desc="Processing papers"):
        filepath = os.path.join(METADATA_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        paper_id = metadata['paper_id']
        title = metadata['title']
        authors = metadata['authors']
        abstract = metadata['abstract']

        # Add paper node
        G.add_node(paper_id, label=title, type='paper', title=title)

        # Add author nodes and connect them to the paper
        for author in authors:
            G.add_node(author, label=author, type='author')
            G.add_edge(paper_id, author, label='authored_by')

        # Extract entities from abstract using LLM
        print(f"\nProcessing: {title}")
        # Pass the current list of topics to the API call
        extracted_data = call_llm_api(abstract, list(existing_topics))

        if extracted_data:
            # Add methodology nodes and connect them
            for methodology in extracted_data.get('methodologies', []):
                G.add_node(methodology, label=methodology, type='methodology')
                G.add_edge(paper_id, methodology, label='uses_methodology')

            # Add topic nodes and connect them
            for topic in extracted_data.get('topics', []):
                # Add to the graph
                G.add_node(topic, label=topic, type='topic')
                G.add_edge(paper_id, topic, label='has_topic')
                # Add to our set of existing topics for the next API call
                existing_topics.add(topic)
        else:
            print(f" - Skipping entity extraction for '{title}' due to API failure.")


    print(f"\nKnowledge graph construction complete.")
    print(f" - Nodes: {G.number_of_nodes()}")
    print(f" - Edges: {G.number_of_edges()}")

    # Save the graph
    nx.write_gexf(G, GRAPH_OUTPUT_PATH)
    print(f"\nGraph saved to {GRAPH_OUTPUT_PATH}")
    print("You can open this file with a graph visualization tool like Gephi.")


if __name__ == "__main__":
    main()
