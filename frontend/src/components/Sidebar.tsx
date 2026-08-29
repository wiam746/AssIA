import { useEffect, useState } from "react";
import { NavLink, useNavigate, useLocation } from "react-router-dom";
import {
  MessageSquare,
  FolderOpen,
  Users,
  AlertTriangle,
  Briefcase,
  LogOut,
  Sparkles,
  Plus,
  Trash2,
  Clock,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import api from "@/hooks/useApi";
import type { Conversation } from "@/types";

const links = [
  { to: "/chat", label: "Chat IA", icon: MessageSquare },
  { to: "/bibliotheque", label: "Bibliothèque", icon: FolderOpen },
  { to: "/reunions", label: "Réunions", icon: Users },
  { to: "/incidents", label: "Incidents", icon: AlertTriangle },
  { to: "/projets", label: "Projets", icon: Briefcase },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Charger l'historique des conversations
  useEffect(() => {
    fetchConversations();
  }, [location.pathname]);

  async function fetchConversations() {
    setLoadingHistory(true);
    try {
      const res = await api.get<Conversation[]>("/chat/conversations");
      setConversations(res.data);
    } catch {
      // Ignore if unauthorized or network issue
    } finally {
      setLoadingHistory(false);
    }
  }

  async function handleDeleteConversation(e: React.MouseEvent, id: string) {
    e.stopPropagation();
    e.preventDefault();
    try {
      await api.delete(`/chat/conversations/${id}`);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (location.pathname === `/chat/${id}`) {
        navigate("/chat");
      }
    } catch {
      // Error handling
    }
  }

  return (
    <aside className="flex h-screen w-64 flex-col justify-between border-r border-slate-200 bg-white px-4 py-5 shadow-sm select-none">
      <div className="flex flex-col min-h-0 flex-1">
        {/* Logo & Title */}
        <div className="mb-5 flex items-center gap-2.5 px-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-600 text-white shadow-sm">
            <Sparkles size={18} />
          </div>
          <div>
            <div className="text-base font-bold text-slate-900 leading-tight">AssIA</div>
            <div className="text-[10px] text-emerald-600 font-semibold tracking-wide uppercase">
             
            </div>
          </div>
        </div>

        {/* Primary Navigation Links */}
        <nav className="space-y-1 mb-6 shrink-0">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/chat"}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-xs font-semibold transition-all ${
                  isActive
                    ? "bg-emerald-50 text-emerald-700 shadow-sm border border-emerald-200/60"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                }`
              }
            >
              <Icon size={17} className="shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Chat History Section */}
        <div className="flex flex-col flex-1 min-h-0 border-t border-slate-100 pt-4">
          <div className="flex items-center justify-between px-2 mb-2">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Clock size={12} />
              Historique du chat
            </span>
            <button
              onClick={() => navigate("/chat")}
              title="Nouvelle discussion"
              className="flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-1 text-[11px] font-bold text-emerald-700 hover:bg-emerald-100 border border-emerald-200 transition"
            >
              <Plus size={13} />
              <span>Nouveau</span>
            </button>
          </div>

          <div className="flex-1 overflow-y-auto space-y-1 pr-1">
            {loadingHistory && conversations.length === 0 ? (
              <div className="p-2 text-[11px] text-slate-400 text-center">Chargement...</div>
            ) : conversations.length === 0 ? (
              <div className="p-3 text-[11px] text-slate-400 text-center rounded-lg bg-slate-50 border border-dashed border-slate-200">
                Aucune conversation récente.
              </div>
            ) : (
              conversations.map((c) => {
                const isActive = location.pathname === `/chat/${c.id}`;
                return (
                  <div
                    key={c.id}
                    onClick={() => navigate(`/chat/${c.id}`)}
                    className={`group flex items-center justify-between rounded-lg px-2.5 py-2 text-xs transition cursor-pointer ${
                      isActive
                        ? "bg-emerald-50/80 text-emerald-800 font-semibold border border-emerald-200/60"
                        : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                    }`}
                  >
                    <div className="flex items-center gap-2 overflow-hidden mr-2">
                      <MessageSquare size={14} className="shrink-0 text-slate-400 group-hover:text-emerald-600" />
                      <span className="truncate text-xs">{c.title || "Nouvelle conversation"}</span>
                    </div>
                    <button
                      onClick={(e) => handleDeleteConversation(e, c.id)}
                      title="Supprimer la conversation"
                      className="opacity-0 group-hover:opacity-100 shrink-0 text-slate-400 hover:text-red-600 p-0.5 transition"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* User Profile & Logout */}
      <div className="mt-4 space-y-2 rounded-xl border border-slate-100 bg-slate-50/80 p-3 shrink-0">
        <div className="truncate text-xs font-semibold text-slate-700">
          {user?.full_name || user?.email || "Utilisateur"}
        </div>
        <div className="truncate text-[11px] text-slate-400">{user?.email}</div>
        <button
          onClick={logout}
          className="flex w-full items-center gap-2 text-xs font-semibold text-red-600 hover:text-red-700 pt-1 transition"
        >
          <LogOut size={15} />
          Se déconnecter
        </button>
      </div>
    </aside>
  );
}