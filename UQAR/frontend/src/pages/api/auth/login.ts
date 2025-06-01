import { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  // Only allow POST method
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    console.log(`Forwarding login request to ${backendUrl}/api/auth/login`);
    
    // Convertir les données JSON en URLSearchParams pour le backend FastAPI
    const data = req.body;
    const formData = new URLSearchParams();
    
    // Ajouter les paramètres requis par OAuth2PasswordRequestForm
    formData.append('username', data.username);
    formData.append('password', data.password);
    
    console.log(`Request data prepared: username=${data.username}`);
    
    // Ajouter un délai d'attente pour la requête
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    
    try {
      // Forward the request to the backend
      const response = await fetch(`${backendUrl}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
        signal: controller.signal
      });
      
      // Annuler le délai d'attente
      clearTimeout(timeoutId);

      // Check if response is OK
      if (!response.ok) {
        // Try to parse as JSON first
        try {
          const errorData = await response.json();
          console.error('Login error from backend:', errorData);
          return res.status(response.status).json(errorData);
        } catch (parseError) {
          // If JSON parsing fails, get the text response
          const errorText = await response.text();
          console.error('Login error from backend (non-JSON):', errorText);
          return res.status(response.status).json({ 
            error: 'Backend error', 
            detail: `Error status ${response.status}: ${errorText.substring(0, 200)}...`
          });
        }
      }

      // Try to parse the successful response as JSON
      try {
        const data = await response.json();
        console.log('Login successful, returning data to client');
        return res.status(response.status).json(data);
      } catch (parseError) {
        // If successful response isn't JSON
        const responseText = await response.text();
        console.error('Error parsing successful response as JSON:', responseText.substring(0, 200));
        return res.status(500).json({ 
          error: 'Invalid response format',
          detail: 'The backend returned a non-JSON response'
        });
      }
    } catch (fetchError: any) {
      console.error('Fetch error:', fetchError.message);
      return res.status(500).json({
        error: 'Network error',
        detail: fetchError.message || 'Failed to connect to backend'
      });
    }
  } catch (error: any) {
    console.error('Error in login API route:', error);
    return res.status(500).json({ 
      error: 'Internal server error',
      detail: error.message || 'Unknown error'
    });
  }
} 