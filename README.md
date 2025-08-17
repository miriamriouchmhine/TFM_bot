# TFM_bot

# Instrucciones de uso del proyecto RAG + Ollama

Este documento explica cómo ejecutar y probar el proyecto de recuperación aumentada por generación (RAG) usando modelos locales con Ollama.

## 1. Iniciar el entorno Docker

Abre una terminal (cmd o PowerShell) y sigue estos pasos:

```bash
cd ruta/del/proyecto
docker compose up
```

Esto levantará el contenedor de Docker con el entorno necesario.

## 2. Acceder al contenedor Ollama

En otra terminal (cmd o PowerShell), ejecuta el siguiente comando para entrar dentro del contenedor:

```bash
docker exec -it ollama-container bash
```

## 3. Ver y gestionar los modelos en Ollama

Dentro del contenedor, puedes listar los modelos descargados con:

```bash
ollama list
```

Si no tienes ningún modelo, puedes descargarlos con:

```bash
ollama pull deepseek-r1:1.5b
ollama pull llama3.2:1b
```

Para eliminar un modelo:

```bash
ollama rm nombre-del-modelo
```

> 💡 Una vez llegues a este punto, el entorno en Docker ya está configurado.

## 4. Preprocesamiento de PDFs

En el corpus ya están preprocesados los PDFs. El código relacionado con esta parte está en:

- `extracción_docling.py`: convierte el contenido de los PDFs a texto plano.
- `table_to_text.py`: transforma tablas en oraciones con sentido.

## 5. Persistencia de embeddings en la base de datos

Ejecuta el siguiente script para guardar los embeddings en la base de datos Chroma:

```bash
python persist_chroma.py
```

## 6. Probar el sistema RAG

Para probar el sistema por línea de comandos:

```bash
python rag_query.py
```

## 7. Si se quiere ejecutar la aplicación web con Streamlit

Si quieres probar la interfaz visual, ejecuta:

```bash
streamlit run app.py
```

---

⚠️ **Nota:**  
Este código está sujeto a cambios y mejoras. Es una primera versión provisional mientras se avanza en la redacción de la memoria del proyecto.
