import os
import json
import faiss
import networkx as nx
import numpy as np
import openai
from sentence_transformers import SentenceTransformer

# Import configuration from config.py
from config import LLM_API_KEY, LLM_API_ENDPOINT

client = openai.OpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_API_ENDPOINT.rsplit('/', 1)[0] # e.g., "https://api.openai.com/v1"
)

# --- Configuration ---
VECTOR_STORE_PATH = "vector_store.index"
TEXT_METADATA_PATH = "metadata.json" # From data_extractor.py
GRAPH_PATH = "knowledge_graph.gexf"
MODEL_NAME = 'all-MiniLM-L6-v2'

# --- Prompt Templates ---

ROUTER_PROMPT_TEMPLATE = """
Based on the user's question, decide the best way to answer it using the available tools.
You have two tools:
1. "vector_search": Searches over Vector Embeddings of chunks of text. Good for general questions about concepts, summaries, or "what is" style questions. Use this for broad, semantic searches.
2. "graph_search": Searches over a structured Knowledge Graph. Good for specific questions about relationships between entities like authors, papers, topics, or methodologies. Use this for "who worked on X", "what methods are used for Y", "list papers by Z" style questions.

User question: "{question}"

Which tool is most appropriate? Respond with only "vector_search" or "graph_search".
"""

FINAL_ANSWER_PROMPT_TEMPLATE = """
Based on the following context, please provide a comprehensive answer to the user's question.
If the context is empty or not relevant, say that you could not find a specific answer in the knowledge base.

Context:
---
{context}
---

User Question: {question}

Answer:
"""

class QASystem:
    def __init__(self):
        print("Initializing QA System...")
        if not all(os.path.exists(p) for p in [VECTOR_STORE_PATH, TEXT_METADATA_PATH, GRAPH_PATH]):
            raise FileNotFoundError("Ensure all data files (vector_store.index, metadata.json, knowledge_graph.gexf) are present.")
        
        print("Loading Sentence Transformer model...")
        self.model = SentenceTransformer(MODEL_NAME)
        
        print("Loading FAISS index...")
        self.index = faiss.read_index(VECTOR_STORE_PATH)
        
        print("Loading text metadata...")
        with open(TEXT_METADATA_PATH, 'r') as f:
            self.text_metadata = json.load(f)
            
        print("Loading knowledge graph...")
        self.graph = nx.read_gexf(GRAPH_PATH)
        print("QA System ready.\n")

    def _call_llm(self, prompt, model="o3-mini"):
        if not LLM_API_KEY:
            print("LLM_API_KEY not found. Please check your api.key file.")
            return None

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except openai.APIStatusError as e:
            print(f"Error calling LLM API: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    def route_query(self, question):
        prompt = ROUTER_PROMPT_TEMPLATE.format(question=question)
        router_result = self._call_llm(prompt)
        if router_result and "graph_search" in router_result:
            return "graph_search"
        return "vector_search"

    def search_vector_store(self, query, k=5):
        print("Performing vector search...")
        query_embedding = self.model.encode([query]).astype('float32')
        _, I = self.index.search(query_embedding, k)
        
        results = []
        for i in I[0]:
            if i != -1: # FAISS returns -1 for no result
                chunk_info = self.text_metadata.get(str(i))
                if chunk_info:
                    results.append(f"From paper {chunk_info['paper_id']}:\n...{chunk_info['chunk_id']}...")
        return "\n\n".join(results)

    def search_knowledge_graph(self, question):
        print("Performing knowledge graph search...")
        # A more advanced version would translate the question to a Cypher query.
        # For now, we'll extract entities and find their connections.
        extraction_prompt = f"From the following question, extract the key entities (like author names, paper titles, methodologies, or topics). Return them as a JSON list. Question: {question}"
        
        entities_str = self._call_llm(extraction_prompt)
        try:
            entities = json.loads(entities_str)
        except:
            print(" - Could not parse entities from LLM response.")
            return "Could not identify specific entities in the question for graph search."

        if not entities:
            return "No specific entities found in the question to search the graph."

        print(f" - Found entities: {entities}")
        context = []
        for entity in entities:
            # Find nodes that match the entity
            matching_nodes = [n for n, d in self.graph.nodes(data=True) if entity.lower() in d.get('label', '').lower()]
            for node in matching_nodes:
                node_type = self.graph.nodes[node].get('type', 'Unknown')
                context.append(f"Found Node: {self.graph.nodes[node].get('label')} (Type: {node_type})")
                # Find its neighbors
                for neighbor in self.graph.neighbors(node):
                    neighbor_label = self.graph.nodes[neighbor].get('label')
                    neighbor_type = self.graph.nodes[neighbor].get('type', 'Unknown')
                    context.append(f"  - Is connected to: {neighbor_label} (Type: {neighbor_type})")
        
        return "\n".join(context) if context else f"Could not find any information about {', '.join(entities)} in the knowledge graph."

    def answer_question(self, question):
        print(f"--- New Question ---")
        print(f"User: {question}")
        
        tool_choice = self.route_query(question)
        print(f"Routing decision: {tool_choice}")
        
        context = ""
        if tool_choice == "vector_search":
            context = self.search_vector_store(question)
        elif tool_choice == "graph_search":
            context = self.search_knowledge_graph(question)
            
        if not context:
            print("Could not retrieve any context.")
            return "I'm sorry, I could not find any relevant information in my knowledge base to answer that question."

        print("\nSynthesizing final answer...")
        final_prompt = FINAL_ANSWER_PROMPT_TEMPLATE.format(context=context, question=question)
        final_answer = self._call_llm(final_prompt, model="o3") # Use a more capable model for final answer
        
        print(f"\nFinal Answer: {final_answer}")
        return final_answer


if __name__ == '__main__':
    qa = QASystem()

    # --- Example Questions ---
    
    # This question is broad and semantic, so it should be routed to vector_search
    qa.answer_question("What are the common approaches to modeling market volatility?")

    # This question is specific and relational, so it should be routed to graph_search
    qa.answer_question("Which authors have published papers on GARCH models?")
    
    # Another vector search example
    qa.answer_question("Explain reinforcement learning in the context of financial trading.")

    # Another graph search example
    qa.answer_question("List papers related to the topic of Algorithmic Trading.")