import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";
import {
  IconAlbum,
  IconAlert,
  IconHome,
  IconLayers,
  IconMapPin,
  IconSearch,
  IconSwap,
} from "./icons.jsx";

const NAV_ITEMS = [
  { to: "/", label: "Inicio", icon: IconHome },
  { to: "/buscar", label: "Buscar", icon: IconSearch },
  { to: "/album", label: "Álbum", icon: IconAlbum },
  { to: "/faltantes", label: "Faltantes", icon: IconAlert },
  { to: "/repetidas", label: "Repetidas", icon: IconLayers },
  { to: "/intercambios", label: "Cambios", icon: IconSwap },
  { to: "/cerca", label: "Cerca", icon: IconMapPin },
];

export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      <header className="flex items-center justify-between border-b border-gray-100 bg-white p-3 md:mx-auto md:w-full md:max-w-2xl">
        <span className="text-sm font-bold text-gray-800">StickerControl 2026</span>
        {user && (
          <div className="flex items-center gap-2">
            {user.avatar && (
              <img src={user.avatar} alt={user.name} className="h-6 w-6 rounded-full" />
            )}
            <span className="max-w-[96px] truncate text-xs font-semibold text-gray-600">
              {user.name}
            </span>
            <button
              type="button"
              onClick={logout}
              className="text-xs font-bold text-gray-400 active:text-gray-600"
            >
              Salir
            </button>
          </div>
        )}
      </header>

      <main className="w-full flex-1 p-4 pb-28 md:mx-auto md:max-w-2xl md:pb-24">
        <Outlet />
      </main>

      <nav className="fixed bottom-0 left-0 right-0 border-t border-gray-100 bg-white shadow-[0_-2px_12px_rgba(0,0,0,0.06)]">
        <div className="mx-auto grid grid-cols-7 md:max-w-2xl">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex flex-col items-center justify-center gap-1 py-2.5 text-xs font-semibold leading-tight transition-colors md:gap-0.5 md:py-2 md:text-[10px] ${
                    isActive ? "text-green-600" : "text-gray-400"
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <span
                      className={`flex h-9 w-9 items-center justify-center rounded-full transition-colors md:h-7 md:w-7 ${
                        isActive ? "bg-green-100" : ""
                      }`}
                    >
                      <Icon className="h-6 w-6 md:h-5 md:w-5" />
                    </span>
                    {item.label}
                  </>
                )}
              </NavLink>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
