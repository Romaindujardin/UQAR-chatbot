import React, { useState, useEffect } from "react";
import Head from "next/head";
import { useRouter } from "next/router";
import api from "@/utils/api";
import toast from "react-hot-toast";

interface Question {
  id: number;
  text: string;
  question_type: string;
  options?: string[];
  correct_answer?: string;
  explanation?: string;
  points: number;
}

interface Exercise {
  id: number;
  section_id: number;
  status: string;
  questions: Question[];
  created_at: string;
  updated_at: string;
}

interface Section {
  id: number;
  name: string;
  description?: string;
  allow_exercises?: boolean;
}

interface AnswerFeedback {
  question_id: number;
  is_correct: boolean;
  feedback: string;
  earned_points: number;
}

interface ExerciseResult {
  exercise_id: number;
  total_points: number;
  earned_points: number;
  percentage: number;
  feedback: AnswerFeedback[];
  overall_feedback: string;
}

export default function StudentExercisesPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [sections, setSections] = useState<Section[]>([]);
  const [selectedSectionId, setSelectedSectionId] = useState<number | null>(null);
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [selectedExercise, setSelectedExercise] = useState<Exercise | null>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [result, setResult] = useState<ExerciseResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isFetchingSubmission, setIsFetchingSubmission] = useState(false);
  
  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    router.push("/login");
  };

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    const userData = localStorage.getItem("user");

    if (!token || !userData) {
      toast.error("Veuillez vous connecter.");
      router.push("/login");
      return;
    }

    const parsedUser = JSON.parse(userData);
    if (parsedUser.role !== "STUDENT") {
      toast.error("Accès non autorisé. Cette page est réservée aux étudiants.");
      router.push("/login");
      return;
    }
    
    setUser(parsedUser);
    fetchSections();
  }, [router]);

  const fetchSections = async () => {
    setIsLoading(true);
    try {
      const response = await api.get("/api/sections/");
      const activeSections = response.data.filter((section: Section) => 
        section.allow_exercises !== false
      );
      setSections(activeSections);
      
      if (activeSections.length > 0) {
        setSelectedSectionId(activeSections[0].id);
      }
    } catch (err: any) {
      console.error("Failed to fetch sections:", err);
      toast.error("Erreur lors du chargement des sections.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (selectedSectionId) {
      fetchExercises(selectedSectionId);
    }
  }, [selectedSectionId]);

  const fetchExercises = async (sectionId: number) => {
    setIsLoading(true);
    try {
      const response = await api.get(`/api/exercises/sections/${sectionId}/exercises`);
      setExercises(response.data);
      setSelectedExercise(null);
      setResult(null);
      setAnswers({});
    } catch (err: any) {
      console.error("Failed to fetch exercises:", err);
      toast.error("Erreur lors du chargement des exercices.");
      setExercises([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnswerChange = (questionId: number, answer: string) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }));
  };

  const handleSubmitExercise = async () => {
    if (!selectedExercise) return;

    // Validate that all questions are answered
    const unansweredQuestions = selectedExercise.questions.filter(
      q => !answers[q.id] || answers[q.id].trim() === ""
    );

    if (unansweredQuestions.length > 0) {
      toast.error("Veuillez répondre à toutes les questions avant de soumettre.");
      return;
    }

    setIsSubmitting(true);
    try {
      const submissionData = {
        exercise_id: selectedExercise.id,
        answers: Object.entries(answers).map(([questionId, answer]) => ({
          question_id: parseInt(questionId),
          answer: answer
        }))
      };

      const response = await api.post(
        `/api/exercises/exercises/${selectedExercise.id}/submit`,
        submissionData
      );
      
      setResult(response.data);
      toast.success("Exercice soumis avec succès!");
    } catch (err: any) {
      console.error("Failed to submit exercise:", err);
      toast.error(err.response?.data?.detail || "Erreur lors de la soumission de l'exercice.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderQuestion = (question: Question, index: number) => {
    const answer = answers[question.id] || "";
    const feedback = result?.feedback.find(f => f.question_id === question.id);

    return (
      <div key={question.id} className="p-4 border rounded-lg bg-gray-50 mb-4">
        <div className="flex justify-between items-start mb-2">
          <h4 className="font-semibold text-gray-800">
            Question {index + 1} 
            {question.points > 1 && ` (${question.points} points)`}
          </h4>
          {feedback && (
            <span className={`text-sm font-medium ${feedback.is_correct ? 'text-green-600' : 'text-red-600'}`}>
              {feedback.earned_points}/{question.points} points
            </span>
          )}
        </div>
        
        <p className="text-gray-700 mb-3">{question.text}</p>

        {/* MCQ Questions */}
        {question.question_type === "mcq" && question.options && (
          <div className="space-y-2">
            {question.options.map((option, optIndex) => (
              <label 
                key={optIndex} 
                className={`flex items-center p-2 rounded cursor-pointer transition-colors ${
                  result 
                    ? option === question.correct_answer 
                      ? 'bg-green-100' 
                      : answer === option && !feedback?.is_correct
                      ? 'bg-red-100'
                      : 'bg-white'
                    : answer === option 
                    ? 'bg-blue-100' 
                    : 'bg-white hover:bg-gray-100'
                }`}
              >
                <input
                  type="radio"
                  name={`question-${question.id}`}
                  value={option}
                  checked={answer === option}
                  onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                  disabled={!!result}
                  className="mr-2"
                />
                <span className="text-gray-700">
                  {option}
                  {result && option === question.correct_answer && (
                    <span className="ml-2 text-green-600 font-medium">✓ Correct</span>
                  )}
                </span>
              </label>
            ))}
          </div>
        )}

        {/* True/False Questions */}
        {question.question_type === "true_false" && (
          <div className="space-y-2">
            {["true", "false"].map((value) => (
              <label 
                key={value}
                className={`flex items-center p-2 rounded cursor-pointer transition-colors ${
                  result 
                    ? value === question.correct_answer 
                      ? 'bg-green-100' 
                      : answer === value && !feedback?.is_correct
                      ? 'bg-red-100'
                      : 'bg-white'
                    : answer === value 
                    ? 'bg-blue-100' 
                    : 'bg-white hover:bg-gray-100'
                }`}
              >
                <input
                  type="radio"
                  name={`question-${question.id}`}
                  value={value}
                  checked={answer === value}
                  onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                  disabled={!!result}
                  className="mr-2"
                />
                <span className="text-gray-700">
                  {value === "true" ? "Vrai" : "Faux"}
                  {result && value === question.correct_answer && (
                    <span className="ml-2 text-green-600 font-medium">✓ Correct</span>
                  )}
                </span>
              </label>
            ))}
          </div>
        )}

        {/* Open-ended Questions */}
        {question.question_type === "open_ended" && (
          <textarea
            className="w-full p-2 border rounded-md resize-none"
            rows={4}
            value={answer}
            onChange={(e) => handleAnswerChange(question.id, e.target.value)}
            disabled={!!result}
            placeholder="Entrez votre réponse ici..."
          />
        )}

        {/* Fill in the blank */}
        {question.question_type === "fill_blank" && (
          <input
            type="text"
            className="w-full p-2 border rounded-md"
            value={answer}
            onChange={(e) => handleAnswerChange(question.id, e.target.value)}
            disabled={!!result}
            placeholder="Entrez le mot manquant..."
          />
        )}

        {/* Feedback */}
        {feedback && (
          <div className={`mt-3 p-3 rounded-md ${feedback.is_correct ? 'bg-green-50' : 'bg-red-50'}`}>
            <p className="text-sm">{feedback.feedback}</p>
            {question.explanation && (
              <p className="text-sm mt-2 text-gray-600">
                <strong>Explication:</strong> {question.explanation}
              </p>
            )}
          </div>
        )}
      </div>
    );
  };

  if (!user) {
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
        <title>Exercices - Assistant Éducatif UQAR</title>
      </Head>
      <div className="min-h-screen bg-gray-100">
        {/* Header */}
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-6">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Exercices
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
                onClick={() => router.push("/student/dashboard")}
              >
                Dashboard
              </button>
              <button
                className="px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 border-b-2 border-transparent hover:border-gray-300"
                onClick={() => router.push("/student/chat")}
              >
                Chat
              </button>
              <button
                className="px-3 py-2 text-sm font-medium text-primary-600 border-b-2 border-primary-600"
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
              {isLoading ? (
                <p>Chargement des sections...</p>
              ) : sections.length === 0 ? (
                <p className="text-sm text-gray-500">Aucune section avec exercices disponible.</p>
              ) : (
                <select
                  id="section-select"
                  className="input w-full md:w-1/2"
                  value={selectedSectionId || ""}
                  onChange={(e) => setSelectedSectionId(parseInt(e.target.value))}
                >
                  {sections.map((section) => (
                    <option key={section.id} value={section.id}>
                      {section.name}
                    </option>
                  ))}
                </select>
              )}
            </div>
          </div>

          {selectedSectionId && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Exercise List */}
              <div className="md:col-span-1">
                <div className="card">
                  <div className="card-header">
                    <h2 className="text-lg font-semibold">Exercices Disponibles</h2>
                  </div>
                  <div className="card-body">
                    {isLoading ? (
                      <p>Chargement des exercices...</p>
                    ) : exercises.length === 0 ? (
                      <p className="text-gray-500">Aucun exercice disponible pour cette section.</p>
                    ) : (
                      <ul className="space-y-2">
                        {exercises.map((exercise, index) => (
                          <li key={exercise.id}>
                            <button
                              onClick={async () => {
                                if (selectedExercise?.id === exercise.id) return; // Avoid refetch if already selected

                                setSelectedExercise(exercise);
                                setResult(null); // Clear previous result
                                setAnswers({});   // Clear previous answers
                                setIsFetchingSubmission(true);

                                try {
                                  const response = await api.get(`/api/exercises/exercises/${exercise.id}/submissions`);
                                  if (response.data && response.data.length > 0) {
                                    const priorSubmission = response.data[0]; // Already ordered by submitted_at desc

                                    const total_points = exercise.questions.reduce((sum, q) => sum + q.points, 0);
                                    
                                    let overallFeedbackText = `Vous avez obtenu ${priorSubmission.score}/${total_points} points (${priorSubmission.percentage.toFixed(1)}%). `;
                                    if (priorSubmission.percentage >= 80) {
                                        overallFeedbackText += "Excellent travail !";
                                    } else if (priorSubmission.percentage >= 60) {
                                        overallFeedbackText += "Bon travail !";
                                    } else {
                                        overallFeedbackText += "Continuez vos efforts !";
                                    }

                                    const mappedResult: ExerciseResult = {
                                      exercise_id: priorSubmission.exercise_id,
                                      total_points: total_points,
                                      earned_points: priorSubmission.score,
                                      percentage: priorSubmission.percentage,
                                      feedback: priorSubmission.feedback, // This should match AnswerFeedback[]
                                      overall_feedback: overallFeedbackText,
                                    };
                                    setResult(mappedResult);
                                    setAnswers(priorSubmission.answers || {});
                                  } else {
                                    // No prior submission found
                                    setResult(null);
                                    setAnswers({});
                                  }
                                } catch (error: any) {
                                  console.error("Failed to fetch prior submission:", error);
                                  toast.error(error.response?.data?.detail || "Erreur lors du chargement de la soumission précédente.");
                                  setResult(null);
                                  setAnswers({});
                                } finally {
                                  setIsFetchingSubmission(false);
                                }
                              }}
                              className={`w-full text-left p-3 rounded-md transition-colors ${
                                selectedExercise?.id === exercise.id
                                  ? 'bg-primary-100 text-primary-700'
                                  : 'hover:bg-gray-100'
                              }`}
                            >
                              <div className="font-medium">Exercice {index + 1}</div>
                              <div className="text-sm text-gray-500">
                                {exercise.questions.length} questions
                              </div>
                              <div className="text-xs text-gray-400">
                                {new Date(exercise.created_at).toLocaleDateString()}
                              </div>
                            </button>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              </div>

              {/* Exercise Content */}
              <div className="md:col-span-2">
                {isFetchingSubmission ? (
                    <div className="card">
                        <div className="card-body text-center">
                            <div className="spinner w-6 h-6 mx-auto mb-2"></div>
                            <p className="text-gray-500">Chargement de la soumission...</p>
                        </div>
                    </div>
                ) : selectedExercise ? (
                  <div className="card">
                    <div className="card-header">
                      <h2 className="text-xl font-semibold">
                        Exercice - {selectedExercise.questions.length} questions
                      </h2>
                    </div>
                    <div className="card-body">
                      {/* Questions */}
                      <div className="space-y-4">
                        {selectedExercise.questions.map((question, index) => 
                          renderQuestion(question, index)
                        )}
                      </div>

                      {/* Submit Button or Results */}
                      {!result ? (
                        <div className="mt-6 flex justify-end">
                          <button
                            onClick={handleSubmitExercise}
                            disabled={isSubmitting}
                            className="btn-primary"
                          >
                            {isSubmitting ? "Soumission..." : "Soumettre l'exercice"}
                          </button>
                        </div>
                      ) : (
                        <div className="mt-6">
                          {/* Overall Result */}
                          <div className={`p-4 rounded-lg ${
                            result.percentage >= 80 
                              ? 'bg-green-50 border-green-200' 
                              : result.percentage >= 60
                              ? 'bg-yellow-50 border-yellow-200'
                              : 'bg-red-50 border-red-200'
                          } border`}>
                            <h3 className="text-lg font-semibold mb-2">Résultat Final</h3>
                            <p className="text-2xl font-bold mb-2">
                              {result.earned_points}/{result.total_points} points ({result.percentage.toFixed(1)}%)
                            </p>
                            <p className="text-gray-700">{result.overall_feedback}</p>
                            <button
                              onClick={() => {
                                setSelectedExercise(null);
                                setResult(null);
                                setAnswers({});
                              }}
                              className="mt-4 btn-secondary"
                            >
                              Faire un autre exercice
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="card">
                    <div className="card-body text-center text-gray-500">
                      <p>Sélectionnez un exercice pour commencer</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </>
  );
} 