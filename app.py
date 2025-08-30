import streamlit as st
import ollama
import chromadb
from transformers import AutoTokenizer, AutoModel
import torch
import time

st.set_page_config(
    page_title="Asistente Reglamento UE 10/2011",
    page_icon="imagenes/icono.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  .block-container{max-width:920px;padding-top:1rem}
  /* burbujas de chat un poco más 'card' */
  [data-testid="chat-message"] {border-radius:16px; box-shadow:0 1px 4px rgba(0,0,0,.06)}
  /* botón ancho en sidebar */
  .sidebar .stButton button {width:100%}
  .app-title{
    font-size:2.2rem; margin:0 0 .25rem 0; font-weight:800; letter-spacing:.2px; line-height:1.1;
    background:linear-gradient(90deg,#4f46e5,#06b6d4); -webkit-background-clip:text; color:transparent;
  }
  .app-subtitle{ color:#6b7280; margin:0 0 1rem 0 }
  .header{
    margin: 6px 0 22px;
    text-align: center;
  }
  .header .app-title{
    margin: 0;
    font-size: clamp(28px, 4.4vw, 52px);
    font-weight: 900;
    letter-spacing: .3px;
    line-height: 1.05;
    background: linear-gradient(90deg,#4f46e5 0%, #06b6d4 55%, #22c55e 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent !important;               /* fuerza el gradiente */
    -webkit-text-fill-color: transparent !important;
  }
  .header .subtitle{
    color: var(--text-color);
    opacity: .7;
    margin: .4rem 0 0;
    font-size: 0.98rem;
  }
  .header .accent{
    height: 6px; width: 120px; margin: 10px auto 0; border-radius: 999px;
    background: linear-gradient(90deg,#4f46e5,#06b6d4,#22c55e);
    filter: blur(.2px);
  }
  .badges{ display:flex; gap:.5rem; justify-content:center; margin-top:.75rem; flex-wrap:wrap }
  .badge{ font-size:.75rem; padding:.3rem .6rem; border-radius:999px; background:rgba(15,23,42,.06); border:1px solid rgba(148,163,184,.25) }
/* --- Botón "Nueva conversación" en la sidebar --- */
[data-testid="stSidebar"] .stButton > button{
  width:100%;
  border:0 !important;
  border-radius:999px;
  padding:.65rem 1rem;
  font-weight:700;
  letter-spacing:.2px;
  color:#fff !important;
  background-image:linear-gradient(90deg,#4f46e5 0%, #06b6d4 50%, #22c55e 100%) !important;
  background-size:200% 100% !important;
  box-shadow:0 6px 18px rgba(79,70,229,.25), inset 0 0 0 1px rgba(255,255,255,.15);
  transition:background-position .25s ease, transform .06s ease, box-shadow .2s ease, filter .2s ease;
}
[data-testid="stSidebar"] .stButton > button:hover{
  background-position:100% 0 !important;
  filter:brightness(1.02);
}
[data-testid="stSidebar"] .stButton > button:active{
  transform:translateY(1px);
  box-shadow:0 3px 10px rgba(79,70,229,.25), inset 0 0 0 1px rgba(255,255,255,.12);
}
[data-testid="stSidebar"] .stButton > button:focus-visible{
  outline:3px solid rgba(6,182,212,.35);
  outline-offset:2px;
}
</style>
""", unsafe_allow_html=True)


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

st.markdown("""
<div class="header">
  <h1 class="app-title">Reglamento (UE) 10/2011 · Asistente RAG</h1>
  <div class="accent"></div>
  <p class="subtitle">Consulta guiada con recuperación aumentada sobre materiales plásticos en contacto con alimentos.</p>
  <div class="badges">
    <span class="badge">Docling</span>
    <span class="badge">Chroma</span>
    <span class="badge">Ollama · LLaMA&nbsp;3.2</span>
  </div>
</div>
""", unsafe_allow_html=True)
if "selected_model" not in st.session_state:
    st.session_state.selected_model = OLLAMA_MODEL  # tu valor por defecto

with st.sidebar:
    st.subheader("Modelo LLM")
    labels = list(MODEL_CHOICES.keys())
    values = list(MODEL_CHOICES.values())
    
    try:
        default_idx = values.index(st.session_state.selected_model)
    except ValueError:
        default_idx = 0
    label = st.selectbox("Selecciona el modelo", labels, index=default_idx)
    st.session_state.selected_model = MODEL_CHOICES[label]
    st.session_state.selected_model_label = label
    st.caption(f"Usando: `{st.session_state.selected_model}`")

    # --- Nueva conversación ---
    if st.button("Nueva conversación", type="primary", key="new_chat"):
        st.session_state.history = []
        st.session_state.query = ""
        st.rerun()

    # --- Footer (sidebar) ---
    st.caption("Versión app v0.3 · Índice: 2025-08-13 · Contacto: x@alu.ua.com")

if "history" not in st.session_state:
    st.session_state.history = []

if "query" not in st.session_state:
    st.session_state.query = ""

def generate_response():
    t0 = time.perf_counter()
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
        n_chunks = len(retrieved_chunks)
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
        lat_ms = round((time.perf_counter() - t0) * 1000)
        elapsed_time = time.time() - start_time
        print(f"Tiempo para generar la respuesta con Ollama: {elapsed_time:.4f} segundos")
        st.session_state.history.append({
            "query": query,
            "answer": answer,
            "model_tag": chosen_model,
            "model_label": chosen_label,
            "lat_ms": lat_ms,                   
            "n_chunks": n_chunks
        })

    # Limpio el input para que quede vacío
    st.session_state.query = ""

# Input con on_change para que se llame al enviar texto
# st.text_input("Escribe tu pregunta y pulsa Enter:", key="query", on_change=generate_response)

# # Mostrar historial
# for chat_turn in st.session_state.history:
#     shown_label = chat_turn.get("model_label") or chat_turn.get("model_tag") or "modelo"
#     st.markdown(f"**Tú:** {chat_turn['query']}")
#     st.markdown(f"**Bot — {shown_label}:** {chat_turn['answer']}")
# Render del historial en burbujas
for turn in st.session_state.get("history", []):
    with st.chat_message("user", avatar="👤"):
        st.markdown(turn["query"])

    shown_label = turn.get("model_label") or turn.get("model_tag") or "modelo"
    with st.chat_message("assistant", avatar="🤖"):
        badges = f"**Modelo:** {shown_label} · **Latencia:** {turn.get('lat_ms','—')} ms · **#Chunks:** {turn.get('n_chunks','—')}"
        st.caption(badges)
        st.markdown(turn["answer"])

# Input de chat
if prompt := st.chat_input("Escribe tu pregunta y pulsa Enter:"):
    st.session_state.query = prompt
    generate_response()
    st.rerun()