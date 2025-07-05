#!/usr/bin/env python3
"""
Test script pour vérifier l'endpoint de streaming du chat
"""

import requests
import json
import sys
import os

# Configuration
BASE_URL = "http://localhost:8000"
STUDENT_USERNAME = "student"
STUDENT_PASSWORD = "student123"

def login_student():
    """Se connecter en tant qu'étudiant"""
    login_data = {
        "username": STUDENT_USERNAME,
        "password": STUDENT_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
    
    if response.status_code != 200:
        print(f"Erreur de connexion étudiant: {response.status_code}")
        print(response.text)
        return None
    
    return response.json()["access_token"]

def get_chat_sessions(token):
    """Récupérer les sessions de chat"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/api/chat/sessions", headers=headers)
    
    if response.status_code != 200:
        print(f"Erreur lors de la récupération des sessions: {response.status_code}")
        print(response.text)
        return []
    
    return response.json()

def create_chat_session(token, section_id):
    """Créer une session de chat"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(f"{BASE_URL}/api/chat/sessions", 
                            json={"section_id": section_id}, 
                            headers=headers)
    
    if response.status_code != 200:
        print(f"Erreur lors de la création de session: {response.status_code}")
        print(response.text)
        return None
    
    return response.json()

def get_sections(token):
    """Récupérer les sections"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/api/sections/", headers=headers)
    
    if response.status_code != 200:
        print(f"Erreur lors de la récupération des sections: {response.status_code}")
        print(response.text)
        return []
    
    return response.json()

def test_streaming(token, session_id, message):
    """Tester le streaming"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/sessions/{session_id}/messages/stream",
            json={"content": message},
            headers=headers,
            stream=True
        )
        
        if response.status_code != 200:
            print(f"Erreur streaming: {response.status_code}")
            print(response.text)
            return False
        
        print(f"🔄 Streaming démarré pour: '{message}'")
        print("-" * 50)
        
        assistant_response = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith("data: "):
                    try:
                        data = json.loads(line_str[6:])
                        
                        if data.get("error"):
                            print(f"❌ Erreur: {data['error']}")
                            return False
                        
                        if data.get("type") == "user_message":
                            print(f"👤 Utilisateur: {data['content']}")
                        
                        elif data.get("type") == "assistant_start":
                            print("🤖 Assistant commence à répondre...")
                        
                        elif data.get("type") == "assistant_chunk":
                            print(data["content"], end="", flush=True)
                            assistant_response += data["content"]
                        
                        elif data.get("type") == "assistant_message" and data.get("done"):
                            print(f"\n✅ Réponse terminée (ID: {data['id']})")
                            print(f"📝 Réponse complète: {data['content'][:100]}...")
                            return True
                            
                    except json.JSONDecodeError as e:
                        print(f"Erreur JSON: {e}")
                        continue
        
        return True
        
    except Exception as e:
        print(f"Erreur lors du test streaming: {e}")
        return False

def main():
    print("=== Test du streaming de chat ===")
    
    # 1. Se connecter
    print("\n1. Connexion en tant qu'étudiant...")
    token = login_student()
    if not token:
        print("❌ Impossible de se connecter")
        return
    print("✅ Connexion réussie")
    
    # 2. Récupérer les sections
    print("\n2. Récupération des sections...")
    sections = get_sections(token)
    if not sections:
        print("❌ Aucune section trouvée")
        return
    print(f"✅ {len(sections)} sections trouvées")
    
    # 3. Récupérer ou créer une session
    print("\n3. Récupération des sessions existantes...")
    sessions = get_chat_sessions(token)
    
    if sessions:
        session = sessions[0]
        print(f"✅ Utilisation de la session existante: {session['title']}")
    else:
        print("Aucune session existante, création d'une nouvelle...")
        session = create_chat_session(token, sections[0]["id"])
        if not session:
            print("❌ Impossible de créer une session")
            return
        print(f"✅ Session créée: {session['title']}")
    
    # 4. Tester le streaming
    print("\n4. Test du streaming...")
    
    test_messages = [
        "Bonjour, peux-tu m'expliquer le concept principal de ce cours ?",
        "Quels sont les points importants à retenir ?"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Test {i}/{len(test_messages)} ---")
        success = test_streaming(token, session["id"], message)
        
        if success:
            print(f"✅ Test {i} réussi !")
        else:
            print(f"❌ Test {i} échoué")
            break
        
        if i < len(test_messages):
            print("\nAttente de 2 secondes avant le prochain test...")
            import time
            time.sleep(2)
    
    print("\n=== Fin des tests ===")

if __name__ == "__main__":
    main() 