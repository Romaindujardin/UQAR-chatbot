import React, { useState, useEffect } from "react";
import Head from "next/head";
import { useRouter } from "next/router";
import api from "@/utils/api"; // Assuming api.ts is in src/utils
import toast from "react-hot-toast";

// Use a more detailed Section interface based on documents.tsx
interface Section {
  id: number;
  name: string;
  description?: string;
  is_active?: boolean; // Assuming this might be relevant from backend Section model
  document_count?: number;
  created_at?: string;
  // Add other fields if known from backend's SectionResponse or Section model
  // For example: teacher_id, course_id, etc.
}



// Defined interfaces for Exercise and Question
interface Question {
  id: number;
  text: string;
  question_type: string; // 'mcq' or 'open_ended'
  options?: string[];
  correct_answer?: string;
  explanation?: string;
  // created_at and updated_at could be added if needed for display
}

interface Exercise {
  id: number;
  section_id: number;
  status: string; // 'pending', 'validated', 'generating'
  questions: Question[];
  created_at: string; // Assuming ISO string date
  updated_at: string; // Assuming ISO string date
}


export default function TeacherExercisesPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null); // Store user info
  
  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    router.push("/login");
  };
  const [sections, setSections] = useState<Section[]>([]);
  const [selectedSectionId, setSelectedSectionId] = useState<number | null>(null);
  
  const [numQuestions, setNumQuestions] = useState<number>(5);
  const [difficulty, setDifficulty] = useState<string>("medium");
  const [exerciseType, setExerciseType] = useState<string>("mcq");
  
  const [exercises, setExercises] = useState<Exercise[]>([]); // Using updated Exercise[] type
  
  const [isLoadingSections, setIsLoadingSections] = useState<boolean>(true);
  const [isGeneratingExercises, setIsGeneratingExercises] = useState<boolean>(false);
  const [isLoadingExercises, setIsLoadingExercises] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    const userData = localStorage.getItem("user");

    if (!token || !userData) {
      toast.error("Veuillez vous connecter.");
      router.push("/login");
      return;
    }

    const parsedUser = JSON.parse(userData);
    if (parsedUser.role !== "TEACHER") {
      toast.error("Accès non autorisé. Cette page est réservée aux enseignants.");
      router.push("/login"); // Or a teacher dashboard if appropriate
      return;
    }
    setUser(parsedUser);
    fetchSections();
  }, [router]);

  const fetchSections = async () => {
    setIsLoadingSections(true);
    setError(null);
    try {
      // Assuming endpoint returns sections for the logged-in teacher
      // The backend /api/sections might need to be filtered by teacher_id
      const response = await api.get("/api/sections/"); 
      if (response.data && response.data.length > 0) {
        setSections(response.data);
        // Optionally, select the first section by default
        // setSelectedSectionId(response.data[0].id); 
      } else {
        setSections([]);
        toast.success("Aucune section trouvée pour cet enseignant.");
      }
    } catch (err: any) {
      console.error("Failed to fetch sections:", err);
      setError("Erreur lors du chargement des sections.");
      toast.error(err.response?.data?.detail || "Erreur lors du chargement des sections.");
    } finally {
      setIsLoadingSections(false);
    }
  };

  // Placeholder: Fetch exercises for the selected section
  useEffect(() => {
    if (selectedSectionId !== null) {
      fetchExercisesForSection(selectedSectionId);
    } else {
      setExercises([]); // Clear exercises if no section is selected
    }
  }, [selectedSectionId]);

  const fetchExercisesForSection = async (sectionId: number) => {
    setIsLoadingExercises(true);
    try {
      const response = await api.get(`/api/exercises/sections/${sectionId}/exercises`);
      setExercises(response.data);
    } catch (err: any) {
      console.error(`Failed to fetch exercises for section ${sectionId}:`, err);
      toast.error(err.response?.data?.detail || `Erreur lors du chargement des exercices pour la section.`);
      setExercises([]); // Clear exercises on error
    } finally {
      setIsLoadingExercises(false);
    }
  };
  
  const handleGenerateExercises = async () => {
    if (selectedSectionId === null) {
      toast.error("Veuillez d'abord sélectionner une section.");
      return;
    }
    setIsGeneratingExercises(true);
    setError(null);
    const options = { num_questions: numQuestions, difficulty, exercise_type: exerciseType };
    console.log("Generating exercises for section:", selectedSectionId, "with options:", options);
    toast(`Génération d'exercices pour la section ${selectedSectionId}...`);

    try {
      // Backend endpoint: POST /api/exercises/sections/{section_id}/exercises/generate
      const response = await api.post(`/api/exercises/sections/${selectedSectionId}/exercises/generate`, options);
      toast.success("Exercices générés avec succès!");
      // Add the new exercise to the list or refresh the list
      setExercises(prev => [response.data, ...prev.filter(ex => ex.id !== response.data.id)]); // Basic update
      // A more robust way would be to re-fetch or ensure the response matches the Exercise[] structure.
      // For now, let's just re-fetch.
      fetchExercisesForSection(selectedSectionId);

    } catch (err: any) {
      console.error("Failed to generate exercises:", err);
      setError(err.response?.data?.detail || "Erreur lors de la génération des exercices.");
      toast.error(err.response?.data?.detail || "Erreur lors de la génération des exercices.");
    } finally {
      setIsGeneratingExercises(false);
    }
  };

  const handleValidateExercise = async (exerciseId: number) => {
    toast(`Validation de l'exercice ${exerciseId}...`);
    try {
        // PUT /api/exercises/exercises/{exercise_id}/validate
        const response = await api.put(`/api/exercises/exercises/${exerciseId}/validate`, {
          validation_notes: "Exercice validé par l'enseignant"
        });
        toast.success(`Exercice ${exerciseId} validé avec succès!`);
        // Update local state
        setExercises(prevExercises => 
            prevExercises.map(ex => ex.id === exerciseId ? {...ex, status: "validated"} : ex)
        );
    } catch (err: any) {
        console.error(`Failed to validate exercise ${exerciseId}:`, err);
        toast.error(err.response?.data?.detail || `Erreur lors de la validation de l'exercice ${exerciseId}.`);
    }
  };


  const selectedSectionName = sections.find(s => s.id === selectedSectionId)?.name || "N/A";

  if (!user) { // Initial check before useEffect runs for auth
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
        <title>Gestion des Exercices - Assistant Éducatif UQAR</title>
      </Head>
      <div className="min-h-screen bg-gray-100">
        {/* Header (Simplified - can be expanded or use a layout component) */}
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
                className="px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 border-b-2 border-transparent hover:border-gray-300"
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
                className="px-3 py-2 text-sm font-medium text-primary-600 border-b-2 border-primary-600"

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
              <label htmlFor="section-select" className="block text-sm font-medium text-gray-700 mb-1">
                Sélectionner une Section
              </label>
              {isLoadingSections ? (
                <p>Chargement des sections...</p>
              ) : sections.length === 0 ? (
                 <p className="text-sm text-gray-500">Aucune section disponible. Veuillez d'abord créer une section.</p>
              ) :(
                <select
                  id="section-select"
                  className="input w-full md:w-1/2"
                  value={selectedSectionId || ""}
                  onChange={(e) => setSelectedSectionId(e.target.value ? parseInt(e.target.value) : null)}
                >
                  <option value="">-- Choisir une section --</option>
                  {sections.map((section) => (
                    <option key={section.id} value={section.id}>
                      {section.name}
                    </option>
                  ))}
                </select>
              )}
              {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
            </div>
          </div>

          {selectedSectionId && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Exercise Generation Form */}
              <div className="md:col-span-1 card">
                <div className="card-header">
                  <h2 className="text-xl font-semibold">Générer des Exercices</h2>
                  <p className="text-sm text-gray-500">Pour la section: <span className="font-medium">{selectedSectionName}</span></p>
                </div>
                <div className="card-body space-y-4">
                  <div>
                    <label htmlFor="num-questions" className="block text-sm font-medium text-gray-700">
                      Nombre de Questions
                    </label>
                    <input
                      type="number"
                      id="num-questions"
                      className="input mt-1 block w-full"
                      value={numQuestions}
                      onChange={(e) => setNumQuestions(parseInt(e.target.value))}
                      min="1"
                      max="20"
                    />
                  </div>
                  <div>
                    <label htmlFor="difficulty" className="block text-sm font-medium text-gray-700">
                      Difficulté
                    </label>
                    <select
                      id="difficulty"
                      className="input mt-1 block w-full"
                      value={difficulty}
                      onChange={(e) => setDifficulty(e.target.value)}
                    >
                      <option value="easy">Facile</option>
                      <option value="medium">Moyen</option>
                      <option value="hard">Difficile</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="exercise-type" className="block text-sm font-medium text-gray-700">
                      Type d'Exercice
                    </label>
                    <select
                      id="exercise-type"
                      className="input mt-1 block w-full"
                      value={exerciseType}
                      onChange={(e) => setExerciseType(e.target.value)}
                    >
                      <option value="mcq">Choix Multiple (QCM)</option>
                      <option value="open_ended">Question Ouverte</option>
                    </select>
                  </div>
                  <button
                    onClick={handleGenerateExercises}
                    className="btn-primary w-full"
                    disabled={isGeneratingExercises}
                  >
                    {isGeneratingExercises ? "Génération en cours..." : "Générer les Exercices"}
                  </button>
                </div>
              </div>

              {/* Display Area for Exercises */}
              <div className="md:col-span-2 card">
                <div className="card-header">
                  <h2 className="text-xl font-semibold">Exercices Générés</h2>
                  <p className="text-sm text-gray-500">Pour la section: <span className="font-medium">{selectedSectionName}</span></p>
                </div>
                <div className="card-body">
                  {isLoadingExercises ? (
                    <p>Chargement des exercices...</p>
                  ) : exercises.length === 0 ? (
                    <p className="text-gray-500">Aucun exercice généré pour cette section ou aucun exercice trouvé. Utilisez le formulaire pour en générer.</p>
                  ) : (
                    <ul className="space-y-4">
                      {exercises.map((exercise) => (
                        <li key={exercise.id} className="p-4 border rounded-md shadow-sm bg-white">
                          <div className="flex justify-between items-center">
                            <div>
                                <h3 className="text-lg font-semibold">Exercice #{exercise.id}</h3>
                                <div className="flex space-x-4 text-sm text-gray-500 mt-1">
                                    <span>Statut: <span className={`font-medium ${exercise.status === 'validated' ? 'text-green-600' : exercise.status === 'pending' ? 'text-yellow-600' : 'text-blue-600'}`}>{exercise.status}</span></span>
                                    <span>Créé le: {new Date(exercise.created_at).toLocaleDateString()} {new Date(exercise.created_at).toLocaleTimeString()}</span>
                                    <span>Mis à jour le: {new Date(exercise.updated_at).toLocaleDateString()} {new Date(exercise.updated_at).toLocaleTimeString()}</span>
                                </div>
                            </div>
                            {exercise.status === 'pending' && (
                                <button 
                                    onClick={() => handleValidateExercise(exercise.id)}
                                    className="btn-secondary btn-sm"
                                >
                                    Valider cet Exercice
                                </button>
                            )}
                          </div>
                          {/* Display Questions */}
                          <div className="mt-4 space-y-3">
                            <h4 className="text-md font-semibold text-gray-700">Questions ({exercise.questions?.length || 0}):</h4>
                            {exercise.questions && exercise.questions.length > 0 ? (
                              exercise.questions.map((question, qIndex) => (
                                <div key={question.id} className="p-3 border rounded-md bg-gray-50 shadow-sm">
                                  <p className="font-medium text-gray-800">Q{qIndex + 1}: {question.text}</p>
                                  <p className="text-xs text-gray-500 uppercase tracking-wider mt-1">Type: {question.question_type}</p>
                                  {question.question_type === 'mcq' && question.options && (
                                    <div className="mt-2">
                                      <p className="text-sm font-medium text-gray-700">Options:</p>
                                      <ul className="list-disc pl-5 mt-1 space-y-1">
                                        {question.options.map((option, oIndex) => (
                                          <li key={oIndex} className={`text-sm ${option === question.correct_answer ? 'font-semibold text-green-700' : 'text-gray-700'}`}>
                                            {option}
                                            {option === question.correct_answer && <span className="text-green-600 ml-2">(Correct)</span>}
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                   {question.question_type === 'mcq' && !question.correct_answer && (
                                     <p className="text-sm text-orange-600 mt-1">Note: La réponse correcte n'est pas définie pour ce QCM.</p>
                                   )}
                                  {question.explanation && (
                                    <div className="mt-2">
                                      <p className="text-sm font-medium text-gray-700">Explication:</p>
                                      <p className="text-sm text-gray-600 bg-blue-50 p-2 rounded">{question.explanation}</p>
                                    </div>
                                  )}
                                  {!question.explanation && (
                                     <p className="text-sm text-gray-500 mt-1">Aucune explication fournie.</p>
                                  )}
                                </div>
                              ))
                            ) : (
                              <p className="text-sm text-gray-500">Aucune question dans cet exercice.</p>
                            )}
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </>
  );
}
