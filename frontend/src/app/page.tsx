"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { Send, ChefHat, Loader2, BookOpen, AlertCircle } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hello! I am your culinary assistant powered by a Recipe Knowledge Graph. What recipe are you looking for today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Auto-scroll to bottom of chat
  const messagesEndRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    try {
      // Format chat history for the backend (excluding the current message, keep only last 6 for context limit safety)
      const chatHistory = messages
        .filter((m, idx) => idx > 0) // Skip initial greeting
        .slice(-6) // Keep only the last 6 messages to prevent LLM token limits
        .map((m) => `${m.role === "user" ? "User" : "Assistant"}: ${m.content}`)
        .join("\\n\\n");

      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: userMessage,
          chat_history: chatHistory,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to communicate with the recipe server.");
      }

      const data = await response.json();

      if (data.status === "error") {
        throw new Error(data.answer);
      }

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer },
      ]);
    } catch (err: any) {
      setError("An error occurred during communication.");
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Oops! An error occurred: ${err.message || "Please check the backend connection."}`,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-[#fcfbf9] text-[#2c2c2c] font-sans selection:bg-orange-200">
      {/* Header */}
      <header className="sticky top-0 z-10 border-b border-[#e5e1d8] bg-[#fcfbf9]/90 backdrop-blur-md px-6 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="bg-[#e96b35] text-white p-2 rounded-lg shadow-sm">
            <ChefHat size={28} strokeWidth={2} />
          </div>
          <div>
            <h1 className="text-xl font-bold font-serif tracking-tight text-[#2c2c2c]">Recipe GraphRAG</h1>
            <p className="text-sm text-[#7a7469] font-medium hidden sm:block">Neo4j & LangGraph Assistant</p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-sm text-[#7a7469] bg-[#f2efe9] px-3 py-1.5 rounded-full border border-[#e5e1d8]">
          <BookOpen size={16} />
          <span className="font-semibold hidden sm:inline">CS Final Project</span>
        </div>
      </header>

      {/* Main Chat Area */}
      <main className="flex-1 overflow-y-auto px-4 py-8">
        <div className="max-w-3xl mx-auto space-y-6">

          {error && (
            <div className="p-4 bg-red-50 text-red-700 border border-red-200 rounded-xl flex items-start gap-3">
              <AlertCircle size={20} className="shrink-0 mt-0.5" />
              <p className="text-sm font-medium">{error}</p>
            </div>
          )}

          {messages.map((m, idx) => (
            <div
              key={idx}
              className={`flex flex-col ${m.role === "user" ? "items-end" : "items-start"
                }`}
            >
              <div
                className={`max-w-[85%] sm:max-w-[75%] px-5 py-4 rounded-2xl shadow-sm border ${m.role === "user"
                  ? "bg-[#3b82f6] text-white border-[#3b82f6] rounded-br-sm"
                  : "bg-white text-[#2c2c2c] border-[#e5e1d8] rounded-bl-sm"
                  }`}
              >
                {m.role === "assistant" ? (
                  <div className="prose prose-sm prose-orange max-w-none">
                    <ReactMarkdown>{m.content}</ReactMarkdown>
                  </div>
                ) : (
                  <p className="whitespace-pre-wrap leading-relaxed m-0" style={{ color: "#ffffff" }}>{m.content}</p>
                )}
              </div>
              <span className="text-xs text-[#a39e93] mt-2 px-1 font-medium">
                {m.role === "user" ? "You" : "Chef AI"}
              </span>
            </div>
          ))}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex flex-col items-start fade-in">
              <div className="bg-white border text-[#e96b35] border-[#e5e1d8] px-5 py-4 rounded-2xl rounded-bl-sm shadow-sm flex items-center gap-3">
                <Loader2 className="animate-spin" size={20} />
                <span className="text-sm font-medium text-[#7a7469]">Searching recipe graph...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input Area */}
      <footer className="sticky bottom-0 bg-[#fcfbf9]/95 backdrop-blur-md border-t border-[#e5e1d8] px-4 py-5 shadow-[0_-4px_20px_rgba(0,0,0,0.02)]">
        <div className="max-w-3xl mx-auto relative">
          <form
            onSubmit={handleSubmit}
            className="flex items-end gap-2 bg-white rounded-2xl border border-[#e5e1d8] p-2 shadow-sm focus-within:ring-2 focus-within:ring-[#e96b35]/20 focus-within:border-[#e96b35] transition-all"
          >
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
              placeholder="Ask for a recipe, ingredient, or cooking method..."
              className="flex-1 max-h-48 min-h-[44px] overflow-y-auto bg-transparent border-0 resize-none px-3 py-2.5 focus:outline-none text-[#2c2c2c] placeholder:text-[#a39e93] leading-relaxed"
              rows={1}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="bg-[#e96b35] hover:bg-[#d65e2b] disabled:bg-[#f2efe9] disabled:text-[#a39e93] text-white p-3 rounded-xl transition-colors shrink-0 flex items-center justify-center shadow-sm disabled:shadow-none mb-0.5 mr-0.5"
            >
              <Send size={18} strokeWidth={2.5} className="ml-0.5" />
            </button>
          </form>
          <div className="text-center mt-3">
            <span className="text-xs text-[#a39e93] font-medium">Recipe Graph RAG answers are generated from Neo4j factual extraction.</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
