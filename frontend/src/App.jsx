import { Navigate, Route, Routes } from "react-router-dom";

import Layout from "./components/Layout.jsx";
import { useAuth } from "./context/AuthContext.jsx";
import Album from "./pages/Album.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Duplicates from "./pages/Duplicates.jsx";
import Login from "./pages/Login.jsx";
import Missing from "./pages/Missing.jsx";
import Nearby from "./pages/Nearby.jsx";
import Search from "./pages/Search.jsx";
import Trades from "./pages/Trades.jsx";

function PrivateRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) return <p className="p-4 text-gray-500">Cargando...</p>;
  if (!user) return <Navigate to="/login" replace />;

  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/buscar" element={<Search />} />
        <Route path="/album" element={<Album />} />
        <Route path="/faltantes" element={<Missing />} />
        <Route path="/repetidas" element={<Duplicates />} />
        <Route path="/intercambios" element={<Trades />} />
        <Route path="/cerca" element={<Nearby />} />
      </Route>
    </Routes>
  );
}
