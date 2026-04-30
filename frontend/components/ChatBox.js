"use client";

import { useEffect, useRef, useState } from "react";
import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000";

export default function ChatBox() {
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState("");
  const [isAsking, setIsAsking] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const askQuestion = async (event) => {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed || isAsking) return;

    const userMessage = { role: "user", content: trimmed };
    setMessages((prev) => [...prev, userMessage]);
    setQuery("");
    setErrorMessage("");

    try {
      setIsAsking(true);
      const response = await axios.post(
        `${API_BASE_URL}/ask`,
        { query: trimmed },
        { timeout: 120000 }
      );
      const answer = response?.data?.answer || "No answer returned from server.";
      const aiMessage = { role: "ai", content: answer };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      const message =
        (error?.code === "ECONNABORTED"
          ? "Request timed out. Backend may still be warming up."
          : null) ||
        error?.response?.data?.detail ||
        "Failed to get response. Please check backend connection.";
      setErrorMessage(message);
    } finally {
      setIsAsking(false);
    }
  };

  const resetConversation = async () => {
    try {
      setErrorMessage("");
      await axios.delete(`${API_BASE_URL}/reset`, { timeout: 30000 });
      setMessages([]);
    } catch (error) {
      const message =
        error?.response?.data?.detail ||
        "Failed to reset memory. Please try again.";
      setErrorMessage(message);
    }
  };

  return (
    <div className="flex h-[70vh] flex-col rounded-2xl bg-white p-5 shadow-md">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Chat</h2>
        <button
          type="button"
          onClick={resetConversation}
          className="rounded-lg bg-red-500 px-3 py-2 text-sm font-medium text-white transition hover:bg-red-600"
        >
          Reset
        </button>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto rounded-xl border border-gray-200 bg-gray-50 p-4">
        {messages.length === 0 && (
          <p className="text-sm text-gray-500">Ask a question to begin chatting.</p>
        )}

        {messages.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-2 text-sm shadow-sm ${
                message.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-white text-gray-900"
              }`}
            >
              {message.content}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {errorMessage && <p className="mt-3 text-sm text-red-600">{errorMessage}</p>}

      <form onSubmit={askQuestion} className="mt-4 flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question..."
          className="flex-1 rounded-xl border border-gray-300 px-4 py-2 text-sm outline-none ring-blue-500 transition focus:ring-2"
        />
        <button
          type="submit"
          disabled={isAsking}
          className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isAsking ? "Sending..." : "Send"}
        </button>
      </form>
    </div>
  );
}
