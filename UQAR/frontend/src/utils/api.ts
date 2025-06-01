import axios, { AxiosRequestConfig, AxiosResponse, AxiosError } from "axios";
import { toast } from "react-hot-toast";

// Utiliser le proxy Next.js pour API
const API_URL = "";

// Log de configuration
console.log("Configuration API avec proxy Next.js");

// Créer une instance Axios avec la configuration de base
const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  // Ajouter des options pour résoudre les problèmes de CORS
  withCredentials: true,
  timeout: 100000, // Augmenter le timeout à 100 secondes
});

// Interface pour la file d'attente
interface QueueItem {
  resolve: (value?: any) => void;
  reject: (reason?: any) => void;
}

// Variable pour suivre si un rafraîchissement est en cours
let isRefreshing = false;
// File d'attente pour les requêtes en attente pendant le rafraîchissement
let failedQueue: QueueItem[] = [];

// Fonction pour traiter la file d'attente
const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });

  failedQueue = [];
};

// Intercepteur de requête - ajoute le token d'accès
api.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    const token = localStorage.getItem("access_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Intercepteur de réponse - gère le rafraîchissement des tokens
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & {
      _retry?: boolean;
    };

    // Si l'erreur n'est pas liée à une réponse ou si la requête originale n'existe pas
    if (!error.response || !originalRequest) {
      return Promise.reject(error);
    }

    // Si c'est une erreur 401 (non autorisé) et que la requête n'a pas déjà été tentée
    if (error.response.status === 401 && !originalRequest._retry) {
      // Si une tentative de rafraîchissement est déjà en cours
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return api(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = localStorage.getItem("refresh_token");

        // Si pas de token de rafraîchissement, déconnexion
        if (!refreshToken) {
          logoutUser();
          return Promise.reject(new Error("Pas de token de rafraîchissement"));
        }

        // Tenter de rafraîchir le token
        const response = await axios.post(`${API_URL}/api/auth/refresh`, {
          refresh_token: refreshToken,
        });

        if (response.data.access_token) {
          // Stocker les nouveaux tokens
          localStorage.setItem("access_token", response.data.access_token);
          localStorage.setItem("refresh_token", response.data.refresh_token);

          // Mettre à jour les en-têtes pour la requête originale
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
          }

          // Traiter la file d'attente avec le nouveau token
          processQueue(null, response.data.access_token);

          return api(originalRequest);
        }
      } catch (refreshError) {
        // Échec du rafraîchissement, déconnexion
        processQueue(refreshError, null);
        logoutUser();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// Fonction utilitaire pour déconnecter l'utilisateur
const logoutUser = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");

  // Déclencher un événement pour informer les autres onglets
  localStorage.setItem("session_expired", "true");

  // Notification à l'utilisateur
  toast.error("Votre session a expiré, veuillez vous reconnecter");

  // Rediriger vers la page de connexion
  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
};

export default api;
