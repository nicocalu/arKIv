import os
import json
import requests
import time
import networkx as nx
from tqdm import tqdm
import re  # Import the regular expression module

# Import configuration from config.py
# NOTE: We will ignore the API key from config and use a local endpoint instead.
from config import EXTRACTION_PROMPT_TEMPLATE

# --- Configuration ---
METADATA_DIR = "metadata"
GRAPH_OUTPUT_PATH = "knowledge_graph.gexf"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# --- Local LLM Configuration ---
LOCAL_LLM_ENDPOINT = "http://localhost:11434/api/chat" # Default for Ollama
LOCAL_MODEL_NAME = "llama3.1:8b" # The model you have installed

def sanitize_for_xml(text):
    """Removes characters that are invalid in XML 1.0."""
    if not isinstance(text, str):
        return text
    # Use a regex to remove illegal control characters.
    # XML 1.0 spec allows #x9, #xA, #xD, and chars in [#x20-#xD7FF] etc.
    # This regex removes most common invalid characters.
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

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
    Reads metadata, calls the LLM to extract entities, and builds a knowledge graph.
    """
    if not os.path.exists(METADATA_DIR):
        print(f"Error: Metadata directory '{METADATA_DIR}' not found.")
        return

    G = nx.Graph()
    existing_topics = set()

    files_to_process = [f for f in os.listdir(METADATA_DIR) if f.endswith('.json')]
    
    for filename in tqdm(files_to_process, desc="Building Knowledge Graph"):
        filepath = os.path.join(METADATA_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            paper_data = json.load(f)

        paper_id = paper_data.get("id", "Unknown")
        # Sanitize all text data before adding it to the graph
        paper_title = sanitize_for_xml(paper_data.get("title", "Unknown Title"))
        authors = paper_data.get("authors", [])
        abstract = paper_data.get("abstract", "")

        if not abstract:
            continue

        # Add paper node
        G.add_node(paper_id, label=paper_title, type="paper")
        
        # Add author nodes and edges
        for author_name in authors:
            sanitized_author = sanitize_for_xml(author_name)
            if sanitized_author not in G:
                G.add_node(sanitized_author, label=sanitized_author, type="author")
            G.add_edge(paper_id, sanitized_author)
        
        # Extract and add methodology and topic nodes
        extracted_data = call_llm_api(abstract, existing_topics)
        
        if extracted_data:
            for methodology in extracted_data.get("methodologies", []):
                sanitized_methodology = sanitize_for_xml(methodology)
                if sanitized_methodology not in G:
                    G.add_node(sanitized_methodology, label=sanitized_methodology, type="methodology")
                G.add_edge(paper_id, sanitized_methodology)

            for topic in extracted_data.get("topics", []):
                sanitized_topic = sanitize_for_xml(topic)
                if sanitized_topic not in G:
                    G.add_node(sanitized_topic, label=sanitized_topic, type="topic")
                existing_topics.add(sanitized_topic)
                G.add_edge(paper_id, sanitized_topic)
    
    print(f"\nKnowledge graph construction complete.")
    print(f" - Total nodes: {G.number_of_nodes()}")
    print(f" - Total edges: {G.number_of_edges()}")

    # Save the graph
    nx.write_gexf(G, GRAPH_OUTPUT_PATH)
    print(f"Graph saved to {GRAPH_OUTPUT_PATH}")


if __name__ == "__main__":
    main()