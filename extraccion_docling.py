from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
import os

PDF_FOLDER = "corpus"
PDFS_A_PROCESAR = [
    "L00001-00089-1-14.pdf",
    "L00001-00089-15-68.pdf",
    "L00001-00089-69-71.pdf",
    "L00001-00089-72-75.pdf",
    "L00001-00089-76-80.pdf",
    "L00001-00089-81-89.pdf"
]

pipeline_options = PdfPipelineOptions(do_table_structure=True)
pipeline_options.table_structure_options.do_cell_matching = False  
# pipeline_options.do_ocr = True


doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

for pdf_file in PDFS_A_PROCESAR:
    source = os.path.join(PDF_FOLDER, pdf_file)
    result = doc_converter.convert(source)

    # Guardar texto limpio en un archivo
    output_file = os.path.join(PDF_FOLDER, pdf_file.replace('.pdf', '_docling.txt'))
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result.document.export_to_markdown())
    
    print(f"[EXITO] Texto limpio guardado en '{output_file}'")