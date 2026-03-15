from langchain_chroma import Chroma
from sentence_transformers import SentenceTransformer
from langchain_core.embeddings import Embeddings
import torch

class LocalEmbedding(Embeddings):
    def __init__(self, model_name="BAAI/bge-small-en-v1.5"):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(model_name, device=device)

    def embed_documents(self, texts):
        return self.model.encode(texts).tolist()

    def embed_query(self, text):
        return self.model.encode([text])[0].tolist()


embeddings = LocalEmbedding()

vectorstore = Chroma(
    collection_name="gitlab_handbook",
    persist_directory="./chroma_db",
    embedding_function=embeddings
)

print(vectorstore._collection.count())