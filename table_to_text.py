import re
import os
from pathlib import Path

def procesar_tabla1(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as file:
        lines = file.readlines()

    data_lines = [line for line in lines if re.match(r"\|\s*\d+\s*\|", line)]
    def fila_a_oracion_tabla1(fila):
        campos = [campo.strip() for campo in fila.strip().strip('|').split('|')]
        if len(campos) == 12:
            campos = campos[:11]
        if len(campos) != 11:
            return None
        n_mca, ref, cas, nombre, uso_aditivo, uso_monomero, frf, lme, lme_t, restricciones, notas = campos

        oracion = (
            f"La sustancia número {n_mca}, identificada con el número de referencia {ref}"
            f"{f' y número CAS {cas}' if cas != '-' else ''}, es {nombre}."
            f" {'Está' if uso_aditivo.lower() == 'sí' else 'No está'} autorizada como aditivo o auxiliar para la producción de polímeros."
            f" {'Está' if uso_monomero.lower() == 'sí' else 'No está'} autorizada como monómero u otra sustancia de partida."
            f" {'Se aplica' if frf.lower() == 'sí' else 'No se aplica'} el FRF."
        )

        if lme and lme != "ND":
            oracion += f" Tiene un límite de migración específica de {lme} mg/kg."
        elif lme == "ND":
            oracion += " No debe migrar en cantidades detectables (ND)."

        if lme_t:
            oracion += f" Se aplica una restricción de grupo identificada como {lme_t}."

        if restricciones:
            oracion += f" Restricciones adicionales: {restricciones}."

        if notas:
            oracion += f" Nota sobre la verificación de conformidad: {notas}."

        return oracion

    # Generar oraciones
    oraciones = [fila_a_oracion_tabla1(fila) for fila in data_lines if fila_a_oracion_tabla1(fila)]

    # Guardar resultado en archivo .txt
    with open(output_file, "w", encoding="utf-8") as f:
        for oracion in oraciones:
            f.write(oracion + "\n\n")

    print(f"{len(oraciones)} oraciones generadas para {input_file} y guardadas en {output_file}")

def procesar_tabla2(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as file:
        lines = file.readlines()

    tabla_lines = [line for line in lines if re.match(r"\|\s*\d+\s*\|", line)]

    def fila_a_oracion_tabla2(fila):
        campos = [campo.strip() for campo in fila.strip().strip('|').split('|')]
        if len(campos) != 4:
            return None
        id_grupo, sustancias, lme, especificacion = campos
        return (
            f"El grupo de restricción número {id_grupo} se aplica a las sustancias {sustancias}."
            f" El límite de migración total (LME) es de {lme} mg/kg. {especificacion}."
        )

    oraciones = [fila_a_oracion_tabla2(fila) for fila in tabla_lines if fila_a_oracion_tabla2(fila)]

    # Guardar el texto original más las oraciones al final
    with open(output_file, "w", encoding="utf-8") as f:
        for line in lines:
            if line not in tabla_lines:
                f.write(line)
        f.write("\n\n# Oraciones generadas a partir de las tablas:\n\n")
        for oracion in oraciones:
            f.write(oracion + "\n\n")

    print(f"{len(oraciones)} oraciones generadas para {input_file} y guardadas en {output_file}")

def procesar_tabla_3(lines):
    oraciones = []
    for line in lines:
        match = re.match(r"\|\s*\(?(\d+)\)?\s*\|\s*(.*?)\s*\|", line)
        if match:
            numero = match.group(1)
            texto = match.group(2).replace('\xa0', ' ')
            oraciones.append(f"La nota número {numero} indica: {texto}")
    return oraciones

def procesar_tabla_4(lines):
    nombre = None
    especificaciones = []

    for line in lines:
        if not line.startswith("|"):
            continue

        celdas = [c.strip().replace("\xa0", " ") for c in line.strip().split("|")]
        if len(celdas) < 3:
            continue

        campo = celdas[2]
        valor = celdas[3]

        # Saltar encabezados y separadores
        if not campo or not valor or campo in ["N o  de sustancia  para MCA", "Especificación detallada de la sustancia"]:
            continue
        if "---" in campo or campo in ["(2)", "(2)"]:
            continue

        if campo == "Nombre químico":
            nombre = valor
        else:
            especificaciones.append(f"{campo.lower()} es {valor}")

    nombre_txt = f", su nombre químico es {nombre}" if nombre else ""
    intro = f"La sustancia para MCA 744{nombre_txt}"
    cuerpo = ", ".join(especificaciones)
    return intro + ", " + cuerpo + "."

def procesar_tabla_simulantes(lines):
    oraciones = []
    carbono = []
    porcentaje = []

    for line in lines:
        if not line.startswith("|") or "---" in line:
            continue

        celdas = [c.strip().replace("\xa0", " ") for c in line.strip().split("|")]
        if len(celdas) >= 3 and "simulante alimentario" in celdas[3].lower():
            nombre = celdas[1]
            clasificacion = celdas[3]
            oraciones.append(f"El simulante '{nombre}' se clasifica como {clasificacion}.")

        if "de átomos de carbono" in line.lower():
            carbono = [c.strip() for c in celdas[1:] if c.strip()]
        elif "gama" in line.lower() and "composición" in line.lower():
            porcentaje = [c.strip() for c in celdas[1:] if c.strip()]

    if carbono and porcentaje and len(carbono) == len(porcentaje):
        for c, p in zip(carbono, porcentaje):
            oraciones.append(
                f"Cuando el número de átomos de carbono en la cadena de ácidos grasos: número de insaturación es {c}, la gama de composición de los ácidos grasos expresada en % (w/w) de ésteres metílicos por cromatografía de gases es {p} %."
            )

    return oraciones

def generar_oraciones_tablas_doc4(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    output_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Detectar inicio de Cuadro 3
        if "## 3. Notas sobre la verificación de la conformidad" in line:
            output_lines.append(line)
            i += 1
            tabla_3_block = []
            while i < len(lines) and not lines[i].startswith("## 4."):
                tabla_3_block.append(lines[i])
                i += 1
            oraciones_3 = procesar_tabla_3(tabla_3_block)
            output_lines.extend([o + "\n" for o in oraciones_3])
            continue

        # Detectar inicio de Cuadro 4
        if "## 4. Especificaciones detalladas de las sustancias" in line:
            output_lines.append(line)
            i += 1
            tabla_4_block = []
            while i < len(lines) and "## ANEXO" not in lines[i]:
                tabla_4_block.append(lines[i])
                i += 1
            oracion_4 = procesar_tabla_4(tabla_4_block)
            output_lines.append(oracion_4 + "\n")
            continue

        # Detectar Cuadro 1 (Simulantes alimentarios)
        if "## Cuadro 1" in line:
            output_lines.append(line)
            i += 1
            simulantes_block = []
            while i < len(lines) and "## 2. Asignación general" not in lines[i]:
                simulantes_block.append(lines[i])
                i += 1
            oraciones_sim = procesar_tabla_simulantes(simulantes_block)
            output_lines.extend([o + "\n" for o in oraciones_sim])
            continue

        # Si no estamos dentro de ningún bloque especial
        output_lines.append(line)
        i += 1

    # Guardar el resultado
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(output_lines)

    print(f"Documento guardado correctamente con las tablas transformadas en {output_path}")

def procesar_cuadro_1(lines):
    oraciones = []
    for line in lines:
        match = re.match(r"\|\s*(.*?)\s*\|\s*(.*?)\s*\|", line)
        if match:
            tiempo = match.group(1).replace('\xa0', ' ')
            duracion = match.group(2).replace('\xa0', ' ')
            if "Más de 30 días" in tiempo:
                oraciones.append("Si el tiempo de contacto es superior a 30 días, deberán consultarse las condiciones específicas aplicables.")
            else:
                oraciones.append(f"Si el tiempo de contacto previsto es {tiempo.lower()}, la duración del ensayo será de {duracion.lower()}.")
    return oraciones

def procesar_cuadro_2(lines):
    oraciones = []
    for line in lines:
        match = re.match(r"\|\s*(.*?)\s*\|\s*(.*?)\s*\|", line)
        if match:
            temperatura = match.group(1).replace('\xa0', ' ')
            temperatura_ensayo = match.group(2).replace('\xa0', ' ')
            if "T > 175 °C" in temperatura:
                oraciones.append("Si la temperatura es superior a 175 ºC, Esta temperatura se usará solo para los simulantes alimentarios D2 y E. Para las aplicaciones calentadas bajo presión, el ensayo de migración podrá efectuarse bajo presión a la temperatura pertinente. Para los simulantes alimentarios A, B, C o D1, el ensayo puede sustituirse por un ensayo a 100 °C o a temperatura de reflujo con una duración cuatro veces superior a la seleccionada conforme a las condiciones del cuadro 1.")
            else:
                oraciones.append(f"Si el contacto en las peores condiciones previsibles de uso, tiene una temperatura de contacto de  {temperatura.lower()}, en las condiciones de ensayo , la temperatura de ensayo será de {temperatura_ensayo.lower()}")
    return oraciones

def procesar_cuadro_3(lines):
    oraciones = []
    for line in lines:
        match = re.match(r"\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|", line)
        if match:
            numero_ensayo = match.group(1).replace('\xa0', ' ')
            tiempo_contacto = match.group(2).replace('\xa0', ' ')
            condiciones_contacto = match.group(3).replace('\xa0', ' ')
            oraciones.append(f"El número de ensayo {numero_ensayo.lower()}, el tiempo de contacto en días [d] u horas [h] a Temperatura  de contacto en °C es de {tiempo_contacto.lower()}, las condiciones de contacto alimentario  previstas es {condiciones_contacto.lower()}")
    return oraciones

def procesar_cuadro_4(lines):
    oraciones = []
    for line in lines:
        match = re.match(r"\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|", line)
        if match:
            numero_ensayo = match.group(1).replace('\xa0', ' ')
            condiciones_ensayo = match.group(2).replace('\xa0', ' ')
            condiciones_contacto = match.group(3).replace('\xa0', ' ')
            incluye = match.group(4).replace('\xa0', ' ')
            oraciones.append(f"El número de ensayo {numero_ensayo.lower()}, la condiciones de ensayo son {condiciones_ensayo.lower()}, las condiciones de contacto alimentario  previstas es {condiciones_contacto.lower()}, incluye las condiciones de contacto alimentario descritas para {incluye.lower()}")
    return oraciones

def generar_oraciones_tablas_doc6(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    output_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Detectar inicio de Cuadro 1
        if "Cuadro 2:" in line:
            output_lines.append(line)
            i += 1
            tabla_1_block = []
            while i < len(lines) and not lines[i].startswith("## Temperatura"):
                tabla_1_block.append(lines[i])
                i += 1
            oraciones_1 = procesar_cuadro_1(tabla_1_block)
            output_lines.extend([o + "\n" for o in oraciones_1])
            continue

        if "## Temperatura de contacto" in line:
            output_lines.append(line)
            i += 1
            tabla_2_block = []
            while i < len(lines) and not lines[i].startswith("( * ) Esta temperatura"):
                tabla_2_block.append(lines[i])
                i += 1
            oraciones_2 = procesar_cuadro_1(tabla_2_block)
            output_lines.extend([o + "\n" for o in oraciones_2])
            continue

        if "## Condiciones normalizadas de ensayo" in line:
            output_lines.append(line)
            i += 1
            tabla_3_block = []
            while i < len(lines) and not lines[i].startswith("El ensayo OM7"):
                tabla_3_block.append(lines[i])
                i += 1
            oraciones_3 = procesar_cuadro_3(tabla_3_block)
            output_lines.extend([o + "\n" for o in oraciones_3])
            continue

        if "En caso de que no sea técnicamente posible efectuar OM7" in line:
            output_lines.append(line)
            i += 1
            tabla_4_block = []
            while i < len(lines) and not lines[i].startswith("## 3.3. Objetos de uso repetido"):
                tabla_4_block.append(lines[i])
                i += 1
            oraciones_4 = procesar_cuadro_4(tabla_4_block)
            output_lines.extend([o + "\n" for o in oraciones_4])
            continue

        # Si no estamos dentro de ningún bloque especial
        output_lines.append(line)
        i += 1

    # Guardar el resultado
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(output_lines)

    print(f"Documento guardado correctamente con las tablas transformadas en {output_path}")

def unir_txts_especificos(lista_archivos, archivo_salida):
    with open(archivo_salida, "w", encoding="utf-8") as salida:
        for archivo in lista_archivos:
            ruta = Path(archivo)
            if ruta.exists():
                with open(ruta, "r", encoding="utf-8") as f:
                    contenido = f.read()
                    salida.write(f"===== {ruta.name} =====\n\n")  # Opcional
                    salida.write(contenido + "\n\n")
            else:
                print(f"[Aviso] El archivo no existe: {ruta}")

    print(f"{len(lista_archivos)} archivos combinados en {archivo_salida}")
# Ejecutar ambos procesamientos
procesar_tabla1(
    input_file=os.path.join("corpus", "L00001-00089-15-68_docling.txt"),
    output_file=os.path.join("corpus", "L00001-00089-15-68_docling_oraciones.txt")
)

procesar_tabla2(
    input_file=os.path.join("corpus", "L00001-00089-69-71_docling.txt"),
    output_file=os.path.join("corpus", "L00001-00089-69-71_docling_oraciones.txt")
)
generar_oraciones_tablas_doc4(
    input_path="corpus/L00001-00089-72-75_docling.txt",
    output_path="corpus/L00001-00089-72-75_docling_oraciones.txt"
)

generar_oraciones_tablas_doc6(
    input_path="corpus/L00001-00089-81-89_docling.txt",
    output_path="corpus/L00001-00089-81-89_docling_oraciones.txt"
)

archivos = [
    "corpus/L00001-00089-1-14_docling.txt",
    "corpus/L00001-00089-15-68_docling_oraciones.txt",
    "corpus/L00001-00089-69-71_docling_oraciones.txt",
    "corpus/L00001-00089-72-75_docling_oraciones.txt",
    "corpus/L00001-00089-76-80_docling_oraciones.txt",
    "corpus/L00001-00089-81-89_docling_oraciones.txt",    
]

unir_txts_especificos(archivos, "corpus/L00001-00089_final.txt")