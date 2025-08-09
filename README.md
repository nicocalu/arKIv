# arKIv
Python Agents for ArXiv Scraping and Knowledge Graph Construction in  Quantitative Finance

## Objective: 
To design, implement, and deploy a system of autonomous Python agents that continuously 
scrape and process research papers from arXiv.org related to **quantitative finance**, extract 
structured information, and populate a **knowledge graph**. The graph will serve as a rich, 
context-aware database to augment the reasoning and retrieval capabilities of a **large 
language model (LLM)**, enabling it to answer detailed technical questions about research 
trends, methodologies, authors, institutions, citations, and more. 
## Key Goals: 
1. **Automate Discovery and Scraping:** Develop agents to autonomously query and 
download relevant papers from arXiv, particularly from categories such as q-fin, stat.ML, 
cs.LG, and econ.EM. 
2. **Extract Structured Data:** Parse the metadata (title, authors, abstract, affiliations, dates, 
references, categories) and _potentially full text_ of each paper to extract key entities and 
relationships. 
3. **Build a Knowledge Graph (KG):** Construct a semantic, graph-based representation of 
extracted data, capturing: 
  - Research topics and subdomains 
  - Methodologies and models used (e.g., GARCH, LSTM, RL, etc.) 
  - Authors and their affiliations 
  - Citation relationships 
  - Datasets and benchmarks used 
  - Temporal trends and co-authorship networks 
4. **Enable LLM Integration:** Provide a querying interface (e.g., vector search over 
embeddings) to allow an LLM to access contextualized information from the knowledge 
graph when answering user queries.

## Acknowledgements
Thank you to arXiv for use of its open access interoperability.
