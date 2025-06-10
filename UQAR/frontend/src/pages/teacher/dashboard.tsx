import { useState, useEffect } from "react";
import Head from "next/head";
import { useRouter } from "next/router";
import toast from "react-hot-toast";
import api from "@/utils/api";

interface Section {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  document_count: number;
  created_at: string;
}

export default function TeacherDashboard() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [sections, setSections] = useState<Section[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newSection, setNewSection] = useState({
    name: "",
    description: "",
  });

  useEffect(() => {
    // Vérifier l'authentification
    const token = localStorage.getItem("access_token");
    const userData = localStorage.getItem("user");

    if (!token || !userData) {
      router.push("/login");
      return;
    }

    const parsedUser = JSON.parse(userData);
    if (parsedUser.role !== "TEACHER") {
      toast.error("Accès non autorisé");
      router.push("/login");
      return;
    }

    setUser(parsedUser);
    loadSections();
  }, [router]);

  const loadSections = async () => {
    try {
      setIsLoading(true);

      const response = await api.get("/api/sections/");

      console.log("Sections loaded successfully:", response.data);
      setSections(response.data);
    } catch (error: any) {
      console.error("Erreur lors du chargement des sections:", error);

      if (error.response) {
        console.error("Response data:", error.response.data);
        console.error("Response status:", error.response.status);

        if (error.response.data && error.response.data.detail) {
          toast.error(`Erreur: ${error.response.data.detail}`);
        } else {
          toast.error(
            `Erreur ${error.response.status}: Échec du chargement des sections`
          );
        }
      } else if (error.request) {
        console.error("No response received:", error.request);
        toast.error(
          "Aucune réponse du serveur. Vérifiez votre connexion ou le statut du backend."
        );
      } else {
        console.error("Error message:", error.message);
        toast.error("Erreur lors du chargement des sections");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const createSection = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!newSection.name.trim()) {
      toast.error("Le nom de la section est requis");
      return;
    }

    try {
      console.log("Creating section with data:", newSection);

      const response = await api.post("/api/sections/", newSection);

      console.log("Section created successfully:", response.data);
      toast.success("Section créée avec succès");
      setShowCreateModal(false);
      setNewSection({ name: "", description: "" });
      loadSections();
    } catch (error: any) {
      console.error("Erreur lors de la création:", error);

      if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        console.error("Response data:", error.response.data);
        console.error("Response status:", error.response.status);
        console.error("Response headers:", error.response.headers);

        if (error.response.data && error.response.data.detail) {
          toast.error(`Erreur: ${error.response.data.detail}`);
        } else {
          toast.error(
            `Erreur ${error.response.status}: Échec de la création de la section`
          );
        }
      } else if (error.request) {
        // The request was made but no response was received
        console.error("No response received:", error.request);
        toast.error(
          "Aucune réponse du serveur. Vérifiez votre connexion ou le statut du backend."
        );
      } else {
        // Something happened in setting up the request that triggered an Error
        console.error("Error message:", error.message);
        toast.error("Erreur lors de la création de la section");
      }
    }
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    router.push("/login");
  };

  const handleDeleteSection = async (sectionId: number) => {
    if (
      !confirm(
        "Êtes-vous sûr de vouloir supprimer cette section et tous ses documents et exercices associés ? Cette action est irréversible."
      )
    ) {
      return;
    }

    toast.loading("Suppression de la section en cours...");
    try {
      await api.delete(`/api/sections/${sectionId}`);
      toast.dismiss();
      toast.success("Section supprimée avec succès");
      loadSections(); // Reload sections to reflect the deletion
    } catch (error: any) {
      toast.dismiss();
      console.error("Erreur lors de la suppression de la section:", error);
      if (error.response && error.response.data && error.response.data.detail) {
        toast.error(`Erreur: ${error.response.data.detail}`);
      } else {
        toast.error("Échec de la suppression de la section.");
      }
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="spinner w-8 h-8 mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <Head>
        <title>Dashboard Enseignant - Assistant Éducatif UQAR</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-6">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Dashboard Enseignant
                </h1>
                <p className="text-gray-600">
                  Bienvenue, {user?.full_name || user?.username}
                </p>
              </div>
              <div className="flex space-x-4">
                <button onClick={logout} className="btn-outline">
                  Déconnexion
                </button>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 border-t border-gray-200">
            <nav className="flex space-x-8">
              <button
                className="px-3 py-2 text-sm font-medium text-primary-600 border-b-2 border-primary-600"
                onClick={() => router.push("/teacher/dashboard")}
              >
                Dashboard
              </button>
              <button
                className="px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 border-b-2 border-transparent hover:border-gray-300"
                onClick={() => router.push("/teacher/documents")}
              >
                Documents
              </button>
              <button
                className="px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 border-b-2 border-transparent hover:border-gray-300"
                onClick={() => router.push("/teacher/exercises")}
              >
                Exercices
              </button>
            </nav>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="card">
              <div className="card-body">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                      <svg
                        className="w-5 h-5 text-white"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg>
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Sections de cours
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {sections.length}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-body">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                      <svg
                        className="w-5 h-5 text-white"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                        <path
                          fillRule="evenodd"
                          d="M4 5a2 2 0 012-2v1a1 1 0 001 1h6a1 1 0 001-1V3a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Documents uploadés
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {sections.reduce(
                          (total, section) => total + section.document_count,
                          0
                        )}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-body">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                      <svg
                        className="w-5 h-5 text-white"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Sections actives
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {sections.filter((s) => s.is_active).length}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Sections */}
          <div className="card">
            <div className="card-header">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium text-gray-900">
                  Mes sections de cours
                </h3>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="btn-primary"
                >
                  Créer une section
                </button>
              </div>
            </div>

            <div className="card-body">
              {sections.length === 0 ? (
                <div className="text-center py-12">
                  <svg
                    className="mx-auto h-12 w-12 text-gray-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                    />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">
                    Aucune section
                  </h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Commencez par créer votre première section de cours.
                  </p>
                  <div className="mt-6">
                    <button
                      onClick={() => setShowCreateModal(true)}
                      className="btn-primary"
                    >
                      Créer une section
                    </button>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {sections.map((section) => (
                    <div
                      key={section.id}
                      className="card hover:shadow-md transition-shadow flex flex-col" // Added flex flex-col
                    >
                      <div className="card-body flex flex-col flex-grow"> {/* Added flex flex-col flex-grow */}
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="text-lg font-medium text-gray-900 truncate" title={section.name}>
                            {section.name}
                          </h4>
                          <span
                            className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              section.is_active
                                ? "bg-green-100 text-green-800"
                                : "bg-gray-100 text-gray-800"
                            }`}
                          >
                            {section.is_active ? "Active" : "Inactive"}
                          </span>
                        </div>

                        {section.description && (
                          <p className="text-sm text-gray-600 mb-4 flex-grow"> {/* Added flex-grow */}
                            {section.description}
                          </p>
                        )}
                        {!section.description && <div className="flex-grow"></div>} {/* Spacer if no description */}

                        <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                          <span>{section.document_count} documents</span>
                          <span>
                            {new Date(section.created_at).toLocaleDateString(
                              "fr-FR"
                            )}
                          </span>
                        </div>

                        <div className="flex space-x-2 mt-auto"> {/* Buttons at the bottom */}
                          <button 
                            onClick={() => router.push(`/teacher/section/${section.id}`)} 
                            className="btn-primary py-2 px-3 text-sm flex-1 whitespace-nowrap"
                          >
                            Gérer
                          </button>
                          <button 
                            onClick={() => router.push(`/teacher/documents?section_id=${section.id}`)} 
                            className="btn-outline py-2 px-3 text-sm flex-1 whitespace-nowrap"
                          >
                            Documents
                          </button>
                          <button
                            onClick={() => handleDeleteSection(section.id)}
                            className="bg-red-600 hover:bg-red-700 text-white py-2 px-3 text-sm rounded-md shadow-sm flex items-center justify-center"
                            title="Supprimer la section"
                          >
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                            </svg>
                            {/* Text "Supprimer" removed to make it an icon button */}
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </main>
      </div>

      {/* Modal de création */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Créer une nouvelle section
              </h3>

              <form onSubmit={createSection}>
                <div className="form-group">
                  <label htmlFor="name" className="form-label">
                    Nom de la section
                  </label>
                  <input
                    id="name"
                    type="text"
                    required
                    className="input"
                    placeholder="Ex: Mathématiques, Physique..."
                    value={newSection.name}
                    onChange={(e) =>
                      setNewSection((prev) => ({
                        ...prev,
                        name: e.target.value,
                      }))
                    }
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="description" className="form-label">
                    Description (optionnelle)
                  </label>
                  <textarea
                    id="description"
                    className="input"
                    rows={3}
                    placeholder="Description de la section..."
                    value={newSection.description}
                    onChange={(e) =>
                      setNewSection((prev) => ({
                        ...prev,
                        description: e.target.value,
                      }))
                    }
                  />
                </div>

                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="btn-outline"
                  >
                    Annuler
                  </button>
                  <button type="submit" className="btn-primary">
                    Créer
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
