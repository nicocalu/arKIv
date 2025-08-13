import os

def load_api_key():
    """Loads the API key from a file named 'api.key' in the root directory."""
    try:
        with open("api.key", "r") as f:
            key = f.read().strip()
            if not key:
                raise ValueError("API key file is empty.")
            return key
    except FileNotFoundError:
        print("ERROR: API key file 'api.key' not found.")
        print("Please create this file in the root directory and paste your API key into it.")
        return None
    except Exception as e:
        print(f"An error occurred while reading the API key: {e}")
        return None

# The API key is now loaded securely from the 'api.key' file.
LLM_API_KEY = load_api_key()


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
