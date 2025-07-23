import re
import nltk
import uuid
import chromadb
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel
import torch
from nltk.tokenize import sent_tokenize

nltk.download("punkt_tab")

# --- Chunking personalizado ---
def sliding_window_chunks(text, max_chars=1050, overlap=170):
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = ""

    for sent in sentences:
        if len(current_chunk) + len(sent) + 1 <= max_chars:
            current_chunk += " " + sent
        else:
            chunks.append(current_chunk.strip())
            # Corte inteligente desde último punto hacia atrás
            overlap_part = current_chunk[-overlap:]
            current_chunk = overlap_part.strip() + " " + sent

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

# --- Leer archivo de texto ---
with open("corpus/L00001-00089_final.txt", "r", encoding="utf-8") as f:
    full_text = f.read()

# --- Crear chunks ---
chunks = sliding_window_chunks(full_text, max_chars=1000, overlap=150)
print(f"Total de chunks: {len(chunks)}")

# --- Embeddings con sentence-transformers ---
# model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
# embeddings = model.encode(chunks, show_progress_bar=True)
device = "cuda" if torch.cuda.is_available() else "cpu"
model_name = "Alibaba-NLP/gte-multilingual-base"

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModel.from_pretrained(model_name, trust_remote_code=True).to(device)

def get_embeddings(texts):
    all_embeddings = []
    for text in texts:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512).to(device)
        with torch.no_grad():
            outputs = model(**inputs)
        embeddings = outputs.last_hidden_state
        attention_mask = inputs["attention_mask"]
        mask_expanded = attention_mask.unsqueeze(-1).expand(embeddings.size()).float()
        summed = torch.sum(embeddings * mask_expanded, dim=1)
        counts = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
        mean_pooled = summed / counts
        all_embeddings.append(mean_pooled.squeeze().cpu().tolist())
    return all_embeddings

print("Generando embeddings...")
embeddings = get_embeddings(chunks)

# --- Inicializar Chroma DB ---
# client = chromadb.Client()
chroma_client = chromadb.PersistentClient(path="./chromadb")
collection = chroma_client.get_or_create_collection(name="reglamento_chunks")

# --- Añadir chunks a la colección ---
collection.add(
    documents=chunks,
    embeddings=embeddings,
    ids=[str(uuid.uuid4()) for _ in chunks],
    metadatas=[{"source": "L00001-00089_final.txt"}] * len(chunks)
)
# chroma_client.persist()

print("Chunks almacenados en Chroma correctamente.")
