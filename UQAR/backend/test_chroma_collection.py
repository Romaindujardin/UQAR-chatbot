import chromadb
import sys

try:
    # Créer un client ChromaDB
    client = chromadb.HttpClient(
        host="chromadb",
        port=8000
    )
    
    # Vérifier la connexion
    heartbeat = client.heartbeat()
    print(f"ChromaDB est accessible ! Heartbeat: {heartbeat}")
    
    # Lister les collections existantes
    collections = client.list_collections()
    print(f"Collections existantes: {[c.name for c in collections]}")
    
    # Créer une collection
    collection_name = "test_collection"
    try:
        # Supprimer la collection si elle existe déjà
        client.delete_collection(collection_name)
        print(f"Collection {collection_name} supprimée")
    except:
        pass
    
    collection = client.create_collection(name=collection_name)
    print(f"Collection créée avec succès: {collection.name}")
    
    # Ajouter des documents à la collection
    collection.add(
        ids=["id1", "id2"],
        documents=["This is a test document", "This is another test document"],
        metadatas=[{"source": "test"}, {"source": "test"}]
    )
    print("Documents ajoutés avec succès")
    
    # Rechercher dans la collection
    results = collection.query(
        query_texts=["test document"],
        n_results=2
    )
    print(f"Résultats de la recherche: {results}")
    
    sys.exit(0)
except Exception as e:
    print(f"Erreur lors de l'utilisation de ChromaDB: {e}")
    sys.exit(1) 