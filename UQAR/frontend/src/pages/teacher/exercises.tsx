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
  title?: string; // Titre personnalisé de l'exercice
  questions: Question[];
  created_at: string; // Assuming ISO string date
  updated_at: string; // Assuming ISO string date
}


export default function TeacherExercisesPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null); // Store user info
  const [advancedMode, setAdvancedMode] = useState<boolean>(false);
  const [customPrompt, setCustomPrompt] = useState<string>("");
  const [tempFileContent, setTempFileContent] = useState<string>("");
  const [uploadingTempFile, setUploadingTempFile] = useState<boolean>(false);
  
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
  const [editingQuestionId, setEditingQuestionId] = useState<number | null>(null);
  const [editedQuestion, setEditedQuestion] = useState<Partial<Question>>({});

  // États pour l'édition des titres
  const [editingTitleId, setEditingTitleId] = useState<number | null>(null);
  const [editedTitle, setEditedTitle] = useState<string>("");

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

  const handleDeleteExercise = async (exerciseId: number) => {
    if (!confirm("Êtes-vous sûr de vouloir supprimer cet exercice ? Cette action est irréversible.")) {
      return;
    }

    toast.loading("Suppression de l'exercice en cours...");
    try {
      await api.delete(`/api/exercises/exercises/${exerciseId}`);
      toast.dismiss();
      toast.success("Exercice supprimé avec succès");
      if (selectedSectionId) {
        fetchExercisesForSection(selectedSectionId);
      }
    } catch (error: any) {
      toast.dismiss();
      console.error("Erreur lors de la suppression de l'exercice:", error);
      if (error.response && error.response.data && error.response.data.detail) {
        toast.error(`Erreur: ${error.response.data.detail}`);
      } else {
        toast.error("Échec de la suppression de l'exercice.");
      }
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

  const handleTempFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingTempFile(true);
    const reader = new FileReader();
    reader.onload = () => {
      const text = reader.result as string;
      setTempFileContent(text);
      setUploadingTempFile(false);
    };
    reader.onerror = () => {
      toast.error("Erreur lors de la lecture du fichier temporaire");
      setUploadingTempFile(false);
    };
    reader.readAsText(file);
  };
  
  const handleGenerateExercises = async () => {
    if (selectedSectionId === null) {
      toast.error("Veuillez d'abord sélectionner une section.");
      return;
    }
    setIsGeneratingExercises(true);
    setError(null);
    let options: any;
    if (advancedMode) {
      options = { custom_prompt: customPrompt, temp_content: tempFileContent };
    } else {
      options = { num_questions: numQuestions, difficulty, exercise_type: exerciseType };
    }    console.log("Generating exercises for section:", selectedSectionId, "with options:", options);
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

  const startEdit = (q: Question) => {
    setEditingQuestionId(q.id);
    setEditedQuestion({ ...q });
  };

  const cancelEdit = () => {
    setEditingQuestionId(null);
    setEditedQuestion({});
  };

  const saveEdit = async (exerciseId: number, qId: number) => {
    try {
      toast.loading("Sauvegarde de la question...");
      
      // Envoyer les modifications au backend
      await api.put(`/api/exercises/questions/${qId}`, editedQuestion);
      
      toast.dismiss();
      toast.success("Question modifiée avec succès");
      
      // Mettre à jour l'état local
      setExercises(prev =>
        prev.map(ex =>
          ex.id === exerciseId
            ? {
                ...ex,
                questions: ex.questions.map(q =>
                  q.id === qId ? { ...q, ...editedQuestion } : q
                )
              }
            : ex
        )
      );
      
      cancelEdit();
    } catch (error: any) {
      toast.dismiss();
      console.error("Erreur lors de la modification de la question:", error);
      toast.error(error.response?.data?.detail || "Erreur lors de la modification de la question");
    }
  };

  // Fonctions pour l'édition du titre
  const startTitleEdit = (exercise: Exercise) => {
    setEditingTitleId(exercise.id);
    setEditedTitle(exercise.title || `Exercice #${exercise.id}`);
  };

  const cancelTitleEdit = () => {
    setEditingTitleId(null);
    setEditedTitle("");
  };

  const saveTitleEdit = async (exerciseId: number) => {
    if (!editedTitle.trim()) {
      toast.error("Le titre ne peut pas être vide");
      return;
    }

    try {
      const response = await api.put(`/api/exercises/update-title`, {
        exerciseId: exerciseId,
        title: editedTitle.trim()
      });
      
      toast.success("Titre mis à jour avec succès");
      
      // Mettre à jour l'exercice dans la liste
      setExercises(prev => 
        prev.map(exercise => 
          exercise.id === exerciseId 
            ? { ...exercise, title: editedTitle.trim() }
            : exercise
        )
      );
      
      // Sortir du mode édition
      setEditingTitleId(null);
      setEditedTitle("");
      
    } catch (error: any) {
      console.error("Erreur lors de la mise à jour du titre:", error);
      toast.error(error.response?.data?.detail || "Erreur lors de la mise à jour du titre");
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
                {advancedMode ? (
                    <>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Prompt personnalisé</label>
                        <textarea
                          className="input mt-1 block w-full"
                          rows={4}
                          value={customPrompt}
                          onChange={(e) => setCustomPrompt(e.target.value)}
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Document temporaire</label>
                        <input type="file" className="input mt-1 block w-full" onChange={handleTempFile} />
                        {uploadingTempFile && <p className="text-sm text-gray-500 mt-1">Lecture du fichier...</p>}
                        {!uploadingTempFile && tempFileContent && <p className="text-xs text-gray-500 mt-1">Fichier chargé</p>}
                      </div>
                      <button onClick={() => setAdvancedMode(false)} className="btn-outline w-full">
                        Mode basique
                      </button>
                    </>
                  ) : (
                    <>
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
                      <button onClick={() => setAdvancedMode(true)} className="btn-outline w-full">
                        Options avancées
                      </button>
                    </>
                  )}
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
                            <div className="flex-1">
                                {editingTitleId === exercise.id ? (
                                  <div className="flex items-center space-x-2 mb-2">
                                    <input
                                      type="text"
                                      className="input flex-1"
                                      value={editedTitle}
                                      onChange={(e) => setEditedTitle(e.target.value)}
                                      onKeyPress={(e) => e.key === 'Enter' && saveTitleEdit(exercise.id)}
                                      placeholder="Titre de l'exercice"
                                      autoFocus
                                    />
                                    <button
                                      onClick={() => saveTitleEdit(exercise.id)}
                                      className="btn-secondary btn-sm"
                                      title="Sauvegarder le titre"
                                    >
                                      ✓
                                    </button>
                                    <button
                                      onClick={cancelTitleEdit}
                                      className="btn-outline btn-sm"
                                      title="Annuler"
                                    >
                                      ✕
                                    </button>
                                  </div>
                                ) : (
                                  <div className="flex items-center space-x-2 mb-2">
                                    <h3 className="text-lg font-semibold">
                                      {exercise.title || `Exercice #${exercise.id}`}
                                    </h3>
                                    <button
                                      onClick={() => startTitleEdit(exercise)}
                                      className="text-gray-400 hover:text-gray-600 p-1"
                                      title="Modifier le titre"
                                    >
                                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                        <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                                      </svg>
                                    </button>
                                  </div>
                                )}
                                <div className="flex space-x-4 text-sm text-gray-500">
                                    <span>Statut: <span className={`font-medium ${exercise.status === 'validated' ? 'text-green-600' : exercise.status === 'pending' ? 'text-yellow-600' : 'text-blue-600'}`}>{exercise.status}</span></span>
                                    <span>Créé le: {new Date(exercise.created_at).toLocaleDateString()} {new Date(exercise.created_at).toLocaleTimeString()}</span>
                                    <span>Mis à jour le: {new Date(exercise.updated_at).toLocaleDateString()} {new Date(exercise.updated_at).toLocaleTimeString()}</span>
                                </div>
                            </div>
                            <div className="flex items-center space-x-2">
                                {exercise.status === 'pending' && (
                                    <button 
                                        onClick={() => handleValidateExercise(exercise.id)}
                                        className="btn-secondary btn-sm whitespace-nowrap"
                                    >
                                        Valider cet Exercice
                                    </button>
                                )}
                                <button
                                  onClick={() => handleDeleteExercise(exercise.id)}
                                  className="bg-red-600 hover:bg-red-700 text-white font-medium py-1 px-2 rounded text-sm flex items-center"
                                  title="Supprimer cet exercice"
                                >
                                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                                  </svg>
                                </button>
                            </div>
                          </div>
                          {/* Display Questions */}
                          <div className="mt-4 space-y-3">
                            <h4 className="text-md font-semibold text-gray-700">Questions ({exercise.questions?.length || 0}):</h4>
                            {exercise.questions && exercise.questions.length > 0 ? (
                              exercise.questions.map((question, qIndex) => (
                                <div key={question.id} className="p-3 border rounded-md bg-gray-50 shadow-sm">
                                  {editingQuestionId === question.id ? (
                                    <div className="space-y-2">
                                      <input
                                        type="text"
                                        className="input w-full"
                                        value={editedQuestion.text || ''}
                                        onChange={e => setEditedQuestion({...editedQuestion, text: e.target.value})}
                                      />
                                      {question.question_type === 'mcq' && (
                                        <textarea
                                          className="input w-full"
                                          value={(editedQuestion.options || question.options || []).join('\n')}
                                          onChange={e => setEditedQuestion({...editedQuestion, options: e.target.value.split('\n')})}
                                        />
                                      )}
                                      <input
                                        type="text"
                                        className="input w-full"
                                        value={editedQuestion.correct_answer || ''}
                                        onChange={e => setEditedQuestion({...editedQuestion, correct_answer: e.target.value})}
                                      />
                                      <textarea
                                        className="input w-full"
                                        value={editedQuestion.explanation || ''}
                                        onChange={e => setEditedQuestion({...editedQuestion, explanation: e.target.value})}
                                      />
                                      <div className="flex space-x-2">
                                        <button className="btn-secondary btn-sm" onClick={() => saveEdit(exercise.id, question.id)}>Sauvegarder</button>
                                        <button className="btn-outline btn-sm" onClick={cancelEdit}>Annuler</button>
                                      </div>
                                    </div>
                                  ) : (
                                    <>
                                  <p className="font-medium text-gray-800">Q{qIndex + 1}: {question.text}</p>
                                  <p className="text-xs text-gray-500 uppercase tracking-wider mt-1">Type: {question.question_type}</p>
                                  {question.question_type === 'mcq' && question.options && (
                                    <div className="mt-2">
                                      <p className="text-sm font-medium text-gray-700">Options:</p>
                                      <ul className="list-disc pl-5 mt-1 space-y-1">
                                        {question.options.map((option, oIndex) => (
                                              <li key={oIndex} className={`text-sm ${option === question.correct_answer ? 'font-semibold text-green-700' : 'text-gray-700'}`}>{option}{option === question.correct_answer && <span className="text-green-600 ml-2">(Correct)</span>}</li>
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
                                      <div className="mt-2">
                                        <button className="btn-outline btn-sm" onClick={() => startEdit(question)}>Modifier</button>
                                      </div>
                                    </>
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