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
    <div className="flex flex-col min-h-screen bg-[#faf8f5] text-[#2c2c2c] font-sans selection:bg-orange-200 relative">
      {/* Premium Ambient Background */}
      <div className="fixed inset-0 z-0 bg-gradient-to-br from-[#fffbfa] via-[#f7f3ed] to-[#faeee7] pointer-events-none"></div>
      <div className="fixed -top-[20%] -left-[10%] w-[60%] h-[60%] rounded-full bg-[#e96b35]/5 blur-[120px] pointer-events-none z-0"></div>
      <div className="fixed top-[30%] -right-[10%] w-[50%] h-[70%] rounded-full bg-[#3b82f6]/5 blur-[120px] pointer-events-none z-0"></div>

      {/* Subtle Texture */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.015] bg-[url('https://www.transparenttextures.com/patterns/food.png')] z-0"></div>

      {/* Header */}
      <header className="sticky top-0 z-10 border-b border-white/60 bg-white/60 backdrop-blur-2xl px-6 md:px-10 py-5 flex items-center justify-between shadow-[0_4px_30px_rgba(0,0,0,0.03)]">
        <div className="flex items-center gap-3">
          <div className="bg-gradient-to-br from-[#e96b35] to-[#d65e2b] text-white p-2.5 rounded-xl shadow-md border border-[#c55322]">
            <ChefHat size={26} strokeWidth={2.5} />
          </div>
          <div>
            <h1 className="text-xl font-bold font-serif tracking-tight text-[#1a1a1a]">Recipe GraphRAG</h1>
            <p className="text-xs text-[#8c8577] font-semibold tracking-wide uppercase mt-0.5 hidden sm:block">Neo4j Knowledge Graph</p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-sm text-[#5a5449] bg-[#f4f1eb] px-4 py-2 rounded-full border border-[#e5e1d8] shadow-inner">
          <BookOpen size={16} className="text-[#e96b35]" />
          <span className="font-bold hidden sm:inline tracking-tight">CS Final Project</span>
        </div>
      </header>

      {/* Main Chat Area */}
      <main className="flex-1 overflow-y-auto px-6 md:px-12 py-10 md:py-16 relative z-0">
        <div className="max-w-4xl mx-auto space-y-10">

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
                } animate-in slide-in-from-bottom-2 fade-in duration-300`}
            >
              <div
                className={`max-w-[85%] sm:max-w-[80%] px-6 py-4 rounded-2xl shadow-sm border ${m.role === "user"
                  ? "bg-[#3b82f6] text-white border-[#3b82f6] rounded-br-sm shadow-blue-500/10"
                  : "bg-white text-[#2c2c2c] border-[#e5e1d8] rounded-bl-sm shadow-black/5"
                  }`}
              >
                {m.role === "assistant" ? (
                  <div className="prose prose-sm md:prose-base prose-orange max-w-none prose-p:leading-relaxed prose-li:my-1">
                    <ReactMarkdown>{m.content}</ReactMarkdown>
                  </div>
                ) : (
                  <p className="whitespace-pre-wrap leading-relaxed m-0 text-base font-medium" style={{ color: "#ffffff" }}>{m.content}</p>
                )}
              </div>
              <span className="text-xs text-[#8c8577] mt-2 px-2 font-semibold tracking-wide uppercase">
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
      <footer className="sticky bottom-0 w-full bg-gradient-to-t from-[#f7f3ed] via-[#f7f3ed]/95 to-transparent pt-12 pb-24 md:pb-32 px-6 md:px-10 drop-shadow-[0_-15px_30px_rgba(233,107,53,0.04)] z-10">
        <div className="max-w-4xl mx-auto relative">
          <form
            onSubmit={handleSubmit}
            className="flex items-end gap-5 bg-white rounded-[32px] border-[2px] border-[#e5e1d8] p-4 focus-within:ring-[6px] focus-within:ring-[#e96b35]/20 focus-within:border-[#e96b35] hover:border-[#d6caba] transition-all duration-300 shadow-xl shadow-orange-100/40"
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
              placeholder="Ask the chef..."
              className="flex-1 max-h-[300px] min-h-[60px] overflow-y-auto bg-transparent border-0 resize-none px-6 py-4 focus:outline-none text-[#2c2c2c] text-xl font-semibold placeholder:text-[#a39e93] placeholder:font-medium leading-relaxed tracking-wide"
              rows={1}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="bg-[#e96b35] hover:bg-[#c55322] hover:shadow-xl hover:-translate-y-1 active:translate-y-0 disabled:bg-[#f2efe9] disabled:text-[#a39e93] disabled:hover:shadow-none disabled:hover:translate-y-0 disabled:transform-none text-white p-6 rounded-[24px] transition-all duration-300 shrink-0 flex items-center justify-center shadow-md mb-2 mr-2"
            >
              <Send size={32} strokeWidth={2.5} className="ml-1" />
            </button>
          </form>
          <div className="text-center mt-6 mb-2">
            <span className="text-sm text-[#8c8577] font-bold tracking-wide">Recipe Graph RAG • Powered by Neo4j</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
