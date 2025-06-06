import { useState, useEffect } from "react";
import Head from "next/head";
import { useRouter } from "next/router";
import axios from "axios";
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

export default function TeacherDocuments() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [sections, setSections] = useState<Section[]>([]);
  const [selectedSection, setSelectedSection] = useState<Section | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(true);

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

  useEffect(() => {
    if (selectedSection) {
      loadDocuments(selectedSection.id);
    }
  }, [selectedSection]);

  const loadSections = async () => {
    try {
      setIsLoading(true);

      const response = await api.get("/api/sections/");

      setSections(response.data);

      if (response.data && response.data.length > 0) {
        setSelectedSection(response.data[0]);
        await loadDocuments(response.data[0].id);
      }
    } catch (error: any) {
      console.error("Erreur lors du chargement des sections:", error);
      toast.error("Erreur lors du chargement des sections");
    } finally {
      setIsLoading(false);
    }
  };

  const loadDocuments = async (sectionId: number) => {
    try {
      setIsLoadingDocuments(true);

      const response = await api.get(`/api/documents/section/${sectionId}`);

      setDocuments(response.data);
      setIsLoadingDocuments(false);
    } catch (error: any) {
      console.error("Erreur lors du chargement des documents:", error);
      toast.error("Erreur lors du chargement des documents");
      setIsLoadingDocuments(false);
    }
  };

  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const files = event.target.files;
    if (!files || files.length === 0 || !selectedSection) {
      return;
    }

    const formData = new FormData();
    formData.append("file", files[0]);
    formData.append("section_id", selectedSection.id.toString());

    setIsUploading(true);
    setUploadProgress(0);

    try {
      // Utiliser axios directement pour bénéficier du suivi de progression
      // Mais configurer le token d'autorisation
      const token = localStorage.getItem("access_token");

      const response = await axios.post(
        `${
          process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080"
        }/api/documents/upload`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
            Authorization: `Bearer ${token}`,
          },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / (progressEvent.total || 100)
            );
            setUploadProgress(percentCompleted);
          },
        }
      );

      console.log("Document uploaded:", response.data);
      toast.success("Document uploadé avec succès");

      await loadDocuments(selectedSection.id);
    } catch (error: any) {
      console.error("Erreur lors de l'upload du document:", error);

      if (error.response) {
        console.error("Response data:", error.response.data);

        if (error.response.data && error.response.data.detail) {
          toast.error(`Erreur: ${error.response.data.detail}`);
        } else {
          toast.error(`Erreur ${error.response.status}: Échec de l'upload`);
        }
      } else {
        toast.error("Erreur lors de l'upload du document");
      }
    } finally {
      setIsUploading(false);
      setUploadProgress(0);

      event.target.value = "";
    }
  };

  const handleDeleteDocument = async (documentId: number) => {
    if (!confirm("Êtes-vous sûr de vouloir supprimer ce document ?")) {
      return;
    }

    try {
      await api.delete(`/api/documents/${documentId}`);

      toast.success("Document supprimé avec succès");

      if (selectedSection) {
        await loadDocuments(selectedSection.id);
      }
    } catch (error: any) {
      console.error("Erreur lors de la suppression:", error);

      if (error.response && error.response.data && error.response.data.detail) {
        toast.error(`Erreur: ${error.response.data.detail}`);
      } else {
        toast.error("Erreur lors de la suppression du document");
      }
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) {
      return bytes + " bytes";
    } else if (bytes < 1024 * 1024) {
      return (bytes / 1024).toFixed(2) + " KB";
    } else {
      return (bytes / (1024 * 1024)).toFixed(2) + " MB";
    }
  };

  const getStatusBadgeClass = (status: string): string => {
    switch (status) {
      case "uploaded":
        return "bg-blue-100 text-blue-800";
      case "processing":
        return "bg-yellow-100 text-yellow-800";
      case "processed":
        return "bg-green-100 text-green-800";
      case "error":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusLabel = (status: string): string => {
    switch (status) {
      case "uploaded":
        return "Uploadé";
      case "processing":
        return "En traitement";
      case "processed":
        return "Traité";
      case "error":
        return "Erreur";
      default:
        return status;
    }
  };

  const getDocumentTypeIcon = (type: string): JSX.Element => {
    switch (type) {
      case "pdf":
        return (
          <svg
            className="w-5 h-5 text-red-500"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M9 2a2 2 0 00-2 2v8a2 2 0 002 2h6a2 2 0 002-2V6.414A2 2 0 0016.414 5L14 2.586A2 2 0 0012.586 2H9z" />
            <path d="M3 8a2 2 0 012-2h2a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />
          </svg>
        );
      case "docx":
        return (
          <svg
            className="w-5 h-5 text-blue-500"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M9 2a2 2 0 00-2 2v8a2 2 0 002 2h6a2 2 0 002-2V6.414A2 2 0 0016.414 5L14 2.586A2 2 0 0012.586 2H9z" />
            <path d="M3 8a2 2 0 012-2h2a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />
          </svg>
        );
      case "pptx":
        return (
          <svg
            className="w-5 h-5 text-orange-500"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M9 2a2 2 0 00-2 2v8a2 2 0 002 2h6a2 2 0 002-2V6.414A2 2 0 0016.414 5L14 2.586A2 2 0 0012.586 2H9z" />
            <path d="M3 8a2 2 0 012-2h2a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />
          </svg>
        );
      default:
        return (
          <svg
            className="w-5 h-5 text-gray-500"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M9 2a2 2 0 00-2 2v8a2 2 0 002 2h6a2 2 0 002-2V6.414A2 2 0 0016.414 5L14 2.586A2 2 0 0012.586 2H9z" />
            <path d="M3 8a2 2 0 012-2h2a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />
          </svg>
        );
    }
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    router.push("/login");
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
        <title>Gestion des Documents - Assistant Éducatif UQAR</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-6">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Gestion des Documents
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
                className="px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 border-b-2 border-transparent hover:border-gray-300"
                onClick={() => router.push("/teacher/dashboard")}
              >
                Dashboard
              </button>
              <button
                className="px-3 py-2 text-sm font-medium text-primary-600 border-b-2 border-primary-600"
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
          {/* Section Selector */}
          <div className="card mb-6">
            <div className="card-body">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between">
                <div className="mb-4 md:mb-0">
                  <label
                    htmlFor="section-select"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Sélectionner une section
                  </label>
                  <select
                    id="section-select"
                    className="input"
                    value={selectedSection?.id || ""}
                    onChange={(e) => {
                      const sectionId = parseInt(e.target.value);
                      const section = sections.find((s) => s.id === sectionId);
                      setSelectedSection(section || null);
                    }}
                  >
                    <option value="" disabled>
                      Choisir une section
                    </option>
                    {sections.map((section) => (
                      <option key={section.id} value={section.id}>
                        {section.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Upload de document
                  </label>
                  <div className="flex">
                    <label className="btn-primary cursor-pointer">
                      <span>Choisir un fichier</span>
                      <input
                        type="file"
                        className="hidden"
                        accept=".pdf,.docx,.pptx,.txt,.md"
                        onChange={handleFileUpload}
                        disabled={isUploading || !selectedSection}
                      />
                    </label>
                  </div>
                  {isUploading && (
                    <div className="mt-2">
                      <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div
                          className="bg-primary-600 h-2.5 rounded-full"
                          style={{ width: `${uploadProgress}%` }}
                        ></div>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        Upload en cours: {uploadProgress}%
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Documents List */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-medium text-gray-900">
                Documents {selectedSection ? `- ${selectedSection.name}` : ""}
              </h3>
            </div>

            <div className="card-body">
              {!selectedSection ? (
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
                      d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"
                    />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">
                    Veuillez sélectionner une section
                  </h3>
                </div>
              ) : documents.length === 0 ? (
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
                      d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"
                    />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">
                    Aucun document dans cette section
                  </h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Commencez par uploader un document.
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Document
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Type
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Taille
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Statut
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Vectorisé
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Date d'upload
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {documents.map((doc) => (
                        <tr key={doc.id}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              {getDocumentTypeIcon(doc.document_type)}
                              <div className="ml-4">
                                <div className="text-sm font-medium text-gray-900">
                                  {doc.original_filename}
                                </div>
                                {doc.page_count && (
                                  <div className="text-sm text-gray-500">
                                    {doc.page_count} pages
                                  </div>
                                )}
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">
                              {doc.document_type.toUpperCase()}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">
                              {formatFileSize(doc.file_size)}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span
                              className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadgeClass(
                                doc.status
                              )}`}
                            >
                              {getStatusLabel(doc.status)}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">
                              {doc.is_vectorized ? (
                                <span className="text-green-600">
                                  Oui ({doc.vector_count} chunks)
                                </span>
                              ) : (
                                <span className="text-red-600">Non</span>
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">
                              {new Date(doc.uploaded_at).toLocaleDateString(
                                "fr-FR"
                              )}
                            </div>
                            <div className="text-sm text-gray-500">
                              {new Date(doc.uploaded_at).toLocaleTimeString(
                                "fr-FR"
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <button
                              onClick={() => handleDeleteDocument(doc.id)}
                              className="text-red-600 hover:text-red-900"
                            >
                              Supprimer
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
