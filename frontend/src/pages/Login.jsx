import { useEffect, useRef, useState } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";
import { DEMO_MODE } from "../demo.js";

const GSI_SRC = "https://accounts.google.com/gsi/client";

// El script de Google Identity Services se carga solo fuera del modo demo,
// así la demo no hace ninguna llamada a Google.
function loadGoogleScript() {
  if (document.querySelector(`script[src="${GSI_SRC}"]`)) return;
  const script = document.createElement("script");
  script.src = GSI_SRC;
  script.async = true;
  script.defer = true;
  document.head.appendChild(script);
}

export default function Login() {
  const { user, loading } = useAuth();

  if (!loading && user) return <Navigate to="/" replace />;

  return DEMO_MODE ? <DemoLogin /> : <GoogleLogin />;
}

function DemoLogin() {
  const { loginDemo } = useAuth();
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState(null);

  const handleStart = async () => {
    setStarting(true);
    setError(null);
    try {
      await loginDemo();
    } catch (err) {
      setError(
        err.status === 429
          ? "Se crearon muchas demos desde tu conexión. Probá de nuevo en unos minutos."
          : "No se pudo iniciar la demo. Probá de nuevo."
      );
      setStarting(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-gray-50 p-6 text-center">
      <div className="flex max-w-sm flex-col items-center gap-2">
        <h1 className="text-2xl font-bold text-gray-800">StickerControl 2026</h1>
        <p className="text-sm text-gray-600">
          Probá la plataforma con un álbum de ejemplo: marcá figuritas, revisá faltantes y
          repetidas, y calculá intercambios con coleccionistas ficticios.
        </p>
      </div>

      <button
        type="button"
        onClick={handleStart}
        disabled={starting}
        className="rounded-xl bg-pegada px-6 py-3 text-lg font-bold text-white disabled:opacity-50"
      >
        {starting ? "Preparando tu álbum..." : "Probar la demo"}
      </button>

      <p className="max-w-sm text-xs text-gray-500">
        Sin registro. Todos los datos son ficticios y tu álbum de prueba se borra automáticamente.
      </p>

      {error && <p className="text-faltante">{error}</p>}
    </div>
  );
}

function GoogleLogin() {
  const { login } = useAuth();
  const buttonRef = useRef(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    if (!clientId) {
      setError("Falta configurar VITE_GOOGLE_CLIENT_ID.");
      return;
    }

    loadGoogleScript();
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
  }, [login]);

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
