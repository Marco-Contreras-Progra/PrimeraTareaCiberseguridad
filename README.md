# PrimeraTareaCiberseguridad

# Analizador de Repositorios en Tiempo Real (Productor-Consumidor)

Este proyecto implementa una arquitectura Productor-Consumidor para extraer, analizar y visualizar en tiempo real las palabras más utilizadas en funciones y variables de repositorios de código (Python) alojados en GitHub.

## Instrucciones de Ejecución

Para ejecutar este sistema, solo necesitas tener instalado **Docker** y **Docker Compose V2**.

1. Clona o descarga este proyecto en tu máquina local, en el miner.py hay que colocar un token de github para que el miner pueda realizar la extraccion de los repositorios.
2. Abre una terminal.
3. Ejecuta el siguiente comando para construir y levantar los contenedores:  docker compose up --build
4. Espera unos segundos a que el "Miner" comience a procesar el primer repositorio.
5. Abre tu navegador web e ingresa a: http://localhost:8000
6. Para detener el sistema ejecuta en el terminal docker compose down
