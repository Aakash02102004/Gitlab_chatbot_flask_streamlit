from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os

from dotenv import load_dotenv

# load variables from .env
load_dotenv()

emb = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=os.environ["GOOGLE_API_KEY"]
)

db = Chroma(
    collection_name="gitlab_handbook",
    persist_directory="./chroma_db",
    embedding_function=emb
)

print(db._collection.count())