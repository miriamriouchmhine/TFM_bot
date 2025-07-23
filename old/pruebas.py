import chromadb
from sentence_transformers import SentenceTransformer
import torch 
from transformers import AutoTokenizer, AutoModel

# --- Cargar el modelo de embeddings (mismo que se usó para indexar) ---
# model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
device = "cuda" if torch.cuda.is_available() else "cpu"
model_name = "Alibaba-NLP/gte-multilingual-base"

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModel.from_pretrained(model_name, trust_remote_code=True).to(device)

def get_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512).to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    embeddings = outputs.last_hidden_state
    attention_mask = inputs["attention_mask"]
    mask_expanded = attention_mask.unsqueeze(-1).expand(embeddings.size()).float()
    summed = torch.sum(embeddings * mask_expanded, dim=1)
    counts = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
    mean_pooled = summed / counts
    return mean_pooled.squeeze().cpu().tolist()

# --- Conectar a la base de datos persistida ---
chroma_client = chromadb.PersistentClient(path="./chromadb")
collection = chroma_client.get_collection("reglamento_chunks")

# --- Introducir la pregunta ---
query = input("Pregunta: ").strip()

# --- Codificar la pregunta ---
# query_embedding = model.encode([query])
query_embedding = get_embedding(query)

# --- Consultar la colección ---
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=3
)

# --- Mostrar resultados ---
print("\nResultados más relevantes:\n")
for i, doc in enumerate(results["documents"][0]):
    print(f"🔹 Resultado {i+1}:\n{doc}\n")

# ¿Qué requisitos debe cumplir un material plástico para ser introducido en el mercado?