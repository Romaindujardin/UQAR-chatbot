import { useState, useEffect } from "react";
import Head from "next/head";
import { useRouter } from "next/router";
import api from "@/utils/api";
import toast from "react-hot-toast";

interface Section {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  document_count: number;
  created_at: string;
}

interface Document {
  id: number;
  original_filename: string;
  file_size: number;
  document_type: string;
  status: string;
  is_vectorized: boolean;
  uploaded_at: string;
  page_count?: number;
  vector_count?: number;
}

interface StudentStats {
  total_exercises: number;
  completed_exercises: number;
  chat_sessions: number;
}

interface ExerciseHistory {
  submission_id: number;
  exercise_id: number;
  exercise_title: string;
  section_name: string;
  score: number;
  percentage: number;
  submitted_at: string;
  questions_count: number;
}

export default function StudentDashboard() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [sections, setSections] = useState<Section[]>([]);
  const [stats, setStats] = useState<StudentStats>({ total_exercises: 0, completed_exercises: 0, chat_sessions: 0 });
  const [exerciseHistory, setExerciseHistory] = useState<ExerciseHistory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [sectionDocuments, setSectionDocuments] = useState<Record<number, Document[] | 'loading' | 'error'>>({});

  useEffect(() => {
    // Vérifier l'authentification
    const token = localStorage.getItem("access_token");
    const userData = localStorage.getItem("user");

    if (!token || !userData) {
      router.push("/login");
      return;
    }

    const parsedUser = JSON.parse(userData);
    if (parsedUser.role !== "STUDENT") {
      toast.error("Accès non autorisé");
      router.push("/login");
      return;
    }

    setUser(parsedUser);
    loadSections();
    loadStudentStats();
    loadExerciseHistory();
  }, [router]);

  const loadExerciseHistory = async () => {
    try {
      console.log("Chargement de l'historique des exercices...");
      
      const token = localStorage.getItem("access_token");
      
      const response = await fetch("/api/students/history?limit=5", {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });
      
      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }
      
      const data = await response.json();
      console.log("Historique récupéré:", data);
      setExerciseHistory(data);
    } catch (error) {
      console.error("Erreur lors du chargement de l'historique:", error);
      // Ne pas afficher d'erreur toast si l'étudiant n'a pas encore fait d'exercices
    }
  };

  const loadStudentStats = async () => {
    try {
      console.log("Chargement des statistiques étudiant...");
      
      const token = localStorage.getItem("access_token");
      
      const response = await fetch("/api/students/stats", {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });
      
      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }
      
      const data = await response.json();
      console.log("Statistiques récupérées:", data);
      setStats(data);
    } catch (error) {
      console.error("Erreur lors du chargement des statistiques:", error);
      toast.error("Erreur lors du chargement des statistiques");
    }
  };

  const loadSections = async () => {
    try {
      console.log("Chargement des sections via proxy...");
      
      // Récupérer le token d'accès
      const token = localStorage.getItem("access_token");
      
      // Effectuer la requête en utilisant fetch directement via notre API route
      const response = await fetch("/api/sections", {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });
      
      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }
      
      const data = await response.json();
      console.log("Réponse des sections:", data);
      setSections(data);
      // Load documents for each section
      if (data && Array.isArray(data)) {
        data.forEach((section: Section) => {
          if (section.is_active) {
            loadDocumentsForSection(section.id);
          }
        });
      }
    } catch (error) {
      console.error("Erreur lors du chargement des sections:", error);
      toast.error("Erreur lors du chargement des sections");
    } finally {
      setIsLoading(false);
    }
  };

  const loadDocumentsForSection = async (sectionId: number) => {
    setSectionDocuments(prev => ({ ...prev, [sectionId]: 'loading' }));
    try {
      const token = localStorage.getItem("access_token");
      const response = await fetch(`/api/documents/section/${sectionId}`, {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });

      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }

      const data = await response.json();
      setSectionDocuments(prev => ({ ...prev, [sectionId]: data as Document[] }));
    } catch (error) {
      console.error(`Erreur lors du chargement des documents pour la section ${sectionId}:`, error);
      setSectionDocuments(prev => ({ ...prev, [sectionId]: 'error' }));
      toast.error(`Erreur lors du chargement des documents pour la section ${sectionId}`);
    }
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    router.push("/login");
  };

  const handleDownload = async (documentId: number, filename: string) => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      toast.error("Authentification requise pour télécharger le fichier.");
      return;
    }

    toast.loading(`Téléchargement de ${filename} en cours...`, { id: 'download-toast' });

    try {
      const response = await fetch(`/api/documents/download/${documentId}`, {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        let errorDetail = "Erreur lors du téléchargement du fichier.";
        try {
          const errorData = await response.json();
          if (errorData && errorData.detail) {
            errorDetail = errorData.detail;
          }
        } catch (e) {
          // Failed to parse JSON, use default error or response status text
          errorDetail = response.statusText || errorDetail;
        }
        toast.error(errorDetail, { id: 'download-toast' });
        return;
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast.success(`Téléchargement de ${filename} terminé.`, { id: 'download-toast' });

    } catch (error) {
      console.error("Erreur de téléchargement:", error);
      toast.error("Une erreur réseau est survenue lors du téléchargement.", { id: 'download-toast' });
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
        <title>Dashboard Étudiant - Assistant Éducatif UQAR</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-6">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Dashboard Étudiant
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
              onClick={() => router.push("/student/dashboard")}
            >
              Dashboard
            </button>
            <button
              className="px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 border-b-2 border-transparent hover:border-gray-300"
              onClick={() => router.push("/student/chat")}
            >
              Assistant IA
            </button>
            <button
              className="px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 border-b-2 border-transparent hover:border-gray-300"
              onClick={() => router.push("/student/exercises")}
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
                        Cours disponibles
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {sections.filter((s) => s.is_active).length}
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
                        <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Sessions de chat
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">{stats.chat_sessions}</dd>
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
                        Exercices complétés
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {stats.completed_exercises}/{stats.total_exercises}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Sections disponibles */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-medium text-gray-900">
                Cours disponibles
              </h3>
            </div>

            <div className="card-body">
              {sections.filter((s) => s.is_active).length === 0 ? (
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
                    Aucun cours disponible
                  </h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Les enseignants n'ont pas encore publié de cours.
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {sections
                    .filter((s) => s.is_active)
                    .map((section) => (
                      <div
                        key={section.id}
                        className="card hover:shadow-md transition-shadow"
                      >
                        <div className="card-body">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="text-lg font-medium text-gray-900">
                              {section.name}
                            </h4>
                            <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                              Disponible
                            </span>
                          </div>

                          {section.description && (
                            <p className="text-sm text-gray-600 mb-4">
                              {section.description}
                            </p>
                          )}

                          <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                            <span>{section.document_count} ressources</span>
                            <span>
                              Créé le{" "}
                              {new Date(section.created_at).toLocaleDateString(
                                "fr-FR"
                              )}
                            </span>
                          </div>

                          <div className="flex space-x-2">
                            <button
                              className="btn-primary flex-1"
                              onClick={() => router.push("/student/chat")}
                            >
                              💬 Assistant IA
                            </button>
                            <button 
                              className="btn-outline"
                              onClick={() => router.push("/student/exercises")}
                            >
                              📝 Exercices
                            </button>
                          </div>

                          {/* Display Documents */}
                          <div className="mt-4 pt-4 border-t border-gray-200">
                            <h5 className="text-sm font-medium text-gray-700 mb-2">
                              Documents:
                            </h5>
                            {sectionDocuments[section.id] === 'loading' && (
                              <p className="text-sm text-gray-500">Chargement des documents...</p>
                            )}
                            {sectionDocuments[section.id] === 'error' && (
                              <p className="text-sm text-red-500">Erreur lors du chargement des documents.</p>
                            )}
                            {Array.isArray(sectionDocuments[section.id]) && (
                              (sectionDocuments[section.id] as Document[]).length > 0 ? (
                                <ul className="space-y-2">
                                  {(sectionDocuments[section.id] as Document[]).map(doc => (
                                    <li key={doc.id} className="flex justify-between items-center py-1 px-2 rounded hover:bg-gray-100">
                                      <span className="text-sm text-gray-700">{doc.original_filename}</span>
                                      <button
                                        onClick={() => handleDownload(doc.id, doc.original_filename)}
                                        className="btn-secondary btn-sm py-1 px-2" // Adjusted padding for smaller button
                                        title={`Télécharger ${doc.original_filename}`}
                                      >
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 inline-block mr-1" viewBox="0 0 20 20" fill="currentColor">
                                          <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                                        </svg>
                                        Télécharger
                                      </button>
                                    </li>
                                  ))}
                                </ul>
                              ) : (
                                <p className="text-sm text-gray-500">Aucun document dans cette section.</p>
                              )
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                </div>
              )}
            </div>
          </div>

          {/* Activité récente */}
          <div className="card mt-8">
            <div className="card-header">
              <h3 className="text-lg font-medium text-gray-900">
                Activité récente
              </h3>
            </div>

            <div className="card-body">
              {exerciseHistory.length === 0 ? (
              <div className="text-center py-8">
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
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">
                    Aucun exercice réalisé
                </h3>
                <p className="mt-1 text-sm text-gray-500">
                    Commencez par faire quelques exercices pour voir votre activité ici.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {exerciseHistory.map((item) => (
                    <div
                      key={item.submission_id}
                      className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex items-center space-x-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          item.percentage >= 80 ? 'bg-green-100 text-green-600' :
                          item.percentage >= 60 ? 'bg-yellow-100 text-yellow-600' :
                          'bg-red-100 text-red-600'
                        }`}>
                          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </div>
                        <div>
                          <h4 className="text-sm font-medium text-gray-900">
                            {item.exercise_title}
                          </h4>
                          <p className="text-sm text-gray-500">
                            {item.section_name} • {item.questions_count} question{item.questions_count > 1 ? 's' : ''}
                          </p>
                          <p className="text-xs text-gray-400">
                            {new Date(item.submitted_at).toLocaleDateString('fr-FR', {
                              day: 'numeric',
                              month: 'long',
                              year: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                </p>
              </div>
                      </div>
                      <div className="text-right">
                        <div className={`text-lg font-semibold ${
                          item.percentage >= 80 ? 'text-green-600' :
                          item.percentage >= 60 ? 'text-yellow-600' :
                          'text-red-600'
                        }`}>
                          {item.percentage.toFixed(0)}%
                        </div>
                        <div className="text-sm text-gray-500">
                          {item.score.toFixed(1)} pts
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Guide de démarrage */}
          <div className="card mt-8 bg-blue-50 border-blue-200">
            <div className="card-body">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg
                    className="h-5 w-5 text-blue-400"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-blue-800">
                    Comment utiliser l'assistant éducatif ?
                  </h3>
                  <div className="mt-2 text-sm text-blue-700">
                    <ul className="list-disc list-inside space-y-1">
                      <li>Sélectionnez un cours dans la liste ci-dessus</li>
                      <li>
                        Utilisez le <strong>Chat RAG</strong> pour poser des
                        questions sur le contenu
                      </li>
                      <li>
                        Pratiquez avec les <strong>exercices</strong> générés
                        automatiquement
                      </li>
                      <li>
                        L'IA répond uniquement basée sur le contenu de chaque
                        cours
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
