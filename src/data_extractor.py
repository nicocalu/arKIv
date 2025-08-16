import os
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
import json
import re
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed


# --- Configuration ---
PAPER_DIR = "papers"
VECTOR_STORE_PATH = "vector_store.index"
METADATA_STORE_PATH = "metadata.json"
MODEL_NAME = 'all-mpnet-base-v2'
# Set the number of parallel processes. Defaults to number of cores.
# On Debian, you can find the number of cores with `nproc`.
# Let's use a few less than max to keep the system responsive.
MAX_WORKERS = 40    

def clean_text(text):
    """
    Cleans the extracted text by removing excessive newlines, special characters,
    and references section.
    """
    # Remove the references/bibliography section
    text = re.split(r'references|bibliography', text, flags=re.IGNORECASE)[0]
    # Remove excessive newlines and whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Optional: Remove hyphenation at line breaks
    text = text.replace('-\n', '')
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

def process_pdf(filepath):
    """
    Processes a single PDF file: extracts, cleans, and chunks text.
    Returns a tuple of (paper_id, list_of_chunks).
    """
    paper_id = os.path.splitext(os.path.basename(filepath))[0]
    try:
        with fitz.open(filepath) as doc:
            full_text = "".join(page.get_text() or "" for page in doc)

        cleaned_text = clean_text(full_text)
        if not cleaned_text:
            return paper_id, []

        text_chunks = chunk_text(cleaned_text)
        return paper_id, text_chunks
    except Exception as e:
        print(f" - Error processing {os.path.basename(filepath)}: {e}")
        return paper_id, []

def main():
    """
    Main function to process PDFs, create embeddings, and build a vector store.
    """
    if not os.path.exists(PAPER_DIR):
        print(f"Directory '{PAPER_DIR}' not found. Please run main.py to download papers first.")
        return

    pdf_files = [os.path.join(PAPER_DIR, f) for f in os.listdir(PAPER_DIR) if f.endswith('.pdf')]
    if not pdf_files:
        print(f"No PDF files found in '{PAPER_DIR}'.")
        return

    all_chunks = []
    metadata = {}
    chunk_id_counter = 0

    print(f"Processing {len(pdf_files)} PDF files using up to {MAX_WORKERS} cores...")
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all PDF processing tasks
        future_to_pdf = {executor.submit(process_pdf, pdf_path): pdf_path for pdf_path in pdf_files}

        # Process results as they complete
        for future in tqdm(as_completed(future_to_pdf), total=len(pdf_files), desc="Processing PDFs"):
            paper_id, text_chunks = future.result()
            if not text_chunks:
                print(f" - No text extracted from {paper_id}.pdf, skipping.")
                continue

            for i, chunk in enumerate(text_chunks):
                chunk_id = f"{paper_id}_chunk_{i}"
                all_chunks.append(chunk)
                metadata[chunk_id_counter] = {
                    "paper_id": paper_id,
                    "chunk_id": chunk_id,
                    "text": chunk
                }
                chunk_id_counter += 1

    if not all_chunks:
        print("No text chunks were generated. Exiting.")
        return

    print("\nLoading sentence transformer model...")
    model = SentenceTransformer(MODEL_NAME)
    print("Model loaded.")

    print(f"\nGenerating embeddings for {len(all_chunks)} text chunks...")
    embeddings = model.encode(all_chunks, show_progress_bar=True, device='cuda' if 'cuda' in str(faiss.get_num_gpus()) else 'cpu')
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