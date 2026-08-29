import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import api from "@/hooks/useApi";
import type { User } from "@/types";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem("access_token"));
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      return;
    }
    api
      .get<User>("/auth/me")
      .then((res) => setUser(res.data))
      .catch(() => {
        localStorage.removeItem("access_token");
        setToken(null);
      })
      .finally(() => setIsLoading(false));
  }, [token]);

  async function login(username: string, password: string) {
    const res = await api.post("/auth/login", { username, password });
    const accessToken = res.data.access_token as string;
    localStorage.setItem("access_token", accessToken);
    setToken(accessToken);
  }

  async function register(email: string, password: string, fullName?: string) {
    const res = await api.post("/auth/register", {
      email,
      password,
      full_name: fullName ?? null,
    });
    const accessToken = res.data.access_token as string;
    localStorage.setItem("access_token", accessToken);
    setToken(accessToken);
  }

  function logout() {
    localStorage.removeItem("access_token");
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuthContext() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuthContext doit être utilisé dans un AuthProvider");
  return ctx;
}