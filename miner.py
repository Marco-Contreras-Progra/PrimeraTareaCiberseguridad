import requests
import time

GITHUB_TOKEN = ''  # REEMPLAZA ESTO CON TU PROPIO TOKEN
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

def obtener_repositorios_por_pagina(pagina):
    """Consulta la API de GitHub buscando repos de Python y Java, ordenados por estrellas."""
    # Fíjate en el query (q=), el sort (stars) y el order (desc)
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
    
    # REQUISITO: "demostrar que el proceso puede ejecutarse de manera continua"
    while True:
        print(f"\n--- Consultando página {pagina_actual} ---")
        repos = obtener_repositorios_por_pagina(pagina_actual)
        
        # Manejo de errores o límite de tasa (Rate Limit)
        if repos is None:
            print("Esperando 60 segundos antes de reintentar para enfriar la API...")
            time.sleep(60)
            continue
            
        if not repos:
            print("No hay más repositorios. Volviendo a empezar.")
            pagina_actual = 1
            continue
            
        # Procesar cada repositorio encontrado
        for repo in repos:
            nombre_repo = repo['full_name']
            estrellas = repo['stargazers_count']
            
            print(f"Miner analizando: {nombre_repo} (⭐️ {estrellas})")
            
        # Pasar a la siguiente página de resultados
        pagina_actual += 1
        
        # Pausa amable para no saturar la API entre páginas
        time.sleep(2) 

if __name__ == "__main__":
    iniciar_miner()