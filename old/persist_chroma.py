import os
import pdfplumber
import camelot
import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

#Step 5: Chunk the combined text using RecursiveCharacterTextSplitter
with open("full_text.txt", "r", encoding="utf-8") as f:
    full_text = f.read()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
chunks = text_splitter.split_text(full_text)
print("Number of chunks generated:", len(chunks))

#Step 6: Generate embeddings using SentenceTransformers
embedder = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = embedder.encode(chunks, show_progress_bar=True)

#Step 7: Store embeddings in Chroma vector database
#Initialize Chroma (uses in-memory storage; for persistence, configure a persistent directory)
# os.makedirs("./data/chroma_db", exist_ok=True)
# os.environ["CHROMA_DB_IMPL"] = "duckdb+parquet"
# os.environ["PERSIST_DIRECTORY"] = "./data/chroma_db"

# client = chromadb.Client(persist_directory=os.environ["PERSIST_DIRECTORY"],
#                            chroma_db_impl=os.environ["CHROMA_DB_IMPL"])
chroma_client = chromadb.PersistentClient(path="./chromadb")
# client = chromadb.Client(persist_directory="./chroma_db", chroma_db_impl="duckdb+parquet")

#Add documents to the collection; each document is a chunk with its embedding
documents = chunks 
ids = [f"chunk_{i}" for i in range(len(chunks))]
metadatas = [{"chunk_index": i} for i in range(len(chunks))]  
collection = chroma_client.create_collection(name="pdf_embeddings")
collection.add(documents=documents, embeddings=embeddings.tolist(), ids=ids, metadatas=metadatas) 

#client.persist()
print(f"Stored {len(documents)} chunks in Chroma.")

#Step 8: Query the chroma DB
# def query_chroma(query_text, top_k=5): 
#     query_embedding = embedder.encode([query_text]).tolist()[0] 
#     results = collection.query(query_embeddings=[query_embedding], n_results=top_k) 
#     return results

#results = query_chroma("Que es el limte de migración para las sustancias?")
# print(results)