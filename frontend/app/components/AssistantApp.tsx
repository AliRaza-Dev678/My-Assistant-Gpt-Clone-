"use client";

import {
  Check,
  ChevronLeft,
  Copy,
  Menu,
  MessageSquare,
  Moon,
  PanelLeftClose,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Send,
  Sparkles,
  Square,
  Sun,
  Trash2,
  X,
} from "lucide-react";
import {
  FormEvent,
  KeyboardEvent,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import {
  createConversation,
  deleteConversation,
  getConversation,
  getIdentityProfile,
  listConversations,
  renameConversation,
  streamConversation,
} from "../lib/api";
import {
  configureClientIdentity,
  getOrCreateDeviceIdentity,
} from "../lib/identity";
import type {
  ConversationDetail,
  ConversationSummary,
  IdentityProfile,
  Message,
  StreamEvent,
} from "../types";
const SUGGESTIONS = [
  {
    title: "Plan a product",
    prompt: "Help me turn an app idea into a clear MVP plan.",
  },
  {
    title: "Write better code",
    prompt: "Review this problem with me and propose a clean implementation.",
  },
  {
    title: "Learn a concept",
    prompt: "Teach me a difficult concept with a simple example.",
  },
  {
    title: "Improve my writing",
    prompt: "Help me rewrite a message so it sounds clear and confident.",
  },
];

type Theme = "system" | "light" | "dark";

function temporaryId(prefix: string): string {
  return prefix + "-" + Math.random().toString(36).slice(2);
}

export function AssistantApp() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(
    null,
  );
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [theme, setTheme] = useState<Theme>("system");
  const [error, setError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [identityProfile, setIdentityProfile] = useState<IdentityProfile | null>(
    null,
  );
  const abortController = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const activeConversation = conversations.find(
    (conversation) => conversation.id === activeConversationId,
  );

  const filteredConversations = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    return query
      ? conversations.filter((item) => item.title.toLowerCase().includes(query))
      : conversations;
  }, [conversations, searchQuery]);

  useEffect(() => {
    const storedTheme = localStorage.getItem("ara-theme") as Theme | null;
    if (!storedTheme) {
      return;
    }
    const timeout = window.setTimeout(() => setTheme(storedTheme), 0);
    return () => window.clearTimeout(timeout);
  }, []);

  useEffect(() => {
    if (theme === "system") {
      delete document.documentElement.dataset.theme;
    } else {
      document.documentElement.dataset.theme = theme;
    }
    localStorage.setItem("ara-theme", theme);
  }, [theme]);

  useEffect(() => {
    async function initialLoad() {
      const deviceIdentity = getOrCreateDeviceIdentity();
      configureClientIdentity(deviceIdentity);
      setIdentityProfile({
        user_id: `device:${deviceIdentity.deviceId}`,
        display_name: deviceIdentity.deviceLabel,
        source: "device",
        device_id: deviceIdentity.deviceId,
        device_label: deviceIdentity.deviceLabel,
      });
      try {
        setIdentityProfile(await getIdentityProfile());
      } catch {
        // The local browser identity remains available if verification is offline.
      }

      try {
        const items = await listConversations();
        setConversations(items);
        if (items[0]) {
          const detail = await getConversation(items[0].id);
          setActiveConversationId(detail.id);
          setMessages(detail.messages);
        }
      } catch {
        setError(
          "The API is offline. Start the FastAPI service on port 8000, then refresh.",
        );
      } finally {
        setIsLoading(false);
      }
    }
    void initialLoad();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  async function refreshSidebar() {
    const items = await listConversations();
    setConversations(items);
  }

  async function selectConversation(id: string) {
    if (isStreaming) {
      return;
    }
    setError(null);
    setActiveConversationId(id);
    setMobileSidebarOpen(false);
    try {
      const detail = await getConversation(id);
      setMessages(detail.messages);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Could not open this conversation.",
      );
    }
  }

  async function startNewChat(): Promise<ConversationDetail | null> {
    if (isStreaming) {
      return null;
    }
    setError(null);
    try {
      const created = await createConversation();
      setConversations((current) => [created, ...current]);
      setActiveConversationId(created.id);
      setMessages([]);
      setMobileSidebarOpen(false);
      textareaRef.current?.focus();
      return created;
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Could not create a new chat.",
      );
      return null;
    }
  }

  function applyStreamEvent(
    event: StreamEvent,
    temporaryUserId: string | null,
    temporaryAssistantId: string,
  ) {
    if (event.type === "user" && temporaryUserId) {
      setMessages((current) =>
        current.map((message) =>
          message.id === temporaryUserId ? event.message : message,
        ),
      );
      return;
    }

    if (event.type === "meta") {
      setMessages((current) =>
        current.map((message) =>
          message.id === temporaryAssistantId
            ? { ...message, id: event.assistant_message_id }
            : message,
        ),
      );
      return;
    }

    if (event.type === "token") {
      setMessages((current) => {
        const assistant = [...current].reverse().find(
          (message) => message.role === "assistant",
        );
        if (!assistant) {
          return current;
        }
        return current.map((message) =>
          message.id === assistant.id
            ? { ...message, content: message.content + event.content }
            : message,
        );
      });
      return;
    }

    if (event.type === "done") {
      setMessages((current) => {
        const assistant = [...current].reverse().find(
          (message) => message.role === "assistant",
        );
        return assistant
          ? current.map((message) =>
              message.id === assistant.id ? event.message : message,
            )
          : current;
      });
      return;
    }

    if (event.type === "error") {
      throw new Error(event.message);
    }
  }

  async function runGeneration(
    conversationId: string,
    content: string | null,
    regenerate: boolean,
  ) {
    const now = new Date().toISOString();
    const temporaryUserId = regenerate ? null : temporaryId("user");
    const temporaryAssistantId = temporaryId("assistant");

    if (regenerate) {
      setMessages((current) => {
        const lastAssistantIndex = current
          .map((item) => item.role)
          .lastIndexOf("assistant");
        return [
          ...current.filter((_, index) => index !== lastAssistantIndex),
          {
            id: temporaryAssistantId,
            conversation_id: conversationId,
            role: "assistant",
            content: "",
            position: current.length,
            created_at: now,
          },
        ];
      });
    } else {
      setMessages((current) => [
        ...current,
        {
          id: temporaryUserId as string,
          conversation_id: conversationId,
          role: "user",
          content: content as string,
          position: current.length,
          created_at: now,
        },
        {
          id: temporaryAssistantId,
          conversation_id: conversationId,
          role: "assistant",
          content: "",
          position: current.length + 1,
          created_at: now,
        },
      ]);
    }

    const controller = new AbortController();
    abortController.current = controller;
    setIsStreaming(true);
    setError(null);

    try {
      await streamConversation(
        conversationId,
        content,
        regenerate,
        (event) =>
          applyStreamEvent(event, temporaryUserId, temporaryAssistantId),
        controller.signal,
      );
      const detail = await getConversation(conversationId);
      setMessages(detail.messages);
      await refreshSidebar();
    } catch (requestError) {
      if (
        !(requestError instanceof DOMException && requestError.name === "AbortError")
      ) {
        setError(
          requestError instanceof Error
            ? requestError.message
            : "The assistant could not answer.",
        );
      }
      try {
        const detail = await getConversation(conversationId);
        setMessages(detail.messages);
        await refreshSidebar();
      } catch {
        setMessages((current) =>
          current.filter(
            (message) =>
              message.id !== temporaryAssistantId || message.content.length > 0,
          ),
        );
      }
    } finally {
      abortController.current = null;
      setIsStreaming(false);
    }
  }

  async function sendMessage(event?: FormEvent) {
    event?.preventDefault();
    const content = input.trim();
    if (!content || isStreaming) {
      return;
    }

    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    let conversationId = activeConversationId;
    if (!conversationId) {
      const created = await startNewChat();
      conversationId = created?.id || null;
    }
    if (conversationId) {
      await runGeneration(conversationId, content, false);
    }
  }

  async function regenerateLatest() {
    if (!activeConversationId || isStreaming) {
      return;
    }
    await runGeneration(activeConversationId, null, true);
  }

  async function renameChat(conversation: ConversationSummary) {
    const title = window.prompt("Rename conversation", conversation.title)?.trim();
    if (!title || title === conversation.title) {
      return;
    }
    try {
      const updated = await renameConversation(conversation.id, title);
      setConversations((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Could not rename this conversation.",
      );
    }
  }

  async function removeChat(conversation: ConversationSummary) {
    if (!window.confirm("Delete " + conversation.title + "?")) {
      return;
    }
    try {
      await deleteConversation(conversation.id);
      const remaining = conversations.filter((item) => item.id !== conversation.id);
      setConversations(remaining);
      if (activeConversationId === conversation.id) {
        setActiveConversationId(null);
        setMessages([]);
        if (remaining[0]) {
          await selectConversation(remaining[0].id);
        }
      }
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Could not delete this conversation.",
      );
    }
  }

  async function copyMessage(message: Message) {
    await navigator.clipboard.writeText(message.content);
    setCopiedId(message.id);
    window.setTimeout(() => setCopiedId(null), 1400);
  }

  function handleComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void sendMessage();
    }
  }

  function cycleTheme() {
    setTheme((current) =>
      current === "system" ? "light" : current === "light" ? "dark" : "system",
    );
  }

  const lastAssistantId = [...messages]
    .reverse()
    .find((message) => message.role === "assistant")?.id;

  return (
    <div className="app-shell">
      {mobileSidebarOpen && (
        <button
          className="mobile-backdrop"
          aria-label="Close navigation"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      <aside
        className={[
          "sidebar",
          sidebarOpen ? "" : "sidebar-collapsed",
          mobileSidebarOpen ? "sidebar-mobile-open" : "",
        ].join(" ")}
      >
        <div className="sidebar-top">
          <button
            className="brand"
            onClick={() => void startNewChat()}
            aria-label="Start a new chat"
          >
            <span className="brand-mark">
              <Sparkles size={18} />
            </span>
            <span className="brand-copy">
              <strong>RazaMind</strong>
              <small>Assistant</small>
            </span>
          </button>
          <button
            className="icon-button desktop-collapse"
            onClick={() => setSidebarOpen(false)}
            aria-label="Collapse sidebar"
          >
            <PanelLeftClose size={18} />
          </button>
          <button
            className="icon-button mobile-close"
            onClick={() => setMobileSidebarOpen(false)}
            aria-label="Close sidebar"
          >
            <X size={19} />
          </button>
        </div>

        <button className="new-chat-button" onClick={() => void startNewChat()}>
          <Plus size={18} />
          <span>New chat</span>
          <kbd>Ctrl K</kbd>
        </button>

        <label className="search-box">
          <Search size={16} />
          <input
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Search chats"
            aria-label="Search chats"
          />
        </label>

        <div className="chat-history">
          <p className="history-label">Recent</p>
          {filteredConversations.map((conversation) => (
            <div
              className={
                "history-item " +
                (conversation.id === activeConversationId ? "active" : "")
              }
              key={conversation.id}
            >
              <button
                className="history-select"
                onClick={() => void selectConversation(conversation.id)}
              >
                <MessageSquare size={16} />
                <span>{conversation.title}</span>
              </button>
              <div className="history-actions">
                <button
                  onClick={() => void renameChat(conversation)}
                  aria-label={"Rename " + conversation.title}
                >
                  <Pencil size={14} />
                </button>
                <button
                  onClick={() => void removeChat(conversation)}
                  aria-label={"Delete " + conversation.title}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
          {!isLoading && filteredConversations.length === 0 && (
            <p className="empty-history">
              {searchQuery ? "No matching chats" : "Your conversations appear here"}
            </p>
          )}
        </div>

        <div className="sidebar-footer">
          <div className="identity-summary">
            <div className="profile-avatar">
              {(identityProfile?.display_name || "Anonymous")
                .split(/\s+/)
                .slice(0, 2)
                .map((part) => part[0])
                .join("")
                .toUpperCase()}
            </div>
            <div className="identity-copy">
              <strong>{identityProfile?.display_name || "Anonymous browser"}</strong>
              <small>Anonymous LangSmith trace label</small>
            </div>
          </div>
          <p className="identity-notice">
            This browser label helps identify new LangSmith traces.
          </p>
        </div>
      </aside>

      {!sidebarOpen && (
        <button
          className="sidebar-restore"
          onClick={() => setSidebarOpen(true)}
          aria-label="Open sidebar"
        >
          <ChevronLeft size={18} />
        </button>
      )}

      <main className="main-panel">
        <header className="topbar">
          <button
            className="icon-button mobile-menu"
            onClick={() => setMobileSidebarOpen(true)}
            aria-label="Open navigation"
          >
            <Menu size={21} />
          </button>
          <div className="conversation-heading">
            <strong>{activeConversation?.title || "New conversation"}</strong>
            <span>
              <span className="status-dot" /> Groq · gpt-oss-120b
            </span>
          </div>
          <button
            className="theme-button"
            onClick={cycleTheme}
            aria-label={"Theme: " + theme}
            title={"Theme: " + theme}
          >
            {theme === "dark" ? (
              <Moon size={17} />
            ) : theme === "light" ? (
              <Sun size={17} />
            ) : (
              <Sparkles size={17} />
            )}
            <span>{theme}</span>
          </button>
        </header>

        <section className="conversation-area" aria-live="polite">
          {messages.length === 0 ? (
            <div className="welcome">
              <div className="welcome-mark">
                <Sparkles size={28} />
              </div>
              <p className="eyebrow">RAZAMIND</p>
              <h1>What can I help you create?</h1>
              <p className="welcome-copy">
                Think through ideas, learn something difficult, or turn a rough
                plan into a polished result.
              </p>
              <div className="suggestion-grid">
                {SUGGESTIONS.map((suggestion) => (
                  <button
                    key={suggestion.title}
                    onClick={() => {
                      setInput(suggestion.prompt);
                      textareaRef.current?.focus();
                    }}
                  >
                    <Sparkles size={16} />
                    <span>
                      <strong>{suggestion.title}</strong>
                      <small>{suggestion.prompt}</small>
                    </span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="message-list">
              {messages.map((message) => (
                <article
                  key={message.id}
                  className={"message-row " + message.role}
                >
                  <div className="message-avatar">
                    {message.role === "assistant" ? (
                      <Sparkles size={16} />
                    ) : (
                      "You"
                    )}
                  </div>
                  <div className="message-content">
                    <div className="message-author">
                      {message.role === "assistant"
                        ? "RazaMind"
                        : "You"}
                    </div>
                    {message.role === "assistant" ? (
                      message.content ? (
                        <div className="markdown">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              a: (props) => (
                                <a {...props} target="_blank" rel="noreferrer" />
                              ),
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        <div className="typing-indicator" aria-label="Thinking">
                          <span />
                          <span />
                          <span />
                        </div>
                      )
                    ) : (
                      <p className="user-copy">{message.content}</p>
                    )}
                    {message.role === "assistant" && message.content && (
                      <div className="message-toolbar">
                        <button onClick={() => void copyMessage(message)}>
                          {copiedId === message.id ? (
                            <Check size={15} />
                          ) : (
                            <Copy size={15} />
                          )}
                          {copiedId === message.id ? "Copied" : "Copy"}
                        </button>
                        {message.id === lastAssistantId && !isStreaming && (
                          <button onClick={() => void regenerateLatest()}>
                            <RefreshCw size={15} />
                            Regenerate
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </article>
              ))}
              <div ref={bottomRef} />
            </div>
          )}
        </section>

        <div className="composer-region">
          {error && (
            <div className="error-banner" role="alert">
              <span>{error}</span>
              <button onClick={() => setError(null)} aria-label="Dismiss error">
                <X size={16} />
              </button>
            </div>
          )}
          <form className="composer" onSubmit={(event) => void sendMessage(event)}>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onInput={(event) => {
                const target = event.currentTarget;
                target.style.height = "auto";
                target.style.height = Math.min(target.scrollHeight, 180) + "px";
              }}
              onKeyDown={handleComposerKeyDown}
              placeholder="Message RazaMind"
              rows={1}
              disabled={isStreaming}
              aria-label="Message"
            />
            {isStreaming ? (
              <button
                type="button"
                className="send-button stop"
                onClick={() => abortController.current?.abort()}
                aria-label="Stop generating"
              >
                <Square size={15} fill="currentColor" />
              </button>
            ) : (
              <button
                type="submit"
                className="send-button"
                disabled={!input.trim()}
                aria-label="Send message"
              >
                <Send size={18} />
              </button>
            )}
          </form>
          <p className="composer-note">
            AI can make mistakes. Check important information.
          </p>
        </div>
      </main>
    </div>
  );
}
