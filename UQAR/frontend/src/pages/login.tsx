import { useState, useEffect } from "react";
import Head from "next/head";
import Link from "next/link";
import { useRouter } from "next/router";
import toast from "react-hot-toast";
import api from "../utils/api"; // Importer l'instance api déjà configurée

export default function Login() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    username: "",
    password: "",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      console.log("Login attempt:", formData);

      // Création de l'objet à envoyer directement, sans passer par URLSearchParams
      const requestBody = {
        username: formData.username,
        password: formData.password
      };

      console.log("Sending login request to: /api/auth/login");

      // Utilisation d'un délai d'attente plus long (10 secondes)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);

      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
        signal: controller.signal,
        // Assurez-vous que la requête inclut les cookies
        credentials: 'same-origin'
      });

      // Annuler le délai d'attente
      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Login error details:", errorData);
        throw new Error(errorData.detail || "Erreur de connexion");
      }

      const data = await response.json();

      if (data) {
        // Stocker les tokens et informations utilisateur
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        localStorage.setItem("user", JSON.stringify(data.user));

        console.log("User stored in localStorage:", data.user);

        toast.success(
          `Bienvenue ${
            data.user.full_name || data.user.username
          } !`
        );

        // Redirection selon le rôle
        const userRole = data.user.role;
        console.log("User role:", userRole);

        if (userRole === "SUPER_ADMIN") {
          router.push("/admin/dashboard");
        } else if (userRole === "TEACHER") {
          router.push("/teacher/dashboard");
        } else {
          router.push("/student/dashboard");
        }
      }
    } catch (err: any) {
      console.error("Login error:", err);

      if (err.response?.status === 401) {
        setError("Nom d'utilisateur ou mot de passe incorrect");
      } else if (err.response?.data?.detail) {
        console.error("API Error details:", err.response.data);
        setError(err.response.data.detail);
      } else if (err.code === "ECONNREFUSED") {
        setError(
          "Impossible de se connecter au serveur. Vérifiez que le backend est démarré."
        );
      } else {
        setError("Une erreur s'est produite lors de la connexion");
      }

      toast.error("Échec de la connexion");
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  return (
    <>
      <Head>
        <title>Connexion - Assistant Éducatif UQAR</title>
        <meta
          name="description"
          content="Connectez-vous à l'assistant éducatif UQAR"
        />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          {/* Header */}
          <div className="text-center">
            <div className="mx-auto h-16 w-16 bg-primary-600 rounded-full flex items-center justify-center mb-6">
              <svg
                className="h-8 w-8 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                />
              </svg>
            </div>
            <h2 className="text-3xl font-bold text-gray-900">
              Assistant Éducatif UQAR
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              Connectez-vous à votre compte pour accéder à vos cours
            </p>
          </div>

          {/* Formulaire de connexion */}
          <div className="card">
            <div className="card-body">
              <form className="space-y-6" onSubmit={handleSubmit}>
                {error && (
                  <div className="bg-error-50 border border-error-200 text-error-700 px-4 py-3 rounded-md">
                    {error}
                  </div>
                )}

                <div className="form-group">
                  <label htmlFor="username" className="form-label">
                    Nom d'utilisateur
                  </label>
                  <input
                    id="username"
                    name="username"
                    type="text"
                    required
                    className="input"
                    placeholder="Votre nom d'utilisateur"
                    value={formData.username}
                    onChange={handleChange}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="password" className="form-label">
                    Mot de passe
                  </label>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    required
                    className="input"
                    placeholder="Votre mot de passe"
                    value={formData.password}
                    onChange={handleChange}
                  />
                </div>

                <div>
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? (
                      <div className="flex items-center justify-center">
                        <div className="spinner w-4 h-4 mr-2"></div>
                        Connexion en cours...
                      </div>
                    ) : (
                      "Se connecter"
                    )}
                  </button>
                </div>
              </form>
            </div>

            <div className="card-footer text-center">
              <p className="text-sm text-gray-600">
                Pas encore de compte ?{" "}
                <Link
                  href="/register"
                  className="font-medium text-primary-600 hover:text-primary-500"
                >
                  S'inscrire
                </Link>
              </p>
            </div>
          </div>

          {/* Informations supplémentaires */}
          <div className="text-center text-xs text-gray-500">
            <p>
              En vous connectant, vous acceptez nos conditions d'utilisation et
              notre politique de confidentialité.
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
