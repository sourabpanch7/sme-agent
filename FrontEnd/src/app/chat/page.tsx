"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { ref, push, onValue, off, set, get } from "firebase/database";
import { database } from "@/lib/firebase";
import Sidebar from "@/components/Sidebar";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

export default function ChatPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>("default");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/auth/login");
    }
  }, [user, loading, router]);

  // Load messages for current conversation
  useEffect(() => {
    if (user && currentConversationId) {
      const isAnonymous = user.isAnonymous;
      const messagesPath = isAnonymous
        ? `users/anonymous/${user.uid}/conversations/${currentConversationId}/messages`
        : `users/${user.uid}/conversations/${currentConversationId}/messages`;
      
      const messagesRef = ref(database, messagesPath);
      
      onValue(messagesRef, (snapshot) => {
        const data = snapshot.val();
        if (data) {
          const messagesList: Message[] = Object.keys(data).map((key) => ({
            id: key,
            ...data[key],
          }));
          setMessages(messagesList.sort((a, b) => a.timestamp - b.timestamp));
        } else {
          setMessages([]);
        }
      });

      return () => {
        off(messagesRef);
      };
    }
  }, [user, currentConversationId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const updateConversationTitle = async (conversationId: string, firstMessage: string) => {
    if (!user) return;

    const isAnonymous = user.isAnonymous;
    const conversationPath = isAnonymous
      ? `users/anonymous/${user.uid}/conversations/${conversationId}`
      : `users/${user.uid}/conversations/${conversationId}`;

    const conversationRef = ref(database, conversationPath);
    const snapshot = await get(conversationRef);
    
    if (!snapshot.exists() || !snapshot.val().title) {
      // Generate title from first message (first 50 characters)
      const title = firstMessage.length > 50 
        ? firstMessage.substring(0, 50) + "..." 
        : firstMessage;
      
      await set(ref(database, `${conversationPath}/title`), title);
      await set(ref(database, `${conversationPath}/lastMessage`), firstMessage.substring(0, 100));
      await set(ref(database, `${conversationPath}/timestamp`), Date.now());
    }
  };

  const updateConversationMetadata = async (conversationId: string, lastMessage: string) => {
    if (!user) return;

    const isAnonymous = user.isAnonymous;
    const conversationPath = isAnonymous
      ? `users/anonymous/${user.uid}/conversations/${conversationId}`
      : `users/${user.uid}/conversations/${conversationId}`;

    await set(ref(database, `${conversationPath}/lastMessage`), lastMessage.substring(0, 100));
    await set(ref(database, `${conversationPath}/timestamp`), Date.now());
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !user || isSending) return;

    const userMessage = input.trim();
    setInput("");
    setIsSending(true);

    try {
      const isAnonymous = user.isAnonymous;
      const conversationId = currentConversationId || `conv_${Date.now()}`;
      
      if (!currentConversationId) {
        setCurrentConversationId(conversationId);
      }

      const messagesPath = isAnonymous
        ? `users/anonymous/${user.uid}/conversations/${conversationId}/messages`
        : `users/${user.uid}/conversations/${conversationId}/messages`;
      
      const messagesRef = ref(database, messagesPath);

      // Add user message
      await push(messagesRef, {
        role: "user",
        content: userMessage,
        timestamp: Date.now(),
      });

      // Update conversation title if it's a new conversation
      if (messages.length === 0) {
        await updateConversationTitle(conversationId, userMessage);
      } else {
        // Update last message and timestamp for existing conversations
        await updateConversationMetadata(conversationId, userMessage);
      }

      // TODO: Replace this with actual API call to your backend
      // For now, we'll simulate a response
      setTimeout(async () => {
        const assistantMessage = "This is a placeholder response. Connecting the backend API will get real responses from our RAG system.";
        await push(messagesRef, {
          role: "assistant",
          content: assistantMessage,
          timestamp: Date.now(),
        });
        
        // Update conversation metadata with assistant's response
        await updateConversationMetadata(conversationId, assistantMessage);
        
        setIsSending(false);
      }, 1000);
    } catch (error) {
      console.error("Error sending message:", error);
      setIsSending(false);
    }
  };

  const handleNewChat = () => {
    setCurrentConversationId(`conv_${Date.now()}`);
    setMessages([]);
  };

  const handleConversationSelect = (conversationId: string) => {
    setCurrentConversationId(conversationId);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-white dark:bg-black">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="flex h-screen bg-white dark:bg-black">
      {/* Sidebar */}
      <Sidebar
        currentConversationId={currentConversationId}
        onConversationSelect={handleConversationSelect}
        onNewChat={handleNewChat}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto px-4 py-8">
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <h2 className="text-3xl font-semibold text-gray-900 dark:text-white mb-4">
                  How can I help you today?
                </h2>
                <p className="text-gray-500 dark:text-gray-400">
                  Start a conversation by typing a message below
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex gap-4 ${
                      message.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    {message.role === "assistant" && (
                      <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-semibold flex-shrink-0">
                        R
                      </div>
                    )}
                    <div
                      className={`max-w-[70%] rounded-2xl px-4 py-3 ${
                        message.role === "user"
                          ? "bg-blue-600 text-white"
                          : "bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-white"
                      }`}
                    >
                      <p className="whitespace-pre-wrap break-words text-sm">
                        {message.content}
                      </p>
                    </div>
                    {message.role === "user" && (
                      <div className="w-8 h-8 rounded-full bg-gray-300 dark:bg-gray-700 flex items-center justify-center text-gray-700 dark:text-gray-300 text-sm font-semibold flex-shrink-0">
                        {user.isAnonymous ? "G" : user.email?.charAt(0).toUpperCase()}
                      </div>
                    )}
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </div>

        {/* Input */}
        <div className="border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-black">
          <div className="max-w-3xl mx-auto px-4 py-6">
            <form onSubmit={handleSubmit} className="relative">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
                placeholder="Message RAGgers..."
                disabled={isSending}
                rows={1}
                className="w-full px-4 py-3 pr-12 border border-gray-300 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 disabled:opacity-50 disabled:cursor-not-allowed resize-none"
                style={{ minHeight: "52px", maxHeight: "200px" }}
              />
              <button
                type="submit"
                disabled={!input.trim() || isSending}
                className="absolute right-3 bottom-3 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isSending ? (
                  <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                  </svg>
                )}
              </button>
            </form>
            <p className="text-xs text-gray-500 dark:text-gray-400 text-center mt-3">
              RAGgers can make mistakes. Check important info.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
