# def convert_table_dict_to_sentences(table_dict):
#     """
#     Convierte la información de una tabla, representada como diccionario con dos claves:
#     'header' (lista de identificadores de columna) y 'rows' (lista de filas, donde la primera fila contiene los nombres de los campos),
#     en una cadena de texto en la que cada fila se transforma en una oración que asocia cada campo con su valor.
#     """
#     # Asumimos que la primera fila en 'rows' contiene los nombres de los campos (encabezados)
#     field_names = table_dict['rows'][0]
#     sentences = []

#     # Iteramos sobre cada fila de datos (a partir del índice 1)
#     for row in table_dict['rows'][1:]:
#         parts = []
#         for header, value in zip(field_names, row):
#             value_str = value.strip() if isinstance(value, str) else str(value)
#             header_str = header.strip() if isinstance(header, str) else str(header)
#             # Si el valor no está vacío, lo incluimos
#             if value_str:
#                 parts.append(f"{header_str} es {value_str}")
#         # Si encontramos algún dato en la fila, generamos una oración
#         if parts:
#             sentence = "La fila tiene: " + ", ".join(parts) + "."
#             sentences.append(sentence)

#     # Retornamos todas las oraciones, separadas por saltos de línea
#     return "\n".join(sentences)

# # Ejemplo de uso:
# table_data = {
#     'header': ['(1)', '(2)', '(3)', '(4)', '(5)', '(6)', '(7)', '(8)', '(9)', '(10)', '(11)'],
#     'rows': [
#         ['N° de sustancia para MCA', 'N° de ref.', 'N° CAS', 'Nombre de la sustancia', 'Uso como monómero, otro sustancia de auxiliar de polimerización (ti/no)', 'Uso como aditivo o auxiliar de polimerización (ti/no)', 'No se verificación de conformidad', 'FRF aplicable (si/no)', '(mg/kg)', ''],
#         ['1', '12310', '0266309-43-7', 'Albúmina', '', 'Si', 'No', '', '', ''],
#         ['2', '13340', '—', 'Albúmina coguguada por formulado hído', '', 'Si', 'No', '', '', ''],
#         ['3', '12375', '—', 'Monoalcoholes saturados lineales, primarios (C=C)', 'No', 'Si', 'No', '', '', '']
#         # Puedes incluir más filas según tu ejemplo
#     ]
# }

# result_text = convert_table_dict_to_sentences(table_data)
# print(result_text)

import json
import re  # Para limpieza avanzada del texto

def clean_text_to_dict(text):
    """
    Limpia el texto del archivo para convertirlo en un diccionario Python válido.
    """
    # Reemplazar comillas simples por dobles
    text = text.replace("'", '"')

    # Escapar apóstrofos dentro del texto (como en: "dimetilhexano y (60 % p/p)")
    text = re.sub(r'(\w)"(\w)', r'\1\'\2', text)

    # Corregir valores vacíos o espacios vacíos
    text = re.sub(r'(?<=[:,\[{])\s*""\s*(?=[,\]}])', 'null', text)

    # Corregir valores como 'ND' o similares sin comillas
    text = re.sub(r'(?<=[\[{,])\s*(ND)\s*(?=[,\]}])', r'"ND"', text)

    # Eliminar espacios en blanco innecesarios
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def convert_table_dict_to_sentences(table_dict):
    """
    Convierte la información de una tabla en un texto donde cada fila se describe en una oración.
    """
    print(table_dict)  # Para ver el contenido real que llega
    field_names = table_dict['rows'][0]
    sentences = []

    for row in table_dict['rows'][1:]:
        parts = []
        for header, value in zip(field_names, row):
            value_str = value.strip() if isinstance(value, str) else str(value)
            header_str = header.strip() if isinstance(header, str) else str(header)
            if value_str:
                parts.append(f"{header_str} es {value_str}")
        if parts:
            sentence = "La fila tiene: " + ", ".join(parts) + "."
            sentences.append(sentence)

    return "\n".join(sentences)

if __name__ == "__main__":
    # 1. Cargar el JSON
    with open("resultado.txt", "r", encoding="utf-8") as f:
        table_data_text = f.read()

    # 2. Limpiar el texto para corregir errores
    cleaned_text = clean_text_to_dict(table_data_text)

    # 3. Intentar convertir el texto limpio en un diccionario
    try:
        table_data = json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        print(f"❌ Error decodificando JSON: {e}")
        with open("resultado_error_log.txt", "w", encoding="utf-8") as f_err:
            f_err.write(cleaned_text)
        exit()

    # 4. Aplicar la función
    result_text = convert_table_dict_to_sentences(table_data)

    # 5. Guardar el resultado en un archivo de texto
    with open("resultado_tablas_oraciones.txt", "w", encoding="utf-8") as f_out:
        f_out.write(result_text)

    print("✅ Proceso completado correctamente.")
