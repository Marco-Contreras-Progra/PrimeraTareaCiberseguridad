import requests
import time
import subprocess
import os
import shutil
import ast  # Para analizar código Python (Abstract Syntax Tree)
import re   # Para buscar patrones en código Java (Expresiones Regulares)

GITHUB_TOKEN = 'token'  # REEMPLAZA ESTO CON TU PROPIO TOKEN
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

CARPETA_TEMPORAL = "./repos_temporales" 

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
            # Convertimos el texto en un árbol de sintaxis que Python entiende
            arbol = ast.parse(contenido)
            # Recorremos cada "nodo" o elemento del código
            for nodo in ast.walk(arbol):
                if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    nombres.append(nodo.name)
    except Exception as e:
        pass
    return nombres

def extraer_nombres_java(ruta_archivo):
    nombres = []
    # Usamos una expresión regular para buscar el patrón típico de un método en Java
    # Busca visibilidad (public/private...), tipo de retorno, nombre_metodo y un paréntesis '('
    patron_java = re.compile(r'(?:public|protected|private)\s+(?:static\s+)?[\w\<\>\[\]\?]+\s+(\w+)\s*\(')
    
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
            contenido = archivo.read()
            # findall nos devuelve una lista con todas las palabras que coinciden con el grupo (\w+)
            nombres = patron_java.findall(contenido)
    except Exception as e:
        pass
    return nombres
# -----------------------------------------------------

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
                subprocess.run(
                    ["git", "clone", "--depth", "1", clone_url, ruta_destino],
                    check=True, 
                    capture_output=True 
                )
                
                archivos_a_procesar = encontrar_archivos_objetivo(ruta_destino)
                print(f"   -> Se encontraron {len(archivos_a_procesar)} archivos (.py y .java). Extrayendo nombres...")
                
                nombres_extraidos = []
                for archivo in archivos_a_procesar:
                    if archivo.endswith('.py'):
                        nombres = extraer_nombres_python(archivo)
                        nombres_extraidos.extend(nombres)
                    elif archivo.endswith('.java'):
                        nombres = extraer_nombres_java(archivo)
                        nombres_extraidos.extend(nombres)
                
                # Imprimimos una muestra para verificar que funciona
                if nombres_extraidos:
                    print(f"   -> ¡Éxito! Se extrajeron {len(nombres_extraidos)} funciones/métodos en total.")
                    print(f"   -> Muestra de lo encontrado: {nombres_extraidos[:5]}...")
                # ------------------------------------
                
            except subprocess.CalledProcessError as e:
                print(f"   -> Error al clonar {nombre_repo}: {e}")
            
            finally:
                if os.path.exists(ruta_destino):
                    shutil.rmtree(ruta_destino, ignore_errors=True)
            
        pagina_actual += 1
        time.sleep(2) 

if __name__ == "__main__":
    iniciar_miner()