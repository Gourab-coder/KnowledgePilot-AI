import { useState } from "react";

import { Brand } from "../components/Brand.jsx";
import { Icon } from "../components/Icon.jsx";
import { api } from "../services/api.js";

export function AuthPage({ onAuthenticated, notice: initialNotice = "" }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(initialNotice);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");

    try {
      if (mode === "register") {
        await api.register({ email, password });
      }
      onAuthenticated(await api.login({ email, password }));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  function toggleMode() {
    setMode((currentMode) => (currentMode === "login" ? "register" : "login"));
    setError("");
  }

  return (
    <main className="auth-page">
      <div className="auth-glow auth-glow-one" />
      <div className="auth-glow auth-glow-two" />
      <Brand className="auth-brand" />

      <section className="auth-card">
        <div className="auth-icon">
          <Icon name="book" size={25} />
        </div>
        <p className="eyebrow">YOUR KNOWLEDGE, CONNECTED</p>
        <h1>{mode === "login" ? "Welcome back" : "Create your account"}</h1>
        <p className="auth-description">
          {mode === "login"
            ? "Sign in to pick up where you left off."
            : "Create an account to start chatting with your documents."}
        </p>

        <form className="auth-form" onSubmit={submit}>
          <label htmlFor="email">Email address</label>
          <input
            id="email"
            autoComplete="email"
            type="email"
            required
            maxLength={320}
            placeholder="you@example.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            type="password"
            required
            minLength={mode === "register" ? 10 : 1}
            maxLength={128}
            placeholder={mode === "register" ? "At least 10 characters" : "Your password"}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />

          {error && (
            <div className="inline-error" role="alert">
              {error}
            </div>
          )}

          <button className="primary-button auth-submit" type="submit" disabled={busy}>
            {busy ? "One moment…" : mode === "login" ? "Sign in" : "Create account"}
            {!busy && <Icon name="chevron" size={17} />}
          </button>
        </form>

        <p className="auth-switch">
          {mode === "login" ? "New to KnowledgePilot?" : "Already have an account?"}{" "}
          <button type="button" onClick={toggleMode}>
            {mode === "login" ? "Create an account" : "Sign in"}
          </button>
        </p>
      </section>

      <p className="auth-footnote">Private by design. Your documents stay yours.</p>
    </main>
  );
}
