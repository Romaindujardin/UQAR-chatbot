import { useState, useEffect } from "react";
import Head from "next/head";
import Link from "next/link";
import { useRouter } from "next/router";
import axios from "axios";
import toast from "react-hot-toast";

export default function Register() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
    first_name: "",
    last_name: "",
    role: "STUDENT",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [apiBaseUrl, setApiBaseUrl] = useState("");

  // Déterminer l'URL de base de l'API
  useEffect(() => {
    // Utiliser l'URL de la variable d'environnement si disponible
    if (process.env.NEXT_PUBLIC_API_URL) {
      setApiBaseUrl(process.env.NEXT_PUBLIC_API_URL);
    } else {
      // Sinon, utiliser l'URL du serveur actuel mais avec le port du backend (8000)
      const currentUrl = window.location.origin;
      const baseUrl = currentUrl.includes('localhost') 
        ? 'http://localhost:8000'
        : currentUrl.replace(/:\d+/, ':8000'); // Remplacer le port actuel par 8000
      setApiBaseUrl(baseUrl);
    }
  }, []);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.username.trim()) {
      newErrors.username = "Le nom d'utilisateur est requis";
    }

    if (!formData.email.trim()) {
      newErrors.email = "L'email est requis";
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = "L'email n'est pas valide";
    }

    if (!formData.password) {
      newErrors.password = "Le mot de passe est requis";
    } else if (formData.password.length < 8) {
      newErrors.password =
        "Le mot de passe doit contenir au moins 8 caractères";
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Les mots de passe ne correspondent pas";
    }

    if (!formData.first_name.trim()) {
      newErrors.first_name = "Le prénom est requis";
    }

    if (!formData.last_name.trim()) {
      newErrors.last_name = "Le nom est requis";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      console.log("Registration attempt:", {
        ...formData,
        password: "[HIDDEN]",
      });

      // Utiliser l'API Next.js plutôt que d'appeler directement le backend
      const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (!response.ok) {
        console.error("Registration error:", data);
        
        // Si l'erreur est un objet, l'afficher comme chaîne
        if (data.detail) {
          const errorMessage = typeof data.detail === 'object' 
            ? JSON.stringify(data.detail) 
            : data.detail;
          setError(errorMessage);
          toast.error(errorMessage);
        } else {
          setError("Une erreur s'est produite lors de l'inscription");
          toast.error("Une erreur s'est produite lors de l'inscription");
        }
        return;
      }

      // Inscription réussie
      toast.success(
        "Compte créé avec succès ! En attente de validation par un administrateur."
      );

      // Redirection vers la page de connexion
      setTimeout(() => {
        router.push("/login");
      }, 2000);
    } catch (err: any) {
      console.error("Registration error:", err);
      const errorMessage = err.message || "Une erreur s'est produite lors de l'inscription";
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));

    // Effacer l'erreur du champ modifié
    if (errors[e.target.name]) {
      setErrors((prev) => ({
        ...prev,
        [e.target.name]: "",
      }));
    }
  };

  return (
    <>
      <Head>
        <title>Inscription - Assistant Éducatif UQAR</title>
        <meta
          name="description"
          content="Créez votre compte pour l'assistant éducatif UQAR"
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
                  d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
                />
              </svg>
            </div>
            <h2 className="text-3xl font-bold text-gray-900">
              Créer un compte
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              Rejoignez l'assistant éducatif UQAR
            </p>
          </div>

          {/* Formulaire d'inscription */}
          <div className="card">
            <div className="card-body">
              <form className="space-y-6" onSubmit={handleSubmit}>
                {error && (
                  <div className="bg-error-50 border border-error-200 text-error-700 px-4 py-3 rounded-md">
                    {typeof error === 'object' ? JSON.stringify(error) : error}
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  <div className="form-group">
                    <label htmlFor="first_name" className="form-label">
                      Prénom
                    </label>
                    <input
                      id="first_name"
                      name="first_name"
                      type="text"
                      required
                      className={`input ${
                        errors.first_name ? "input-error" : ""
                      }`}
                      placeholder="Votre prénom"
                      value={formData.first_name}
                      onChange={handleChange}
                    />
                    {errors.first_name && (
                      <p className="form-error">
                        {typeof errors.first_name === 'object' 
                          ? JSON.stringify(errors.first_name) 
                          : errors.first_name}
                      </p>
                    )}
                  </div>

                  <div className="form-group">
                    <label htmlFor="last_name" className="form-label">
                      Nom
                    </label>
                    <input
                      id="last_name"
                      name="last_name"
                      type="text"
                      required
                      className={`input ${
                        errors.last_name ? "input-error" : ""
                      }`}
                      placeholder="Votre nom"
                      value={formData.last_name}
                      onChange={handleChange}
                    />
                    {errors.last_name && (
                      <p className="form-error">
                        {typeof errors.last_name === 'object' 
                          ? JSON.stringify(errors.last_name) 
                          : errors.last_name}
                      </p>
                    )}
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="username" className="form-label">
                    Nom d'utilisateur
                  </label>
                  <input
                    id="username"
                    name="username"
                    type="text"
                    required
                    className={`input ${errors.username ? "input-error" : ""}`}
                    placeholder="Votre nom d'utilisateur"
                    value={formData.username}
                    onChange={handleChange}
                  />
                  {errors.username && (
                    <p className="form-error">
                      {typeof errors.username === 'object' 
                        ? JSON.stringify(errors.username) 
                        : errors.username}
                    </p>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor="email" className="form-label">
                    Email
                  </label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    required
                    className={`input ${errors.email ? "input-error" : ""}`}
                    placeholder="votre.email@uqar.ca"
                    value={formData.email}
                    onChange={handleChange}
                  />
                  {errors.email && (
                    <p className="form-error">
                      {typeof errors.email === 'object' 
                        ? JSON.stringify(errors.email) 
                        : errors.email}
                    </p>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor="role" className="form-label">
                    Rôle
                  </label>
                  <select
                    id="role"
                    name="role"
                    className="input"
                    value={formData.role}
                    onChange={handleChange}
                  >
                    <option value="STUDENT">Étudiant</option>
                    <option value="TEACHER">Enseignant</option>
                    <option value="SUPER_ADMIN">Super-Admin</option>
                  </select>
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
                    className={`input ${errors.password ? "input-error" : ""}`}
                    placeholder="Votre mot de passe"
                    value={formData.password}
                    onChange={handleChange}
                  />
                  {errors.password && (
                    <p className="form-error">
                      {typeof errors.password === 'object' 
                        ? JSON.stringify(errors.password) 
                        : errors.password}
                    </p>
                  )}
                  <p className="form-help">
                    Au moins 8 caractères avec majuscules, minuscules, chiffres
                    et caractères spéciaux
                  </p>
                </div>

                <div className="form-group">
                  <label htmlFor="confirmPassword" className="form-label">
                    Confirmer le mot de passe
                  </label>
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type="password"
                    required
                    className={`input ${
                      errors.confirmPassword ? "input-error" : ""
                    }`}
                    placeholder="Confirmez votre mot de passe"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                  />
                  {errors.confirmPassword && (
                    <p className="form-error">
                      {typeof errors.confirmPassword === 'object' 
                        ? JSON.stringify(errors.confirmPassword) 
                        : errors.confirmPassword}
                    </p>
                  )}
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
                        Création en cours...
                      </div>
                    ) : (
                      "Créer mon compte"
                    )}
                  </button>
                </div>
              </form>
            </div>

            <div className="card-footer text-center">
              <p className="text-sm text-gray-600">
                Déjà un compte ?{" "}
                <Link
                  href="/login"
                  className="font-medium text-primary-600 hover:text-primary-500"
                >
                  Se connecter
                </Link>
              </p>
            </div>
          </div>

          {/* Informations supplémentaires */}
          <div className="text-center text-xs text-gray-500">
            <p>
              Votre compte sera validé par un administrateur avant activation.
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
