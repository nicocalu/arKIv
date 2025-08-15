import arxiv
import os
import json
from tqdm import tqdm

# --- Configuration ---
CATEGORIES = ['q-fin', 'stat.ML', 'cs.LG', 'econ.EM']
MAX_RESULTS = 1000  # Set to your desired total
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

    custom_client = arxiv.Client(
        page_size=99,
        num_retries=5
    )

    # Search for the most recent articles matching the query, using our custom client.
    search = arxiv.Search(
      query=query,
      max_results=MAX_RESULTS,
      sort_by=arxiv.SortCriterion.SubmittedDate,
      client=custom_client
    )

    print(f"Searching for up to {MAX_RESULTS} recent papers in categories: {', '.join(CATEGORIES)}")

    # Using a try/except block for the iterator is a good practice for API calls
    try:
        # Iterate directly over the search results. This handles pagination more simply.
        # The tqdm wrapper provides a progress bar.
        results_iterator = search.results()
        for paper in tqdm(results_iterator, total=MAX_RESULTS, desc="Processing papers"):
            paper_id = paper.get_short_id()
            pdf_filename = f"{paper_id}.pdf"
            metadata_filename = f"{paper_id}.json"
            
            pdf_filepath = os.path.join(DOWNLOAD_DIR, pdf_filename)
            metadata_filepath = os.path.join(METADATA_DIR, metadata_filename)

            # Check if metadata exists, if so, we assume the PDF is also handled.
            if os.path.exists(metadata_filepath):
                continue

            # --- Download PDF ---
            try:
                paper.download_pdf(dirpath=DOWNLOAD_DIR, filename=pdf_filename)
            except Exception as e:
                # Using tqdm.write is better for printing inside a loop
                tqdm.write(f"Error downloading PDF for '{paper.title}': {e}")
                continue # Skip metadata if PDF fails

            # --- Save Metadata ---
            try:
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

            except Exception as e:
                tqdm.write(f"Error saving metadata for '{paper.title}': {e}")

    except arxiv.UnexpectedEmptyPageError as e:
        # This error is less likely now, but we keep the handler as a safeguard.
        tqdm.write(f"\n[WARNING] Hit an empty page from arXiv API: {e}. This can happen with very large result sets.")
        tqdm.write("Processing will continue with the papers downloaded so far.")
    except Exception as e:
        tqdm.write(f"\n[ERROR] An unexpected error occurred: {e}")

    print("\nScraping run complete.")

if __name__ == "__main__":
    main()