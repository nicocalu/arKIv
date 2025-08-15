import networkx as nx
import os

# --- Configuration ---
GRAPH_PATH = "knowledge_graph.gexf"

def interactive_inspector():
    """
    Loads the knowledge graph and provides an interactive prompt to inspect nodes.
    """
    print("--- Interactive Knowledge Graph Inspector ---")
    
    if not os.path.exists(GRAPH_PATH):
        print(f"\n[ERROR] Graph file not found at '{GRAPH_PATH}'.")
        print("Please run kg_builder.py to create the graph first.")
        return

    try:
        print(f"Loading graph from '{GRAPH_PATH}'... (This may take a moment)")
        G = nx.read_gexf(GRAPH_PATH)
        print(f"[OK] Graph loaded with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    except Exception as e:
        print(f"\n[ERROR] Failed to load or parse the graph file: {e}")
        return

    while True:
        print("\n-------------------------------------------")
        query = input("Enter a node name to search for (or 'q' to quit): ").strip()

        if query.lower() in ['q', 'quit', 'exit']:
            break
        
        if not query:
            continue

        # Find nodes that contain the query string (case-insensitive)
        matches = []
        for node_id, data in G.nodes(data=True):
            label = data.get('label', '')
            if query.lower() in label.lower():
                matches.append((node_id, data))

        if not matches:
            print(f"No nodes found matching '{query}'.")
            continue
        
        # --- Handle multiple matches ---
        node_id_to_inspect = None
        if len(matches) > 1:
            print(f"Found {len(matches)} potential matches for '{query}':")
            for i, (node_id, data) in enumerate(matches):
                print(f"  [{i}] {data.get('label')} (Type: {data.get('type', 'N/A')})")
            
            try:
                choice = int(input("Which one do you want to inspect? (Enter number): "))
                if 0 <= choice < len(matches):
                    node_id_to_inspect = matches[choice][0]
                else:
                    print("Invalid choice.")
                    continue
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue
        else:
            node_id_to_inspect = matches[0][0]

        # --- Display Node Information ---
        if node_id_to_inspect:
            node_data = G.nodes[node_id_to_inspect]
            print("\n--- Node Details ---")
            print(f"Label: {node_data.get('label')}")
            print(f"Type:  {node_data.get('type')}")
            print("--------------------")
            
            neighbors = list(G.neighbors(node_id_to_inspect))
            if neighbors:
                print(f"Found {len(neighbors)} connections (neighbors):")
                for neighbor_id in neighbors:
                    neighbor_data = G.nodes[neighbor_id]
                    print(f"  - {neighbor_data.get('label')} (Type: {neighbor_data.get('type')})")
            else:
                print("This node has no connections.")

if __name__ == "__main__":
    interactive_inspector()