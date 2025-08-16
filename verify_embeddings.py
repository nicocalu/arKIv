import faiss
import json
from sentence_transformers import SentenceTransformer

# --- Configuration ---
VECTOR_STORE_PATH = "vector_store.index"
TEXT_METADATA_PATH = "metadata.json"
MODEL_NAME = 'all-mpnet-base-v2'

def verify_vector_search():
    """
    Loads the vector store and performs a test query to verify its contents.
    """
    print("--- Verifying Vector Embeddings and Search ---")
    
    try:
        # 1. Load all necessary components
        print(f"Loading model '{MODEL_NAME}'...")
        model = SentenceTransformer(MODEL_NAME)
        
        print(f"Loading FAISS index from '{VECTOR_STORE_PATH}'...")
        index = faiss.read_index(VECTOR_STORE_PATH)
        
        print(f"Loading text metadata from '{TEXT_METADATA_PATH}'...")
        with open(TEXT_METADATA_PATH, 'r') as f:
            text_metadata = json.load(f)

    except FileNotFoundError as e:
        print(f"\n[ERROR] Could not find a required file: {e}. Please ensure you have run data_extractor.py successfully.")
        return

    # 2. Print basic statistics
    print(f"\n[OK] All components loaded successfully.")
    print(f"Number of vectors in FAISS index: {index.ntotal}")
    print(f"Number of text chunks in metadata: {len(text_metadata)}")

    if index.ntotal == 0:
        print("\n[ERROR] The vector index is empty! Something went wrong during data extraction.")
        return
        
    # 3. Perform a test query
    test_query = "GARCH models for financial risk"
    print(f"\n--- Performing test search for: '{test_query}' ---")
    
    query_embedding = model.encode([test_query])
    
    # Search the index for the 3 most similar vectors
    k = 3
    distances, indices = index.search(query_embedding, k)
    
    # 4. Display the results
    print(f"Top {k} results found:\n")
    for i, idx in enumerate(indices[0]):
        if idx == -1:
            print(f"Result {i+1}: No more results found.")
            continue
            
        # Retrieve the chunk text using the index
        chunk_info = text_metadata.get(str(idx))
        if chunk_info:
            print(f"--- Result {i+1} (Paper: {chunk_info['paper_id']}, Distance: {distances[0][i]:.4f}) ---")
            print(f"...{chunk_info['chunk_id']}...")
            print("-" * 20 + "\n")
        else:
            print(f"[WARNING] Index {idx} found in FAISS but not in metadata file.")


if __name__ == "__main__":
    verify_vector_search()