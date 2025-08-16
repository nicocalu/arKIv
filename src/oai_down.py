from google.cloud import storage
from google.cloud.storage import transfer_manager
import concurrent.futures
from sickle import Sickle
import os
import time
import json

categories = ['q-fin:q-fin', 'stat:stat:ML', 'cs:cs:LG', 'econ:econ:EM']

# 1. Use OAI-PMH to get metadata with category information
def get_papers_by_categories(categories, max_papers=30000, metadata_dir="./metadata/"):
    sickle = Sickle('http://export.arxiv.org/oai2')
    os.makedirs(metadata_dir, exist_ok=True)
    paper_ids = set()  # Use set to avoid duplicates
    
    papers_per_category = max_papers // len(categories)
    
    for category in categories:
            
        try:
            records = sickle.ListRecords(metadataPrefix='arXiv', set=category)
            count = 0
            
            for record in records:
                if count >= papers_per_category:
                    break
                    
                arxiv_id = record.header.identifier.replace('oai:arXiv.org:', '')
                paper_ids.add(arxiv_id)

                metadata = {
                    "id": arxiv_id,
                    "title": record.metadata.get('title', [''])[0],
                    "authors": record.metadata.get('keyname', []),
                    "categories": record.metadata.get('categories', []),
                    "abstract": record.metadata.get('abstract', [''])[0],
                    "date": record.metadata.get('created', [''])[0],
                    "update_date": record.header.datestamp,
                    "doi": record.metadata.get('doi', []),
                }
                
                # Save metadata to file
                with open(os.path.join(metadata_dir, f"{arxiv_id.split('/')[-1]}.json"), 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                count += 1
                
        except Exception as e:
            print(f"Error fetching category {category}: {e}")
    
    return list(paper_ids)

# 2. Use S3 for fast downloading of full PDFs
def download_papers(paper_ids, output_dir='papers', workers = 40):
    os.makedirs(output_dir, exist_ok=True)

    storage_client = storage.Client.create_anonymous_client()
    bucket = storage_client.bucket("arxiv-dataset")

    blob_file_pairs = []
    for paper_id in paper_ids:
        # Convert ID to YYMM format for GCS path
        if '.' in paper_id:
            year_month = paper_id.split('.')[0]
            blob_path = f"arxiv/arxiv/pdf/{year_month}/{paper_id}v1.pdf"
            blob = bucket.blob(blob_path)
            # Just use the paper_id as filename in the destination directory
            destination_file = os.path.join(output_dir, f"{paper_id}.pdf")
            blob_file_pairs.append((blob, destination_file))
        else:
            cat = paper_id.split('/')[0]
            id = paper_id.split('/')[1]
            blob_path = f"arxiv/{cat}/pdf/{id[:4]}/{id}v1.pdf"
            blob = bucket.blob(blob_path)
            # Just use the paper_id as filename in the destination directory
            destination_file = os.path.join(output_dir, f"{id}.pdf")
            blob_file_pairs.append((blob, destination_file))

    results = transfer_manager.download_many(
        blob_file_pairs, max_workers=workers, worker_type="thread"
    )
            
    print(f"Done.")
    
    return len(results)

# Main execution
if __name__ == "__main__":
    max_papers = 7000 # for 6hs runtime
    
    print(f"Fetching metadata for {max_papers} papers in category '{categories}'...")
    paper_ids = get_papers_by_categories(categories, max_papers)
    
    print(f"Found {len(paper_ids)} papers. Downloading...")
    downloaded = download_papers(paper_ids)
    
    print(f"Successfully downloaded {downloaded} papers.")