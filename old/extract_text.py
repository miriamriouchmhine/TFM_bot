import pdfplumber
import os

# Ruta al archivo PDF dentro de la carpeta 'corpus'
pdf_path = os.path.join("corpus", "L00001-00089-1.pdf")
# Ruta del archivo de salida
output_txt_path = os.path.join("corpus", "L00001-00089-1_texto_extraido.txt")

# Función para extraer texto
def extract_text_from_pdf(pdf_path, output_path):
    all_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                all_text += f"\n--- Página {i + 1} ---\n{text}"
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(all_text)

    print(f"Texto extraído y guardado en: {output_path}")

# Ejecutar la función
extract_text_from_pdf(pdf_path, output_txt_path)
