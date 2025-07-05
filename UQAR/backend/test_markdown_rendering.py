#!/usr/bin/env python3
"""
Test script pour vérifier le rendu Markdown dans les réponses du chat
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

def get_or_create_session(token):
    """Récupérer ou créer une session de chat"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Récupérer les sessions existantes
    response = requests.get(f"{BASE_URL}/api/chat/sessions", headers=headers)
    if response.status_code == 200:
        sessions = response.json()
        if sessions:
            return sessions[0]
    
    # Récupérer les sections
    response = requests.get(f"{BASE_URL}/api/sections/", headers=headers)
    if response.status_code != 200:
        print("Erreur lors de la récupération des sections")
        return None
    
    sections = response.json()
    if not sections:
        print("Aucune section trouvée")
        return None
    
    # Créer une nouvelle session
    response = requests.post(f"{BASE_URL}/api/chat/sessions", 
                            json={"section_id": sections[0]["id"]}, 
                            headers=headers)
    
    if response.status_code != 200:
        print(f"Erreur lors de la création de session: {response.status_code}")
        return None
    
    return response.json()

def test_markdown_message(token, session_id, message):
    """Tester un message et vérifier la réponse Markdown"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n📝 Test: {message}")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/sessions/{session_id}/messages/stream",
            json={"content": message},
            headers=headers,
            stream=True
        )
        
        if response.status_code != 200:
            print(f"❌ Erreur: {response.status_code}")
            return False
        
        full_response = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith("data: "):
                    try:
                        data = json.loads(line_str[6:])
                        
                        if data.get("type") == "assistant_chunk":
                            print(data["content"], end="", flush=True)
                            full_response += data["content"]
                        
                        elif data.get("type") == "assistant_message" and data.get("done"):
                            print(f"\n\n✅ Réponse complète reçue")
                            
                            # Analyser le contenu Markdown
                            markdown_elements = analyze_markdown(full_response)
                            if markdown_elements:
                                print("\n🎨 Éléments Markdown détectés:")
                                for element in markdown_elements:
                                    print(f"  - {element}")
                            else:
                                print("\n⚠️  Aucun élément Markdown détecté")
                            
                            return True
                            
                    except json.JSONDecodeError:
                        continue
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def analyze_markdown(text):
    """Analyser le texte pour détecter les éléments Markdown"""
    elements = []
    
    # Vérifier le gras
    if "**" in text:
        elements.append("Texte en gras (**texte**)")
    
    # Vérifier l'italique
    if "*" in text and "**" not in text:
        elements.append("Texte en italique (*texte*)")
    
    # Vérifier le code inline
    if "`" in text and "```" not in text:
        elements.append("Code inline (`code`)")
    
    # Vérifier les blocs de code
    if "```" in text:
        elements.append("Bloc de code (```)")
    
    # Vérifier les titres
    if text.count("#") > 0:
        elements.append("Titres (# ## ###)")
    
    # Vérifier les listes
    if "\n-" in text or "\n*" in text:
        elements.append("Listes (- ou *)")
    
    # Vérifier les listes numérotées
    if any(line.strip().startswith(f"{i}.") for i in range(1, 10) for line in text.split('\n')):
        elements.append("Listes numérotées (1. 2. 3.)")
    
    return elements

def main():
    print("=== Test du rendu Markdown dans le chat ===")
    
    # 1. Se connecter
    print("\n1. Connexion...")
    token = login_student()
    if not token:
        print("❌ Impossible de se connecter")
        return
    print("✅ Connexion réussie")
    
    # 2. Récupérer ou créer une session
    print("\n2. Récupération/création de session...")
    session = get_or_create_session(token)
    if not session:
        print("❌ Impossible de créer une session")
        return
    print(f"✅ Session: {session['title']}")
    
    # 3. Tester différents types de contenu Markdown
    test_messages = [
        "Peux-tu m'expliquer ce qu'est la programmation orientée objet avec des exemples de code ?",
        "Quels sont les avantages et inconvénients des différents langages de programmation ?",
        "Comment créer une fonction en Python ? Donne-moi un exemple détaillé.",
        "Explique-moi les concepts de base des structures de données avec des exemples."
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{'='*20} Test {i}/{len(test_messages)} {'='*20}")
        success = test_markdown_message(token, session["id"], message)
        
        if not success:
            print(f"❌ Test {i} échoué")
            break
        
        if i < len(test_messages):
            print("\n⏳ Attente de 3 secondes avant le prochain test...")
            import time
            time.sleep(3)
    
    print(f"\n{'='*60}")
    print("🎯 Vérifiez maintenant l'interface web pour voir le rendu Markdown !")
    print("   Les réponses doivent afficher :")
    print("   - **Texte en gras**")
    print("   - `Code inline`")
    print("   - ```Blocs de code```")
    print("   - ## Titres")
    print("   - - Listes à puces")

if __name__ == "__main__":
    main() 