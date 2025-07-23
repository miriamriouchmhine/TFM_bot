import ollama
import chromadb
from transformers import AutoTokenizer, AutoModel
import torch

# --- CONFIGURACIÓN ---
CHROMA_PATH = "./chromadb"
COLLECTION_NAME = "reglamento_chunks"
OLLAMA_MODEL = "llama3.2:1b"  # o "deepseek:1.5b"

# --- Conectar a Chroma ---
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_collection(name=COLLECTION_NAME)


device = "cuda" if torch.cuda.is_available() else "cpu"
model_name = "Alibaba-NLP/gte-multilingual-base"

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModel.from_pretrained(model_name, trust_remote_code=True).to(device)

def get_embedding(text: str):
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


# --- Iniciar cliente de Ollama ---
ollama_client = ollama.Client(host="http://localhost:11434")

# --- Loop interactivo ---
print("\n Escribe tu pregunta o 'salir':\n")

while True:
    query = input("Pregunta: ").strip()
    if query.lower() == "salir":
        break

    # 1. Codificar pregunta
    query_embedding = get_embedding(query)

    # 2. Recuperar chunks relevantes
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=4
    )
    retrieved_chunks = results["documents"][0]

    # 3. Construir contexto
    context = "\n\n".join(retrieved_chunks)

    # 4. Crear prompt para el modelo
    prompt = f"""Eres un asistente experto en regulación. Usa la siguiente información del reglamento para contestar con precisión y claridad.

{context}

Pregunta: {query}
Respuesta:"""

    # 5. Enviar a Ollama
    response = ollama_client.generate(
        model=OLLAMA_MODEL,
        prompt=prompt,
        stream=False
    )

    # 6. Mostrar respuesta
    print("\n Respuesta del modelo:")
    print(response["response"])
