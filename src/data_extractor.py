import os
import pdfplumber
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
import json
import re

# --- Configuration ---
PAPER_DIR = "papers"
VECTOR_STORE_PATH = "vector_store.index"
METADATA_STORE_PATH = "metadata.json"
# Using a model well-suited for semantic search
MODEL_NAME = 'all-MiniLM-L6-v2'

def clean_text(text):
    """
    Cleans the extracted text by removing excessive newlines, special characters,
    and references section.
    """
    # Remove the references/bibliography section
    text = re.split(r'references|bibliography', text, flags=re.IGNORECASE)[0]
    # Remove excessive newlines and whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def chunk_text(text, chunk_size=512, overlap=64):
    """
    Splits the text into overlapping chunks.
    """
    tokens = text.split()
    chunks = []
    for i in range(0, len(tokens), chunk_size - overlap):
        chunk = " ".join(tokens[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

def main():
    """
    Main function to process PDFs, create embeddings, and build a vector store.
    """
    if not os.path.exists(PAPER_DIR):
        print(f"Directory '{PAPER_DIR}' not found. Please run main.py to download papers first.")
        return

    print("Loading sentence transformer model...")
    model = SentenceTransformer(MODEL_NAME)
    print("Model loaded.")

    all_chunks = []
    metadata = {}
    chunk_id_counter = 0

    pdf_files = [f for f in os.listdir(PAPER_DIR) if f.endswith('.pdf')]
    if not pdf_files:
        print(f"No PDF files found in '{PAPER_DIR}'.")
        return

    for filename in pdf_files:
        paper_id = os.path.splitext(filename)[0]
        filepath = os.path.join(PAPER_DIR, filename)
        print(f"Processing {filename}...")

        try:
            with pdfplumber.open(filepath) as pdf:
                full_text = "".join(page.extract_text() or "" for page in pdf.pages)

            cleaned_text = clean_text(full_text)
            if not cleaned_text:
                print(f" - No text extracted from {filename}, skipping.")
                continue

            text_chunks = chunk_text(cleaned_text)

            for i, chunk in enumerate(text_chunks):
                chunk_id = f"{paper_id}_chunk_{i}"
                all_chunks.append(chunk)
                metadata[chunk_id_counter] = {
                    "paper_id": paper_id,
                    "chunk_id": chunk_id,
                    "text": chunk
                }
                chunk_id_counter += 1

        except Exception as e:
            print(f" - Error processing {filename}: {e}")

    if not all_chunks:
        print("No text chunks were generated. Exiting.")
        return

    print(f"\nGenerating embeddings for {len(all_chunks)} text chunks...")
    embeddings = model.encode(all_chunks, show_progress_bar=True)
    embedding_dim = embeddings.shape[1]

    print("Building FAISS index...")
    index = faiss.IndexFlatL2(embedding_dim)
    index = faiss.IndexIDMap(index)
    index.add_with_ids(np.array(embeddings).astype('float32'), np.arange(len(all_chunks)))

    print(f"Saving FAISS index to {VECTOR_STORE_PATH}")
    faiss.write_index(index, VECTOR_STORE_PATH)

    print(f"Saving metadata to {METADATA_STORE_PATH}")
    with open(METADATA_STORE_PATH, 'w') as f:
        json.dump(metadata, f, indent=4)

    print("\nData extraction and embedding generation complete.")

if __name__ == "__main__":
    main()
