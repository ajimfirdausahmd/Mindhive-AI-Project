import { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:8000/api/v1/chat";

const QUICK_ACTIONS = [
  { cmd: "/calc ", label: "Calculator" },
  { cmd: "/products ", label: "Products" },
  { cmd: "/outlets ", label: "Outlets" },
  { cmd: "/reset", label: "Reset conversation" },
];

function App() {
  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem("mh-chat-messages");
    return saved ? JSON.parse(saved) : [];
  });
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState(QUICK_ACTIONS);

  useEffect(() => {
    localStorage.setItem("mh-chat-messages", JSON.stringify(messages));
  }, [messages]);

  const handleReset = () => {
    setMessages([]);
    localStorage.removeItem("mh-chat-messages");
  };

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    if (trimmed === "/reset") {
      handleReset();
      setInput("");
      return;
    }

    const userMsg = {
      id: Date.now(),
      role: "user",
      text: trimmed,
      meta: null,
      time: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: "demo-user", 
          message: trimmed,
        }),
      });

      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        const detail = errBody.detail || res.statusText;
        throw new Error(detail);
      }

      const data = await res.json(); 

      const botMsg = {
        id: Date.now() + 1,
        role: "bot",
        text: data.reply,
        meta: {
          intent: data.intent,
          tool: data.tool,
          error: data.error,
          slots: data.slots,
        },
        time: new Date().toLocaleTimeString(),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      const botMsg = {
        id: Date.now() + 1,
        role: "bot",
        text: "Sorry, something went wrong calling the chat API.",
        meta: { error: String(err) },
        time: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, botMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleInputChange = (e) => {
    const val = e.target.value;
    setInput(val);

    if (val.startsWith("/")) {
      const lower = val.toLowerCase();
      setSuggestions(
        QUICK_ACTIONS.filter((q) =>
          q.cmd.toLowerCase().startsWith(lower)
        )
      );
    } else {
      setSuggestions(QUICK_ACTIONS);
    }
  };

  const handleQuickActionClick = (cmd) => {
    setInput(cmd);
    if (cmd.startsWith("/")) {
      const lower = cmd.toLowerCase();
      setSuggestions(
        QUICK_ACTIONS.filter((q) =>
          q.cmd.toLowerCase().startsWith(lower)
        )
      );
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Mindhive Chat</h1>
        <button onClick={handleReset}>/reset</button>
      </header>

      <main className="chat-window">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`msg-row ${m.role === "user" ? "user" : "bot"}`}
          >
            <div className="avatar">
              {m.role === "user" ? "🧑" : "🤖"}
            </div>
            <div className="bubble">
              <div className="text">{m.text}</div>
              <div className="meta">
                <span>{m.time}</span>
                {m.meta && (m.meta.intent || m.meta.tool || m.meta.error) && (
                  <span>
                    {" · "}
                    intent: {m.meta.intent || "–"} / tool: {m.meta.tool || "–"}
                    {m.meta.error && (
                      <>
                        {" "}
                        / error: <strong>{m.meta.error}</strong>
                      </>
                    )}
                  </span>
                )}
              </div>
              {m.meta && m.meta.slots && (
                <pre className="slots">
                  slots: {JSON.stringify(m.meta.slots, null, 2)}
                </pre>
              )}
            </div>
          </div>
        ))}
        {messages.length === 0 && (
          <div className="empty-hint">
            Type a message, e.g. “Is there an outlet in Petaling Jaya?”
          </div>
        )}
      </main>

      <footer className="composer">
        <div className="quick-actions-bar">
          {suggestions.map((q) => (
            <button
              key={q.cmd}
              type="button"
              className="quick-action-btn"
              onClick={() => handleQuickActionClick(q.cmd)}
            >
              <span className="quick-action-cmd">{q.cmd}</span>
              <span className="quick-action-label">{q.label}</span>
            </button>
          ))}
        </div>

        <div className="composer-main">
          <textarea
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Type your message... (Enter = send, Shift+Enter = newline, try /calc)"
            rows={3}
          />
          <button onClick={sendMessage} disabled={loading}>
            {loading ? "Sending..." : "Send"}
          </button>
        </div>
      </footer>
    </div>
  );
}

export default App;

