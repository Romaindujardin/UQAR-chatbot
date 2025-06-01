import { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  // Only allow POST method
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    console.log(`Forwarding registration request to ${backendUrl}/api/auth/register`);
    
    // Ajouter un délai d'attente pour la requête
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    
    try {
      // Forward the request to the backend
      const response = await fetch(`${backendUrl}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(req.body),
        signal: controller.signal
      });
      
      // Annuler le délai d'attente
      clearTimeout(timeoutId);

      // Lire le corps de la réponse (qu'elle soit réussie ou non)
      const responseText = await response.text();
      let responseData;
      
      // Essayer de parser la réponse comme JSON
      try {
        responseData = responseText ? JSON.parse(responseText) : {};
      } catch (parseError) {
        console.error('Error parsing response as JSON:', responseText);
        responseData = { 
          error: 'Invalid response format', 
          detail: 'Unable to parse response' 
        };
      }

      // Traiter les erreurs et les réponses réussies
      if (!response.ok) {
        console.error('Registration error from backend:', responseData);
        
        // Traiter les différents types d'erreurs
        if (responseData.detail && typeof responseData.detail === 'object') {
          // Si detail est un objet (comme avec les erreurs de validation Pydantic)
          // Le convertir en chaîne de caractères pour éviter l'erreur React
          responseData.detail = JSON.stringify(responseData.detail);
        }
        
        return res.status(response.status).json(responseData);
      }

      // Réponse réussie
      console.log('Registration successful, returning data to client');
      return res.status(response.status).json(responseData);
    } catch (fetchError: any) {
      console.error('Fetch error:', fetchError.message);
      return res.status(500).json({
        error: 'Network error',
        detail: fetchError.message || 'Failed to connect to backend'
      });
    }
  } catch (error: any) {
    console.error('Error in registration API route:', error);
    return res.status(500).json({ 
      error: 'Internal server error',
      detail: error.message || 'Unknown error'
    });
  }
} 