import os
import pdfplumber
import camelot
import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

#Step 1: Extract narrative text from PDF using pdfplumber
def extract_text(pdf_path):
    all_text = "" 
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    all_text += text + "\n"
    finally:
        pdf.close()
    return all_text

#Step 2: Extract tables from pdf using Camelot
#Lattice tiene bordes, si no tuviese stream
def extract_tables(pdf_path):
    tables = camelot.read_pdf(pdf_path, pages='all', flavor='lattice') 
    return tables

#Step 3: Process tables into text
def tables_to_text(tables):
    table_texts = []
    for i, table in enumerate(tables):
        df = table.df

        # The first row is field names (headers)
        field_names = df.iloc[0].tolist()

        # The rest are data rows
        data_rows = df.iloc[1:]

        lines = [f"Table {i+1}:"]
        # Iterate over each data row
        for row_index, row in data_rows.iterrows():
            # row is a Series of cell values
            lines.append(f"Row {row_index}:")
            for col_index, cell_value in enumerate(row):
                field_label = field_names[col_index]
                # Format them, e.g. " - (1): 12310"
                lines.append(f" - {field_label.strip()}: {cell_value.strip() if isinstance(cell_value, str) else cell_value}")
            lines.append("")  # blank line to separate rows

        table_text = "\n".join(lines)
        table_texts.append(table_text)

    # Combine all tables with a blank line between them
    return "\n\n".join(table_texts)
    # table_texts = []
    # for i, table in enumerate(tables):
    #     #Convert each table (pandas DataFrame) to a csv formatted string
    #     csv_str = table.df.to_csv(index = False)
    #     table_text = f"Table {i+1}:\n{csv_str}" #opcional
    #     table_texts.append(table_text) 
    # return "\n".join(table_texts)

def tables_to_text_(tables):
    table_texts = []
    for table in tables:
        df = table.df
        # Convertir el DataFrame a string sin índices
        plain_table = df.to_string(index=False)
        table_texts.append(plain_table)
    return "\n\n".join(table_texts)
#Step 4: Narrative text and table text
pdf_path = "L00001-00089-1.pdf"
narrative_text = extract_text(pdf_path)

tables = extract_tables(pdf_path)
table_text = tables_to_text_(tables)

#Combine both texts
full_text = narrative_text + "\n\n" + table_text
with open("full_text_tables.txt", "w", encoding="utf-8") as f:
    f.write(full_text)

print("Total extracted text length:", len(full_text))


