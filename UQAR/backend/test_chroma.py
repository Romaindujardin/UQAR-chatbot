import requests
import sys

try:
    # Essayer de se connecter à ChromaDB avec une requête HTTP directe
    response = requests.get("http://chromadb:8000/api/v2/heartbeat")
    
    if response.status_code == 200:
        print(f"ChromaDB est accessible ! Heartbeat: {response.json()}")
        sys.exit(0)
    else:
        print(f"Erreur lors de la connexion à ChromaDB: {response.status_code} - {response.text}")
        sys.exit(1)
except Exception as e:
    print(f"Erreur lors de la connexion à ChromaDB: {e}")
    sys.exit(1) 