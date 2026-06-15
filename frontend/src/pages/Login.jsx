import { useEffect, useRef, useState } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";

export default function Login() {
  const { user, loading, login } = useAuth();
  const buttonRef = useRef(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (loading || user) return;

    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    if (!clientId) {
      setError("Falta configurar VITE_GOOGLE_CLIENT_ID.");
      return;
    }

    let cancelled = false;

    const renderButton = () => {
      if (cancelled) return;
      if (!window.google?.accounts?.id || !buttonRef.current) {
        setTimeout(renderButton, 100);
        return;
      }

      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: async (response) => {
          try {
            await login(response.credential);
          } catch (err) {
            setError(err.message);
          }
        },
      });

      window.google.accounts.id.renderButton(buttonRef.current, {
        theme: "outline",
        size: "large",
        text: "continue_with",
        width: 280,
      });
    };

    renderButton();

    return () => {
      cancelled = true;
    };
  }, [loading, user, login]);

  if (!loading && user) return <Navigate to="/" replace />;

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-gray-50 p-6 text-center">
      <div className="flex flex-col items-center gap-2">
        <h1 className="text-2xl font-bold text-gray-800">StickerControl 2026</h1>
        <p className="text-sm text-gray-600">
          Iniciá sesión con Google para ver tu álbum y tu colección.
        </p>
      </div>

      <div ref={buttonRef} />

      {error && <p className="text-faltante">{error}</p>}
    </div>
  );
}
