import { Route, Routes } from "react-router-dom";

import Layout from "./components/Layout.jsx";
import Album from "./pages/Album.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Duplicates from "./pages/Duplicates.jsx";
import Missing from "./pages/Missing.jsx";
import Nearby from "./pages/Nearby.jsx";
import Search from "./pages/Search.jsx";
import Trades from "./pages/Trades.jsx";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
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
