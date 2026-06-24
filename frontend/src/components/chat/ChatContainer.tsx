import { useState, useRef, useEffect } from "react";
import { Menu, X, Bot } from "lucide-react";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { ChatSidebar } from "./ChatSidebar";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

// Simulated streaming response for demo
const simulateStream = async (
  text: string,
  onChunk: (chunk: string) => void
) => {
  const words = text.split(" ");
  for (let i = 0; i < words.length; i++) {
    await new Promise((resolve) => setTimeout(resolve, 50 + Math.random() * 50));
    onChunk(words[i] + (i < words.length - 1 ? " " : ""));
  }
};

const sampleResponses = [
  "Based on the documents I've analyzed, I can provide you with a comprehensive answer. The RAG (Retrieval-Augmented Generation) system combines the power of large language models with your specific document knowledge base to deliver accurate, contextual responses.",
  "That's a great question! Let me search through the relevant documents to find the most accurate information for you. According to the indexed content, here's what I found...",
  "I've reviewed your documents and found several relevant pieces of information. The key points are: First, the system uses vector embeddings to understand semantic similarity. Second, it retrieves the most relevant chunks before generating a response.",
  "Based on my analysis of the document corpus, I can confirm that this approach provides better accuracy than traditional keyword search. The embedding-based retrieval ensures we capture the true meaning of your query.",
];

export const ChatContainer = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedProvider, setSelectedProvider] = useState("GROQ");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content,
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    // Create assistant message placeholder
    const assistantId = (Date.now() + 1).toString();
    setMessages((prev) => [
      ...prev,
      { id: assistantId, role: "assistant", content: "" },
    ]);

    // Simulate streaming response
    const responseText =
      sampleResponses[Math.floor(Math.random() * sampleResponses.length)];

    await simulateStream(responseText, (chunk) => {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantId
            ? { ...msg, content: msg.content + chunk }
            : msg
        )
      );
    });

    setIsLoading(false);
  };

  const handleReload = async () => {
    await new Promise((resolve) => setTimeout(resolve, 1500));
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <ChatSidebar
        isOpen={sidebarOpen}
        onReload={handleReload}
        status={{
          assistantReady: true,
          documentsLoaded: true,
          documentCount: 5,
          chunkCount: 127,
        }}
        documents={[
          "introduction.txt",
          "api-reference.txt",
          "best-practices.txt",
          "faq.txt",
          "troubleshooting.txt",
        ]}
        selectedProvider={selectedProvider}
        onProviderChange={setSelectedProvider}
        providers={["GROQ", "Gemini"]}
      />

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-foreground/20 backdrop-blur-sm z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Chat Area */}
      <main
        className={cn(
          "flex-1 flex flex-col transition-all duration-300",
          sidebarOpen ? "lg:ml-72" : "ml-0"
        )}
      >
        {/* Header */}
        <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-card/50 backdrop-blur-sm">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="rounded-lg"
            >
              {sidebarOpen ? (
                <X className="w-5 h-5" />
              ) : (
                <Menu className="w-5 h-5" />
              )}
            </Button>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg gradient-primary flex items-center justify-center shadow-primary">
                <Bot className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-foreground">
                  RAG Assistant
                </h1>
                <p className="text-xs text-muted-foreground">
                  AI-powered document retrieval
                </p>
              </div>
            </div>
          </div>
        </header>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-4 py-6">
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full py-20 animate-fade-in">
                <div className="w-20 h-20 rounded-xl gradient-primary flex items-center justify-center shadow-primary mb-6">
                  <Bot className="w-10 h-10 text-primary-foreground" />
                </div>
                <h2 className="text-2xl font-semibold text-foreground mb-2">
                  Welcome to RAG Assistant
                </h2>
                <p className="text-muted-foreground text-center max-w-md">
                  Ask anything about your documents with AI-powered retrieval
                  and reasoning.
                </p>
              </div>
            ) : (
              messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  role={message.role}
                  content={message.content}
                  isStreaming={
                    isLoading &&
                    message.role === "assistant" &&
                    message.id === messages[messages.length - 1]?.id
                  }
                />
              ))
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-border bg-card/50 backdrop-blur-sm px-4 py-4">
          <div className="max-w-3xl mx-auto">
            <ChatInput
              onSend={handleSend}
              disabled={isLoading}
              placeholder="Type your question here..."
            />
          </div>
        </div>
      </main>
    </div>
  );
};
