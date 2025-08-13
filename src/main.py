import arxiv
import os
import json

# --- Configuration ---
CATEGORIES = ['q-fin', 'stat.ML', 'cs.LG', 'econ.EM']
MAX_RESULTS = 20  # for testing
DOWNLOAD_DIR = "papers"
METADATA_DIR = "metadata"

def main():
    """
    Main function to scrape and download papers and their metadata from arXiv.
    """
    # Ensure the download and metadata directories exist
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
    if not os.path.exists(METADATA_DIR):
        os.makedirs(METADATA_DIR)

    # Construct the search query
    query = " OR ".join([f"cat:{cat}" for cat in CATEGORIES])

    # Construct the default API client.
    client = arxiv.Client()

    # Search for the most recent articles matching the query
    search = arxiv.Search(
      query=query,
      max_results=MAX_RESULTS,
      sort_by=arxiv.SortCriterion.SubmittedDate
    )

    print(f"Searching for the {MAX_RESULTS} most recent papers in categories: {', '.join(CATEGORIES)}")

    results = client.results(search)

    # Download papers and save metadata
    for paper in results:
        paper_id = paper.get_short_id()
        pdf_filename = f"{paper_id}.pdf"
        metadata_filename = f"{paper_id}.json"
        
        pdf_filepath = os.path.join(DOWNLOAD_DIR, pdf_filename)
        metadata_filepath = os.path.join(METADATA_DIR, metadata_filename)

        # --- Download PDF ---
        try:
            if os.path.exists(pdf_filepath):
                print(f"Skipping PDF for '{paper.title}', already downloaded.")
            else:
                print(f"Downloading PDF for '{paper.title}'...")
                paper.download_pdf(dirpath=DOWNLOAD_DIR, filename=pdf_filename)
                print(f" -> Saved to {pdf_filepath}")
        except Exception as e:
            print(f"Error downloading PDF for '{paper.title}': {e}")
            continue # Skip metadata if PDF fails

        # --- Save Metadata ---
        try:
            if os.path.exists(metadata_filepath):
                 print(f"Skipping metadata for '{paper.title}', already exists.")
            else:
                print(f"Saving metadata for '{paper.title}'...")
                metadata = {
                    "paper_id": paper_id,
                    "title": paper.title,
                    "authors": [author.name for author in paper.authors],
                    "abstract": paper.summary,
                    "published_date": paper.published.isoformat(),
                    "categories": paper.categories
                }
                with open(metadata_filepath, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=4)
                print(f" -> Saved to {metadata_filepath}")

        except Exception as e:
            print(f"Error saving metadata for '{paper.title}': {e}")


    print("\nScraping complete.")

if __name__ == "__main__":
    main()
