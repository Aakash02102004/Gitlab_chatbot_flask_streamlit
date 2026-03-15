import os
import time
from langchain_google_genai import GoogleGenerativeAIEmbeddings


from dotenv import load_dotenv

# load variables from .env
load_dotenv()

api_key = os.environ.get("GOOGLE_API_KEY")

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=api_key
)

test_text = "A" * 10000   # simulate huge chunk

print("Sending embedding request...")

start = time.time()

vector = embeddings.embed_query(test_text)

end = time.time()

print("\nEmbedding length:", len(vector))
print("Response time:", end - start, "seconds")

size_bytes = len(vector) * 8
print(vector)
print("Approx memory used:", size_bytes / 1024, "KB")