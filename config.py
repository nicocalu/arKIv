# --- LLM Configuration ---
# IMPORTANT: Replace with your actual API key and endpoint.
# This is a placeholder and will not work without your credentials.
LLM_API_KEY = ""

# Example for a known provider (e.g., OpenAI-compatible):
LLM_API_ENDPOINT = "https://api.openai.com/v1/chat/completions"

# --- Prompt Configuration ---
# This prompt instructs the LLM to act as an expert in quantitative finance
# and extract specific entities from a research paper's abstract.
# The goal is to get a structured JSON output.
EXTRACTION_PROMPT_TEMPLATE = """
You are an expert AI assistant specializing in quantitative finance and academic research.
Your task is to extract specific entities from the abstract of a research paper, to create a knowledge graph.
Based on the provided abstract, identify and list the following:
1.  **Methodologies and Models**: Any specific models, algorithms, or techniques mentioned (e.g., GARCH, LSTM, Reinforcement Learning, Monte Carlo Simulation).
2.  **Datasets**: Any specific datasets used or mentioned (e.g., "S&P 500 historical data", "CRSP database"). If none are mentioned, return an empty list.
3.  **Research Topics**: The key topics or subdomains of the paper (e.g., "algorithmic trading", "risk management", "option pricing").

To ensure consistency, here is a list of topics already present in the knowledge graph. If the abstract discusses one of these topics, please use the existing name. If a new topic is discussed, feel free to add it.
**Existing Topics:**
---
{existing_topics}
---

Return the result as a single, clean and valid JSON object with the keys "methodologies", "datasets", and "topics".

**Abstract:**
---
{abstract}
---

**JSON Output:**
"""
