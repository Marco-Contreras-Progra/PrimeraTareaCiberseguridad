import requests
import time
import subprocess
import os
import shutil

GITHUB_TOKEN = 'TOKEN'  # REEMPLAZA ESTO CON TU PROPIO TOKEN
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

# --- NUEVO: Definimos la carpeta temporal donde se clonarán los repos ---
CARPETA_TEMPORAL = "./repos_temporales" 

# --- NUEVO: Función para buscar archivos ---
def encontrar_archivos_objetivo(ruta_base):
    """Recorre todas las carpetas y devuelve una lista con las rutas de los archivos .py y .java"""
    archivos_encontrados = []
    # os.walk recorre el directorio principal y todos sus subdirectorios automáticamente
    for raiz, directorios, archivos in os.walk(ruta_base):
        for archivo in archivos:
            if archivo.endswith('.py') or archivo.endswith('.java'):
                # Unimos la ruta de la carpeta con el nombre del archivo
                ruta_completa = os.path.join(raiz, archivo)
                archivos_encontrados.append(ruta_completa)
    
    return archivos_encontrados
# -----------------------------------------

def obtener_repositorios_por_pagina(pagina):
    # ... (tu código se mantiene igual aquí) ...
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
    
    # Creamos la carpeta temporal si no existe
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
            clone_url = repo['clone_url']  # --- NUEVO: Extraemos la URL para clonar ---
            
            print(f"Miner analizando: {nombre_repo} (estrellas: {estrellas})")

            nombre_carpeta_seguro = nombre_repo.replace('/', '_')
            ruta_destino = os.path.join(CARPETA_TEMPORAL, nombre_carpeta_seguro)

            try:
                print(f"   -> Clonando repositorio...")
                subprocess.run(
                    ["git", "clone", "--depth", "1", clone_url, ruta_destino],
                    check=True, 
                    capture_output=True 
                )
                print(f"   -> ¡Clonado exitosamente en {ruta_destino}!")
                
                # --- NUEVO: PASO 1 INTEGRADO AQUÍ ---
                archivos_a_procesar = encontrar_archivos_objetivo(ruta_destino)
                print(f"   -> Se encontraron {len(archivos_a_procesar)} archivos (.py y .java) para analizar.")
                
                # En el próximo paso, iteraremos sobre esta lista "archivos_a_procesar"
                # ------------------------------------
                
            except subprocess.CalledProcessError as e:
                print(f"   -> Error al clonar {nombre_repo}: {e}")
            
            finally:
                if os.path.exists(ruta_destino):
                    print(f"   -> Borrando archivos temporales...")
                    shutil.rmtree(ruta_destino, ignore_errors=True)
            
        pagina_actual += 1
        time.sleep(2) 

if __name__ == "__main__":
    iniciar_miner()