import type { NextApiRequest, NextApiResponse } from 'next';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'PUT') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { exerciseId, title } = req.body;
    
    if (!exerciseId) {
      return res.status(400).json({ error: 'Exercise ID is required' });
    }

    if (!title || typeof title !== 'string' || title.trim().length === 0) {
      return res.status(400).json({ error: 'Title is required' });
    }

    const authHeader = req.headers.authorization;
    if (!authHeader) {
      return res.status(401).json({ error: 'Authorization header required' });
    }

    console.log(`Updating title for exercise ${exerciseId} to: ${title}`);
    
    const response = await fetch(`${BACKEND_URL}/api/exercises/exercises/${exerciseId}/title`, {
      method: 'PUT',
      headers: {
        'Authorization': authHeader,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ title: title.trim() }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend error:', response.status, errorText);
      return res.status(response.status).json({ 
        error: `Backend error: ${response.status}`,
        details: errorText 
      });
    }

    const data = await response.json();
    console.log('Exercise title updated successfully:', data);
    
    return res.status(200).json(data);
    
  } catch (error) {
    console.error('Error updating exercise title:', error);
    return res.status(500).json({ 
      error: 'Internal server error',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
} 