import axios from 'axios';

export default async function handler(req, res) {
  // Handle CORS
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, Authorization'
  );

  // Handle preflight request
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }
  
  try {
    const token = req.headers.authorization;
    
    // Forward the request to the backend
    const backendUrl = 'http://localhost:8000';
    
    console.log(`Forwarding sections request to ${backendUrl}/api/sections/`);
    
    const response = await axios({
      method: req.method,
      url: `${backendUrl}/api/sections/`,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token || '',
      },
      data: req.body,
    });
    
    return res.status(response.status).json(response.data);
  } catch (error) {
    console.error('Error forwarding request to backend:', error.message);
    
    // Return proper error response
    const statusCode = error.response?.status || 500;
    const errorMessage = error.response?.data?.detail || error.message || 'Internal Server Error';
    
    return res.status(statusCode).json({
      error: true,
      message: errorMessage,
    });
  }
} 