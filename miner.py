import requests
import time
import subprocess
import os
import shutil
import ast  
import re   

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

#Función para limpiar y separar palabras
def procesar_y_limpiar_nombres(lista_nombres):
    palabras_finales = []
    for nombre in lista_nombres:
        # 1. Detectar camelCase: insertamos un guión bajo entre una minúscula y una mayúscula
        # Ejemplo: "retainAll" se convierte en "retain_All"
        nombre_modificado = re.sub(r'([a-z])([A-Z])', r'\1_\2', nombre)
        
        # 2. Ahora que todo tiene un formato similar a snake_case, separamos por guiones bajos
        # "make_response" -> ["make", "response"]
        # "retain_All" -> ["retain", "All"]
        palabras = nombre_modificado.split('_')
        
        # 3. Limpiamos símbolos extraños y convertimos a minúsculas
        for p in palabras:
            # Eliminamos cualquier cosa que no sea una letra de la A a la Z
            p_limpia = re.sub(r'[^a-zA-Z]', '', p).lower()
            
            # Solo guardamos la palabra si no quedó vacía y tiene más de 1 letra (opcional, para evitar variables basura como 'i', 'x')
            if len(p_limpia) > 1: 
                palabras_finales.append(p_limpia)
                
    return palabras_finales
# ---------------------------------------------------------------

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
                subprocess.run(["git", "clone", "--depth", "1", clone_url, ruta_destino], check=True, capture_output=True)
                
                archivos_a_procesar = encontrar_archivos_objetivo(ruta_destino)
                
                nombres_extraidos = []
                for archivo in archivos_a_procesar:
                    if archivo.endswith('.py'):
                        nombres_extraidos.extend(extraer_nombres_python(archivo))
                    elif archivo.endswith('.java'):
                        nombres_extraidos.extend(extraer_nombres_java(archivo))
                
               
                if nombres_extraidos:
                    palabras_procesadas = procesar_y_limpiar_nombres(nombres_extraidos)
                    print(f"   -> Se extrajeron y limpiaron {len(palabras_procesadas)} palabras en total.")
                    print(f"   -> Muestra de palabras listas para enviar: {palabras_procesadas[:10]}...")
                
            except subprocess.CalledProcessError as e:
                print(f"   -> Error al clonar {nombre_repo}: {e}")
            
            finally:
                if os.path.exists(ruta_destino):
                    shutil.rmtree(ruta_destino, ignore_errors=True)
            
        pagina_actual += 1
        time.sleep(2) 

if __name__ == "__main__":
    iniciar_miner()