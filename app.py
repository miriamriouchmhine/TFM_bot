import streamlit as st
import ollama
import chromadb
from transformers import AutoTokenizer, AutoModel
import torch
import time

# --- Modelos disponibles en Ollama (tags) ---
MODEL_CHOICES = {
    "LLaMA 3.2 (1B)": "llama3.2:1b",
    "DeepSeek R1 (1.5B)": "deepseek-r1:1.5b",
    "Gemma 3 (1B)": "gemma3:1b",
    "Qwen 2.5 (1.5B Instruct)": "qwen2.5:1.5b",
    "Qwen 3 (1.7B)": "qwen3:1.7b",
}

# --- Config ---
CHROMA_PATH = "./chromadb"
COLLECTION_NAME = "reglamento_chunks"
OLLAMA_MODEL = "llama3.2:1b" # o "deepseek-r1:1.5b" 

@st.cache_resource(show_spinner=False)
def load_resources():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained("Alibaba-NLP/gte-multilingual-base", trust_remote_code=True)
    model = AutoModel.from_pretrained("Alibaba-NLP/gte-multilingual-base", trust_remote_code=True).to(device)
    model.eval()
    if device == "cuda":
        model = model.half()

    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma_client.get_collection(name=COLLECTION_NAME)
    ollama_client = ollama.Client(host="http://localhost:11434")
    return device, tokenizer, model, collection, ollama_client

device, tokenizer, model, collection, ollama_client = load_resources()

def get_embedding(text):
    start_time = time.time()  # Marcar el inicio
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512).to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    embeddings = outputs.last_hidden_state
    attention_mask = inputs["attention_mask"]
    mask_expanded = attention_mask.unsqueeze(-1).expand(embeddings.size()).float()
    summed = torch.sum(embeddings * mask_expanded, dim=1)
    counts = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
    mean_pooled = summed / counts
    elapsed_time = time.time() - start_time  # Medir el tiempo transcurrido
    print(f"Tiempo para obtener embedding: {elapsed_time:.4f} segundos")  # Imprimir el tiempo
    return mean_pooled.squeeze().cpu().tolist()

st.title("Chat")
if "selected_model" not in st.session_state:
    st.session_state.selected_model = OLLAMA_MODEL  # tu valor por defecto

with st.sidebar:
    st.subheader("Modelo LLM")
    labels = list(MODEL_CHOICES.keys())
    values = list(MODEL_CHOICES.values())
    # intenta preseleccionar el que ya tengas en OLLAMA_MODEL
    try:
        default_idx = values.index(st.session_state.selected_model)
    except ValueError:
        default_idx = 0
    label = st.selectbox("Selecciona el modelo", labels, index=default_idx)
    st.session_state.selected_model = MODEL_CHOICES[label]
    st.session_state.selected_model_label = label
    st.caption(f"Usando: `{st.session_state.selected_model}`")

if "history" not in st.session_state:
    st.session_state.history = []

if "query" not in st.session_state:
    st.session_state.query = ""

def generate_response():
    query = st.session_state.query.strip()
    if not query:
        return

    # Modelo “congelado” para ESTE turno
    chosen_model = st.session_state.get("selected_model", OLLAMA_MODEL)
    # Resuelve el label aunque no exista en session_state (compat. hacia atrás)
    chosen_label = st.session_state.get(
        "selected_model_label",
        next((k for k, v in MODEL_CHOICES.items() if v == chosen_model), chosen_model)
    )

    with st.spinner("Buscando información y generando respuesta..."):
        # Trazas para el tiempo de obtención de embeddings
        start_time = time.time()
        query_embedding = get_embedding(query)
        elapsed_time = time.time() - start_time
        print(f"Tiempo para obtener embedding de la consulta: {elapsed_time:.4f} segundos")

        # Trazas para la consulta a ChromaDB
        start_time = time.time()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=4
        )
        retrieved_chunks = results["documents"][0]
        elapsed_time = time.time() - start_time
        print(f"Tiempo para obtener resultados de ChromaDB: {elapsed_time:.4f} segundos")

        # Trazas para la preparación del prompt
        start_time = time.time()
        context = "\n\n".join(retrieved_chunks)

        prompt = f"""Eres un asistente experto en regulación. Usa la siguiente información del reglamento para contestar con precisión y claridad. 

{context}

Pregunta: {query}
Respuesta:"""
        
        elapsed_time = time.time() - start_time
        print(f"Tiempo para generar el prompt: {elapsed_time:.4f} segundos")
        
        # Trazas para la generación de respuesta por parte de Ollama
        start_time = time.time()
        response = ollama_client.generate(
            model=chosen_model,
            prompt=prompt,
            stream=False,
            options={
                "temperature": 0.2, 
                "top_p": 0.9, 
                "num_predict": 512
                }
        )
        print("model_",model)
        answer = response["response"]
        elapsed_time = time.time() - start_time
        print(f"Tiempo para generar la respuesta con Ollama: {elapsed_time:.4f} segundos")
        st.session_state.history.append({
            "query": query,
            "answer": answer,
            "model_tag": chosen_model,
            "model_label": chosen_label,
        })

    # Limpio el input para que quede vacío
    st.session_state.query = ""

# Input con on_change para que se llame al enviar texto
st.text_input("Escribe tu pregunta y pulsa Enter:", key="query", on_change=generate_response)

# Mostrar historial
for chat_turn in st.session_state.history:
    shown_label = chat_turn.get("model_label") or chat_turn.get("model_tag") or "modelo"
    st.markdown(f"**Tú:** {chat_turn['query']}")
    st.markdown(f"**Bot — {shown_label}:** {chat_turn['answer']}")
