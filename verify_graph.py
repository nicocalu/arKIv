import networkx as nx
from collections import Counter

# --- Configuration ---
GRAPH_PATH = "knowledge_graph.gexf"

def verify_knowledge_graph():
    """
    Loads the knowledge graph and prints a summary of its contents.
    """
    print("--- Verifying Knowledge Graph ---")
    
    try:
        print(f"Loading graph from '{GRAPH_PATH}'...")
        G = nx.read_gexf(GRAPH_PATH)
    except FileNotFoundError:
        print(f"\n[ERROR] Graph file not found at '{GRAPH_PATH}'. Please ensure you have run kg_builder.py successfully.")
        return

    print("\n--- Graph Census ---")
    print(f"Total number of nodes: {G.number_of_nodes()}")
    print(f"Total number of edges: {G.number_of_edges()}")

    if G.number_of_nodes() == 0:
        print("\n[ERROR] The graph is empty! Something went wrong during KG building.")
        return

    # Count nodes by their 'type' attribute
    node_types = [d['type'] for n, d in G.nodes(data=True) if 'type' in d]
    type_counts = Counter(node_types)
    
    print("\nNode counts by type:")
    for node_type, count in type_counts.items():
        print(f"  - {node_type}: {count}")

    # Example: Find a 'Topic' node and see what's connected to it
    print("\n--- Example Node Inspection ---")
    # Find a topic node to inspect, e.g., one with 'risk' in its label
    topic_node_id = None
    for node, data in G.nodes(data=True):
        if data.get('type') == 'Topic' and 'risk' in data.get('label', '').lower():
            topic_node_id = node
            break
    
    if topic_node_id:
        topic_label = G.nodes[topic_node_id]['label']
        print(f"Inspecting neighbors of Topic node: '{topic_label}'")
        
        # Find all neighbors (which should be 'Paper' nodes)
        for neighbor_id in G.neighbors(topic_node_id):
            neighbor_data = G.nodes[neighbor_id]
            print(f"  - Connected to Paper: '{neighbor_data.get('label', 'N/A')}'")
    else:
        print("Could not find an example 'Topic' node containing 'risk' to inspect.")


if __name__ == "__main__":
    verify_knowledge_graph()