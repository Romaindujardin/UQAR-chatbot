import { useState, useEffect, useRef } from "react";
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

interface ChatSession {
  id: number;
  title: string;
  section_id: number;
  section_name: string;
  created_at: string;
  last_message_at: string | null;
  message_count: number;
}

interface ChatMessage {
  id: number;
  content: string;
  is_user: boolean;
  created_at: string;
}

export default function StudentChat() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [sections, setSections] = useState<Section[]>([]);
  const [selectedSection, setSelectedSection] = useState<Section | null>(null);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [selectedSession, setSelectedSession] = useState<ChatSession | null>(
    null
  );
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [isCreatingSession, setIsCreatingSession] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

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
    loadChatSessions();
  }, [router]);

  useEffect(() => {
    // Scroll to bottom when messages change
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const loadSections = async () => {
    try {
      const response = await api.get("/api/sections/");

      setSections(response.data);
      setIsLoading(false);
    } catch (error: any) {
      console.error("Erreur lors du chargement des sections:", error);
      toast.error("Erreur lors du chargement des sections");
      setIsLoading(false);
    }
  };

  const loadChatSessions = async () => {
    try {
      const response = await api.get("/api/chat/sessions");

      setChatSessions(response.data);
    } catch (error: any) {
      console.error("Erreur lors du chargement des sessions:", error);
      toast.error("Erreur lors du chargement des sessions");
    }
  };

  const loadSessionMessages = async (sessionId: number) => {
    try {
      const response = await api.get(
        `/api/chat/sessions/${sessionId}/messages`
      );

      setMessages(response.data);
    } catch (error: any) {
      console.error("Erreur lors du chargement des messages:", error);
      toast.error("Erreur lors du chargement des messages");
    }
  };

  const createChatSession = async () => {
    if (!selectedSection) {
      toast.error("Veuillez sélectionner une section");
      return;
    }

    try {
      setIsCreatingSession(true);

      const response = await api.post("/api/chat/sessions", {
        section_id: selectedSection.id,
      });

      setChatSessions([...chatSessions, response.data]);

      setSelectedSession(response.data);
      setMessages([]);

      setIsCreatingSession(false);
    } catch (error: any) {
      console.error("Erreur lors de la création de la session:", error);

      if (error.response && error.response.data && error.response.data.detail) {
        toast.error(`Erreur: ${error.response.data.detail}`);
      } else {
        toast.error("Erreur lors de la création de la session");
      }

      setIsCreatingSession(false);
    }
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!newMessage.trim() || !selectedSession) {
      return;
    }

    const optimisticMessage = {
      id: Date.now(),
      content: newMessage,
      is_user: true,
      created_at: new Date().toISOString(),
    };

    setMessages([...messages, optimisticMessage]);

    const currentMessage = newMessage;
    setNewMessage("");

    scrollToBottom();

    try {
      const response = await api.post(
        `/api/chat/sessions/${selectedSession.id}/messages`,
        {
          content: currentMessage,
        }
      );

      if (response.data && response.data.system_message) {
        setMessages((prevMessages) => [
          ...prevMessages,
          response.data.system_message,
        ]);

        scrollToBottom();
      }
    } catch (error: any) {
      console.error("Erreur lors de l'envoi du message:", error);

      if (error.response && error.response.data && error.response.data.detail) {
        toast.error(`Erreur: ${error.response.data.detail}`);
      } else {
        toast.error("Erreur lors de l'envoi du message");
      }

      setMessages((prevMessages) =>
        prevMessages.filter((msg) => msg.id !== optimisticMessage.id)
      );

      setNewMessage(currentMessage);
    }
  };

  const handleSessionSelect = (session: ChatSession) => {
    setSelectedSession(session);
    loadSessionMessages(session.id);

    const section = sections.find((s) => s.id === session.section_id);
    if (section) {
      setSelectedSection(section);
    }
  };

  const deleteSession = async (sessionId: number) => {
    if (!confirm("Êtes-vous sûr de vouloir supprimer cette conversation ?")) {
      return;
    }

    try {
      await api.delete(`/api/chat/sessions/${sessionId}`);

      toast.success("Conversation supprimée avec succès");

      setChatSessions(
        chatSessions.filter((session) => session.id !== sessionId)
      );

      if (selectedSession && selectedSession.id === sessionId) {
        setSelectedSession(null);
        setMessages([]);
      }
    } catch (error: any) {
      console.error("Erreur lors de la suppression:", error);

      if (error.response && error.response.data && error.response.data.detail) {
        toast.error(`Erreur: ${error.response.data.detail}`);
      } else {
        toast.error("Erreur lors de la suppression de la conversation");
      }
    }
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString("fr-FR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
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
        <title>Assistant IA - UQAR</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div className="min-h-screen bg-gray-50 flex flex-col">
        {/* Header */}
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-6">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Assistant IA
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
              className="px-3 py-2 text-sm font-medium text-primary-600 border-b-2 border-primary-600"
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
        <div className="flex-1 flex overflow-hidden py-1 sm:px-2">
          {/* Sidebar */}
          <div className="w-64 bg-white border-r border-gray-200 flex flex-col rounded-lg shadow-sm overflow-hidden">

            {/* Nouvelle conversation */}
            <div className="p-4 border-b border-gray-200">
              <div className="mb-4">
                <label
                  htmlFor="section-select"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Section
                </label>
                <select
                  id="section-select"
                  className="input w-full"
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
              <button
                onClick={createChatSession}
                disabled={isCreatingSession || !selectedSection}
                className="btn-primary w-full"
              >
                {isCreatingSession ? (
                  <div className="flex items-center justify-center">
                    <div className="spinner w-4 h-4 mr-2"></div>
                    Création...
                  </div>
                ) : (
                  "Nouvelle conversation"
                )}
              </button>
            </div>

            {/* Liste des conversations */}
            <div className="flex-1 overflow-y-auto p-2">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-2 mb-2">
                Conversations
              </h3>
              {chatSessions.length === 0 ? (
                <p className="text-sm text-gray-500 px-2">
                  Aucune conversation
                </p>
              ) : (
                <ul className="space-y-1">
                  {chatSessions.map((session) => (
                    <li
                      key={session.id}
                      className={`px-2 py-2 rounded-md cursor-pointer flex justify-between items-center ${
                        selectedSession?.id === session.id
                          ? "bg-primary-100"
                          : "hover:bg-gray-100"
                      }`}
                      onClick={() => handleSessionSelect(session)}
                    >
                      <div className="flex-1 truncate">
                        <div className="text-sm font-medium text-gray-900 truncate">
                          {session.title}
                        </div>
                        <div className="text-xs text-gray-500">
                          {session.section_name} - {session.message_count}{" "}
                          messages
                        </div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteSession(session.id);
                        }}
                        className="text-gray-400 hover:text-red-600"
                      >
                        <svg
                          className="h-4 w-4"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                          />
                        </svg>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {/* Chat Area */}
          <div className="flex-1 flex flex-col bg-gray-50">
            {selectedSession ? (
              <>
                {/* Chat Header */}
                <div className="bg-white border-b border-gray-200 p-4">
                  <div className="flex justify-between items-center">
                    <div>
                      <h2 className="text-lg font-medium text-gray-900">
                        {selectedSession.title}
                      </h2>
                      <p className="text-sm text-gray-500">
                        {selectedSession.section_name}
                      </p>
                    </div>
                    <div className="text-sm text-gray-500">
                      {formatDate(selectedSession.created_at)}
                    </div>
                  </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {messages.length === 0 ? (
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
                          d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                        />
                      </svg>
                      <h3 className="mt-2 text-sm font-medium text-gray-900">
                        Aucun message
                      </h3>
                      <p className="mt-1 text-sm text-gray-500">
                        Commencez la conversation en posant une question.
                      </p>
                    </div>
                  ) : (
                    messages.map((message) => (
                      <div
                        key={message.id}
                        className={`flex ${
                          message.is_user ? "justify-end" : "justify-start"
                        }`}
                      >
                        <div
                          className={`max-w-3xl rounded-lg px-4 py-2 ${
                            message.is_user
                              ? "bg-primary-600 text-white"
                              : "bg-white border border-gray-200"
                          }`}
                        >
                          <div className="text-sm">
                            {message.content.split("\n").map((line, i) => (
                              <p key={i} className={i > 0 ? "mt-2" : ""}>
                                {line}
                              </p>
                            ))}
                          </div>
                          <div
                            className={`text-xs mt-1 ${
                              message.is_user
                                ? "text-primary-100"
                                : "text-gray-500"
                            }`}
                          >
                            {formatDate(message.created_at)}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* Message Input */}
                <div className="bg-white border-t border-gray-200 p-4">
                  <form onSubmit={sendMessage} className="flex space-x-2">
                    <input
                      type="text"
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      placeholder="Posez votre question..."
                      className="input flex-1"
                      disabled={isSending}
                    />
                    <button
                      type="submit"
                      disabled={isSending || !newMessage.trim()}
                      className="btn-primary"
                    >
                      {isSending ? (
                        <div className="spinner w-5 h-5"></div>
                      ) : (
                        <svg
                          className="h-5 w-5"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                          />
                        </svg>
                      )}
                    </button>
                  </form>
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center p-12 max-w-md">
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
                      d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                    />
                  </svg>
                  <h3 className="mt-2 text-lg font-medium text-gray-900">
                    Bienvenue sur l'Assistant IA
                  </h3>
                  <p className="mt-1 text-gray-500">
                    Sélectionnez une section et créez une nouvelle conversation
                    pour poser vos questions sur le contenu du cours.
                  </p>
                  <div className="mt-6">
                    <button
                      onClick={() => {
                        if (sections.length > 0 && !selectedSection) {
                          setSelectedSection(sections[0]);
                        }
                        if (selectedSection) {
                          createChatSession();
                        } else {
                          toast.error("Veuillez sélectionner une section");
                        }
                      }}
                      disabled={isCreatingSession || !sections.length}
                      className="btn-primary"
                    >
                      {isCreatingSession ? (
                        <div className="flex items-center justify-center">
                          <div className="spinner w-4 h-4 mr-2"></div>
                          Création...
                        </div>
                      ) : (
                        "Commencer une conversation"
                      )}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
