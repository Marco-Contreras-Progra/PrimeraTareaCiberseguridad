import requests
import time
import subprocess
import os
import shutil
import ast
import re
import json # Para guardar en formato JSON

GITHUB_TOKEN = ''  # REEMPLAZA ESTO CON TU PROPIO TOKEN
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

CARPETA_TEMPORAL = "./repos_temporales" 
# Carpeta donde guardaremos el JSON que leerá el Visualizer
CARPETA_COMPARTIDA = "./datos_compartidos" 
ARCHIVO_JSONL = os.path.join(CARPETA_COMPARTIDA, "palabras.jsonl")

def encontrar_archivos_objetivo(ruta_base):
    archivos_encontrados = []
    for raiz, directorios, archivos in os.walk(ruta_base):
        for archivo in archivos:
            if archivo.endswith('.py') or archivo.endswith('.java'):
                ruta_completa = os.path.join(raiz, archivo)
                archivos_encontrados.append(ruta_completa)
    return archivos_encontrados

def extraer_nombres_python(ruta_archivo):
    nombres = []
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
            contenido = archivo.read()
            arbol = ast.parse(contenido)
            for nodo in ast.walk(arbol):
                if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    nombres.append(nodo.name)
    except Exception as e:
        pass
    return nombres

def extraer_nombres_java(ruta_archivo):
    nombres = []
    patron_java = re.compile(r'(?:public|protected|private)\s+(?:static\s+)?[\w\<\>\[\]\?]+\s+(\w+)\s*\(')
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
            contenido = archivo.read()
            nombres = patron_java.findall(contenido)
    except Exception as e:
        pass
    return nombres

def procesar_y_limpiar_nombres(lista_nombres):
    palabras_finales = []
    for nombre in lista_nombres:
        nombre_modificado = re.sub(r'([a-z])([A-Z])', r'\1_\2', nombre)
        palabras = nombre_modificado.split('_')
        for p in palabras:
            p_limpia = re.sub(r'[^a-zA-Z]', '', p).lower()
            if len(p_limpia) > 1: 
                palabras_finales.append(p_limpia)
    return palabras_finales

# Función para guardar en el archivo JSONL 
def guardar_en_json(palabras, lenguaje, repo_nombre):
    """Guarda cada palabra como un objeto JSON independiente en una nueva línea."""
    with open(ARCHIVO_JSONL, 'a', encoding='utf-8') as f:
        for palabra in palabras:
            datos = {
                "palabra": palabra,
                "lenguaje": lenguaje,
                "repositorio": repo_nombre,
                "timestamp": time.time() # Útil para que el visualizer sepa qué tan nuevo es el dato
            }
            # json.dumps convierte el diccionario a un texto con formato JSON
            f.write(json.dumps(datos) + "\n")

def obtener_repositorios_por_pagina(pagina):
    url = f"https://api.github.com/search/repositories?q=language:python+language:java&sort=stars&order=desc&per_page=10&page={pagina}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get('items', [])
    else:
        print(f"Error en la API: {response.status_code} - {response.text}")
        return None

def iniciar_miner():
    print("Iniciando el Miner de GitHub...")
    pagina_actual = 1
    os.makedirs(CARPETA_TEMPORAL, exist_ok=True) 
    os.makedirs(CARPETA_COMPARTIDA, exist_ok=True) # --- NUEVO: PASO 4
    
    # Limpiamos el archivo JSON de ejecuciones anteriores
    if os.path.exists(ARCHIVO_JSONL):
        os.remove(ARCHIVO_JSONL)

    while True:
        print(f"\n--- Consultando página {pagina_actual} ---")
        repos = obtener_repositorios_por_pagina(pagina_actual)
        
        if repos is None:
            time.sleep(60)
            continue
            
        if not repos:
            pagina_actual = 1
            continue
            
        for repo in repos:
            nombre_repo = repo['full_name']
            estrellas = repo['stargazers_count']
            clone_url = repo['clone_url']
            
            print(f"Miner analizando: {nombre_repo} (estrellas: {estrellas})")

            nombre_carpeta_seguro = nombre_repo.replace('/', '_')
            ruta_destino = os.path.join(CARPETA_TEMPORAL, nombre_carpeta_seguro)

            try:
                subprocess.run(["git", "clone", "--depth", "1", clone_url, ruta_destino], check=True, capture_output=True)
                
                archivos_a_procesar = encontrar_archivos_objetivo(ruta_destino)
                
                # Separamos la lógica para saber si es Python o Java
                nombres_py = []
                nombres_java = []
                
                for archivo in archivos_a_procesar:
                    if archivo.endswith('.py'):
                        nombres_py.extend(extraer_nombres_python(archivo))
                    elif archivo.endswith('.java'):
                        nombres_java.extend(extraer_nombres_java(archivo))
                
                # Procesamos y guardamos Python
                if nombres_py:
                    palabras_py = procesar_y_limpiar_nombres(nombres_py)
                    guardar_en_json(palabras_py, "python", nombre_repo)
                    
                # Procesamos y guardamos Java
                if nombres_java:
                    palabras_java = procesar_y_limpiar_nombres(nombres_java)
                    guardar_en_json(palabras_java, "java", nombre_repo)

                total_palabras = len(nombres_py) + len(nombres_java)
                print(f"   -> Se extrajeron y guardaron {total_palabras} palabras en {ARCHIVO_JSONL}.")
                
            except subprocess.CalledProcessError as e:
                print(f"   -> Error al clonar {nombre_repo}: {e}")
            
            finally:
                if os.path.exists(ruta_destino):
                    shutil.rmtree(ruta_destino, ignore_errors=True)
            
        pagina_actual += 1
        time.sleep(2) 

if __name__ == "__main__":
    iniciar_miner()