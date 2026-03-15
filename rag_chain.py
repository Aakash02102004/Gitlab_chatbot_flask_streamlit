import os
import torch
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from sentence_transformers import SentenceTransformer
from langchain_core.embeddings import Embeddings
from langchain_core.output_parsers import StrOutputParser
from guardrails import run_guardrails

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LocalEmbedding(Embeddings):
    """
    Local embedding class initializing the 'bge' (BAAI/bge-small-en-v1.5) embedding model 
    as used in vector_db_builder.py.
    """
    def __init__(self, model_name="BAAI/bge-small-en-v1.5"):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(model_name, device=device)

    def embed_documents(self, texts):
        return self.model.encode(
            texts,
            batch_size=512,
            show_progress_bar=False,
            convert_to_numpy=True
        ).tolist()

    def embed_query(self, text):
        return self.model.encode([text])[0].tolist()

def initialize_rag():
    """
    Initializes the RAG chain components.
    """
    # 1) Load the existing ChromaDB vector store using the bge embedding model
    # Matching the model and persist directory from vector_db_builder.py
    embeddings = LocalEmbedding()
    vectorstore = Chroma(
        collection_name="gitlab_handbook",
        persist_directory="./chroma_db",
        embedding_function=embeddings
    )
    


    # 2) Connect to the Gemini-1.5-Flash model
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3
    )

    # 3) Create a prompt template instructing the AI to be a 'GitLab Culture Expert'
    template = """You are **GitLab Handbook Assistant**, an expert on GitLab's culture, policies, and processes.

    Your task is to answer the user's question **ONLY using the provided context from the GitLab Handbook**.

    ## Rules

    1. Use ONLY the information present in the provided context.
    2. If the context does not contain the answer, respond exactly with:
    "I cannot find the answer in the GitLab handbook context provided."
    3. Do NOT use outside knowledge or make assumptions.
    4. If multiple relevant pieces of context exist, synthesize them into a clear answer.
    5. Keep the answer concise, factual, and grounded in the context.
    6. If helpful, include bullet points for clarity.
    7. When referencing information, cite the relevant section or source if available.

    ## Context

    {context}

    ## User Question

    {question}

    ## Instructions for Answer

    * Read the context carefully before answering.
    * Extract the most relevant information.
    * Provide a clear and structured response.
    * Avoid repeating the context verbatim unless necessary.

    ## Answer
    """
    
    prompt = PromptTemplate.from_template(template)
    
    return vectorstore, prompt, llm

# Initialize components
vectorstore, prompt, llm = initialize_rag()

def ask_handbook(query: str) -> dict:
    """
    4) Function that takes a query, runs the RAG chain, and returns the answer AND the source URLs used.
    """

    # Run guardrails
    guardrails_result = run_guardrails(query, llm)
    if not guardrails_result.passed:
        print(f"[guardrails] Guardrail failed: {guardrails_result.reason}")
        return {
            "answer": f"Query blocked by guardrails: {guardrails_result.reason}",
            "sources": []
        }
    
    # Retrieve relevant documents
    K = int(os.environ.get("K", 5))
    docs = vectorstore.similarity_search(query, k=K)
    print(docs)
    
    # Format context
    context = "\n\n".join(doc.page_content for doc in docs)
    
    # Run LLM prediction
    chain = prompt | llm | StrOutputParser()
    print(chain)
    answer = chain.invoke({"context": context, "question": query})
    
    # Extract source URLs from document metadata
    sources = set()
    for doc in docs:
        if "url" in doc.metadata:
            sources.add(doc.metadata["url"])
        elif "source" in doc.metadata:
            sources.add(doc.metadata["source"])
    
    print(answer, sources)
    return {
        "answer": answer,
        "sources": list(sources)
    }

if __name__ == "__main__":
    # Example usage test
    query = "What is the GitLab core value?"
    print(f"Query: {query}\n")
    result = ask_handbook(query)
    print("Answer:")
    print(result["answer"])
    print("\nSource URLs used:")
    for url in result["sources"]:
        print(f" - {url}")
