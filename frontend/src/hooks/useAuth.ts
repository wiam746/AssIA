import { useAuthContext } from "@/context/AuthContext";

/** Hook d'accès simplifié à l'authentification (relaie le AuthContext). */
export function useAuth() {
  return useAuthContext();
}