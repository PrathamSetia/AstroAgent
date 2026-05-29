import { useState, useRef, useEffect } from "react";
import axios from "axios";
import "./App.css";

const API = "http://localhost:8000";

// ── Birth Details Form ────────────────────────────────────────────────────────
function BirthForm({ onSubmit, onSkip }) {
  const [form, setForm] = useState({ date: "", time: "", place: "" });
  const [error, setError] = useState("");

  const validate = () => {
    if (!form.date) return "Please enter your birth date.";
    if (!form.place) return "Please enter your birth place.";
    const d = new Date(form.date);
    if (isNaN(d)) return "Invalid date format.";
    if (d > new Date()) return "Birth date cannot be in the future.";
    return "";
  };

  const handleSubmit = () => {
    const err = validate();
    if (err) { setError(err); return; }
    setError("");
    onSubmit(form);
  };

  return (
    <div className="birth-form-overlay">
      <div className="birth-form">
        <h2>✦ Welcome to Aradhana</h2>
        <p>Your daily spiritual companion. Share your birth details to unlock your personal chart and daily guidance.</p>

        <div className="form-group">
          <label>Date of Birth</label>
          <input type="date" value={form.date}
            onChange={e => setForm({ ...form, date: e.target.value })} />
        </div>

        <div className="form-group">
          <label>Time of Birth</label>
          <input type="time" value={form.time}
            onChange={e => setForm({ ...form, time: e.target.value })} />
          <div className="hint">Leave blank if unknown — chart will be approximate</div>
        </div>

        <div className="form-group">
          <label>Place of Birth</label>
          <input type="text" placeholder="e.g. Mumbai, India"
            value={form.place}
            onChange={e => setForm({ ...form, place: e.target.value })}
            onKeyDown={e => e.key === "Enter" && handleSubmit()} />
        </div>

        {error && <div className="form-error">{error}</div>}

        <button className="btn-primary" onClick={handleSubmit}>
          Reveal My Chart ✦
        </button>
        <button className="btn-skip" onClick={onSkip}>
          Skip for now — just chat
        </button>
      </div>
    </div>
  );
}

// ── Message bubble ────────────────────────────────────────────────────────────
function MessageBubble({ message }) {
  return (
    <div className={`message ${message.role}`}>
      <div className="message-bubble">{message.content}</div>
      {message.tools_used?.length > 0 && (
        <div className="tools-used">
          ✦ used: {message.tools_used.join(", ")}
        </div>
      )}
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [screen, setScreen] = useState("form"); // "form" | "chat"
  const [birthDetails, setBirthDetails] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingText, loading]);

  const handleBirthSubmit = async (details) => {
    setBirthDetails(details);
    setScreen("chat");
    const timeStr = details.time || "unknown time";
    const intro = `I was born on ${details.date} at ${timeStr} in ${details.place}. Please compute my birth chart and give me a brief reading.`;
    await sendMessage(intro, details);
  };

  const handleSkip = () => {
    setScreen("chat");
    setMessages([{
      role: "assistant",
      content: "Namaste ✦ I'm Aradhana, your astrology companion. You can ask me anything about astrology, or share your birth details whenever you're ready.",
      tools_used: []
    }]);
  };

  const sendMessage = async (text, details = birthDetails) => {
    if (!text.trim() || loading) return;

    const userMsg = { role: "user", content: text };
    const history = [...messages, userMsg];
    setMessages(history);
    setInput("");
    setLoading(true);
    setStreamingText("");

    try {
      // Build payload
      const payload = {
        messages: history.map(m => ({ role: m.role, content: m.content })),
        birth_details: details || {},
        chart_data: {}
      };

      // Try streaming first
      const response = await fetch(`${API}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullText = "";
      let toolsUsed = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === "token") {
              fullText += data.content;
              setStreamingText(fullText);
            } else if (data.type === "tools_used") {
              toolsUsed = data.tools;
            } else if (data.type === "done") {
              setMessages(prev => [...prev, {
                role: "assistant",
                content: fullText,
                tools_used: toolsUsed
              }]);
              setStreamingText("");
            } else if (data.type === "error") {
              throw new Error(data.message);
            }
          } catch (e) { /* skip malformed chunks */ }
        }
      }

    } catch (err) {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "I'm sorry, something went wrong. Please try again.",
        tools_used: []
      }]);
      setStreamingText("");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="app">
      <div className="header">
        <div className="header-star">✦</div>
        <div>
          <h1>ARADHANA</h1>
          <p>YOUR DAILY SPIRITUAL COMPANION</p>
        </div>
      </div>

      {screen === "form" ? (
        <BirthForm onSubmit={handleBirthSubmit} onSkip={handleSkip} />
      ) : (
        <div className="chat-container">
          {birthDetails && (
            <div className="chart-banner">
              ✦ Chart loaded for {birthDetails.place} · {birthDetails.date}
            </div>
          )}

          <div className="messages">
            {messages.map((m, i) => <MessageBubble key={i} message={m} />)}

            {streamingText && (
              <div className="message assistant">
                <div className="message-bubble">{streamingText}</div>
              </div>
            )}

            {loading && !streamingText && (
              <div className="message assistant">
                <div className="typing-indicator">
                  <div className="dot" /><div className="dot" /><div className="dot" />
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          <div className="input-bar">
            <textarea
              rows={1}
              placeholder="Ask Aradhana anything…"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />
            <button className="btn-send" onClick={() => sendMessage(input)} disabled={loading || !input.trim()}>
              ➤
            </button>
          </div>
        </div>
      )}
    </div>
  );
}