import {useEffect, useState} from "react";

const API_URL = "http://127.0.0.1:8000/api/v1/chat";

function App() {
  const [messages, setMessages] = useState(() => {
    const saved =localStorage.getItem("mh-chat-messages");
  return saved ? JSON.parse(saved): [];
});
const [input, setInput] = useState("");
const [loading, setLoading] = useState(false);

useEffect(()=> {
  localStorage.setItem('mh-chat-messages',JSON.stringify(messages));
},[messages])

const sendMessage = async () => {
  const trimmed = input.trim();
  if (!trimmed || loading) return;

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
        session_id: "demo-user", // you can later randomize this
        message: trimmed,
      }),
    });

    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      const detail = errBody.detail || res.statusText;
      throw new Error(detail);
    }

    const data = await res.json(); // ChatOut

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

const handleReset = () => {
  setMessages([]);
  localStorage.removeItem("mh-chat-messages");
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
                    <> / error: <strong>{m.meta.error}</strong></>
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
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type your message... (Enter = send, Shift+Enter = newline)"
        rows={3}
      />
      <button onClick={sendMessage} disabled={loading}>
        {loading ? "Sending..." : "Send"}
      </button>
    </footer>
  </div>
);
}

export default App;

