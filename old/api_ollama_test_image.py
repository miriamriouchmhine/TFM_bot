import ollama
from PIL import Image
import io
import sys


def query_model_with_image(image_path):
    client = ollama.Client("http://localhost:11434")

    response = client.generate(
        model="granite3.2-vision",
        prompt="Analiza esta tabla",
        system="""Eres experto en extraer texto de tablas y convertir cada una de las filas en una oración.""",
        images=[image_path]
    )
    print(response.response)
    return response.response
    

if __name__ == "__main__":
    image_path = r"C:\Users\miria\Documents\TFM_bot\image_table.png"
    
    result_text = query_model_with_image(image_path)

    with open("resultado.txt", "w", encoding="utf-8") as f:
        f.write(result_text.strip())