import { NavLink, Outlet } from "react-router-dom";

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
  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      <main className="mx-auto flex-1 w-full max-w-2xl p-4 pb-24">
        <Outlet />
      </main>

      <nav className="fixed bottom-0 left-0 right-0 border-t border-gray-100 bg-white shadow-[0_-2px_12px_rgba(0,0,0,0.06)]">
        <div className="mx-auto grid max-w-2xl grid-cols-7">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex flex-col items-center justify-center gap-0.5 py-2 text-[10px] font-semibold leading-tight transition-colors ${
                    isActive ? "text-green-600" : "text-gray-400"
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <span
                      className={`flex h-7 w-7 items-center justify-center rounded-full transition-colors ${
                        isActive ? "bg-green-100" : ""
                      }`}
                    >
                      <Icon className="h-5 w-5" />
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
