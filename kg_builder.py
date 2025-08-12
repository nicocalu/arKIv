import os
import json
import requests
import networkx as nx
from tqdm import tqdm
import time

# Import configuration from config.py
from config import LLM_API_KEY, LLM_API_ENDPOINT, EXTRACTION_PROMPT_TEMPLATE

# --- Configuration ---
METADATA_DIR = "metadata"
GRAPH_OUTPUT_PATH = "knowledge_graph.gexf"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def call_llm_api(abstract):
    """
    Calls the configured LLM API to extract entities from the abstract.
    Includes retry logic for handling transient API errors.
    """
    if LLM_API_KEY == "YOUR_API_KEY_HERE" or LLM_API_ENDPOINT == "YOUR_API_ENDPOINT_HERE":
        raise ValueError("Please update LLM_API_KEY and LLM_API_ENDPOINT in config.py")

    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }
    # This payload structure is common for OpenAI-compatible APIs.
    # You may need to adjust it based on your specific provider.
    payload = {
        "model": "gpt-3.5-turbo", # Or any other model your provider supports
        "messages": [
            {"role": "user", "content": EXTRACTION_PROMPT_TEMPLATE.format(abstract=abstract)}
        ],
        "temperature": 0.0, # We want deterministic output
        "response_format": {"type": "json_object"}
    }

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(LLM_API_ENDPOINT, headers=headers, json=payload, timeout=60)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            
            # The actual content is usually in response.json()['choices'][0]['message']['content']
            # We will try to parse it as JSON.
            content = response.json()['choices'][0]['message']['content']
            return json.loads(content)

        except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
            print(f" - API Error: {e}. Retrying in {RETRY_DELAY}s... (Attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(RETRY_DELAY)
    
    print(" - Failed to get a valid response from the API after multiple retries.")
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
        extracted_data = call_llm_api(abstract)

        if extracted_data:
            # Add methodology nodes and connect them
            for methodology in extracted_data.get('methodologies', []):
                G.add_node(methodology, label=methodology, type='methodology')
                G.add_edge(paper_id, methodology, label='uses_methodology')

            # Add topic nodes and connect them
            for topic in extracted_data.get('topics', []):
                G.add_node(topic, label=topic, type='topic')
                G.add_edge(paper_id, topic, label='has_topic')
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
