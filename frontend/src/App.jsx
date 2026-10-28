import { useEffect, useState } from "react";

import { Icon } from "./components/Icon.jsx";
import { AuthPage } from "./pages/AuthPage.jsx";
import { ChatPage } from "./pages/ChatPage.jsx";
import { api } from "./services/api.js";

const TOKEN_KEY = "knowledgepilot.access_token";

export default function App() {
  const [session, setSession] = useState(null);
  const [checkingSession, setCheckingSession] = useState(true);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let active = true;

    async function restoreSession() {
      const token = localStorage.getItem(TOKEN_KEY);
      if (!token) {
        setCheckingSession(false);
        return;
      }

      try {
        const user = await api.me(token);
        if (active) setSession({ token, user });
      } catch {
        localStorage.removeItem(TOKEN_KEY);
        if (active) setNotice("Please sign in again to continue.");
      } finally {
        if (active) setCheckingSession(false);
      }
    }

    restoreSession();
    return () => {
      active = false;
    };
  }, []);

  function signIn(authenticatedSession) {
    localStorage.setItem(TOKEN_KEY, authenticatedSession.access_token);
    setSession({
      token: authenticatedSession.access_token,
      user: authenticatedSession.user,
    });
    setNotice("");
  }

  function signOut() {
    localStorage.removeItem(TOKEN_KEY);
    setSession(null);
    setNotice("");
  }

  if (checkingSession) {
    return (
      <main className="loading-screen">
        <span className="loading-mark">
          <Icon name="sparkles" />
        </span>
      </main>
    );
  }

  if (!session) {
    return <AuthPage onAuthenticated={signIn} notice={notice} />;
  }

  return <ChatPage session={session} onSignOut={signOut} />;
}
