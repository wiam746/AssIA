import { useState, useEffect, FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { ShieldCheck, UserCheck, Lock, Mail, User, Check, X, Sparkles, FileText, KeyRound, Loader2 } from "lucide-react";
import api from "@/hooks/useApi";

export default function Login() {
  const [mode, setMode] = useState<"login" | "register">("login");

  // State Login
  const [loginUsername, setLoginUsername] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);

  // State Register
  const [fullName, setFullName] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [acceptedTerms, setAcceptedTerms] = useState(false);

  // General state
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showCguModal, setShowCguModal] = useState(false);

  // Forgot password state
  const [showForgotModal, setShowForgotModal] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotLoading, setForgotLoading] = useState(false);
  const [forgotMsg, setForgotMsg] = useState<string | null>(null);

  const { login, register } = useAuth();
  const navigate = useNavigate();

  // Load remembered username on mount
  useEffect(() => {
    const saved = localStorage.getItem("remembered_username");
    if (saved) {
      setLoginUsername(saved);
      setRememberMe(true);
    }
  }, []);

  async function handleLoginSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setLoading(true);

    if (rememberMe) {
      localStorage.setItem("remembered_username", loginUsername);
    } else {
      localStorage.removeItem("remembered_username");
    }

    try {
      await login(loginUsername, loginPassword);
      navigate("/chat");
    } catch {
      setError("Identifiant ou mot de passe incorrect.");
    } finally {
      setLoading(false);
    }
  }

  async function handleRegisterSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    if (!acceptedTerms) {
      setError("Vous devez accepter les conditions générales d'utilisation pour continuer.");
      return;
    }

    if (registerPassword !== confirmPassword) {
      setError("Les mots de passe ne correspondent pas.");
      return;
    }

    setLoading(true);
    try {
      await register(registerEmail, registerPassword, fullName || undefined);
      navigate("/chat");
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 409) {
        setError("Un compte avec cet email existe déjà. Connectez-vous.");
      } else {
        setError("Échec de la création du compte. Vérifiez vos informations.");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleForgotPasswordSubmit(e: FormEvent) {
    e.preventDefault();
    if (!forgotEmail.trim()) return;
    setForgotLoading(true);
    setForgotMsg(null);

    try {
      const res = await api.post("/auth/forgot-password", { email: forgotEmail.trim() });
      setForgotMsg(res.data?.message || "Un e-mail de réinitialisation vous a été envoyé.");
    } catch {
      setForgotMsg("Si l'adresse est associée à un compte, des instructions ont été envoyées.");
    } finally {
      setForgotLoading(false);
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-slate-50 px-4 py-12 selection:bg-emerald-100 selection:text-emerald-900">
      {/* Decorative background glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-emerald-400/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-teal-300/20 rounded-full blur-3xl pointer-events-none" />

      <div className="relative w-full max-w-md">
        {/* Logo and Header */}
        <div className="mb-6 text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-emerald-600 text-white shadow-lg shadow-emerald-600/30 mb-3">
            <Sparkles className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">AssIA</h1>
          <p className="mt-1 text-sm text-slate-500">
            Plateforme IA d'analyse de réunions & gestion d'incidents
          </p>
        </div>

        {/* Card */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-8 shadow-xl shadow-slate-200/60 backdrop-blur-sm">
          {/* Navigation Tabs */}
          <div className="flex rounded-xl bg-slate-100 p-1 mb-6">
            <button
              type="button"
              onClick={() => {
                setMode("login");
                setError(null);
                setSuccessMsg(null);
              }}
              className={`flex-1 rounded-lg py-2 text-xs font-semibold transition-all ${
                mode === "login"
                  ? "bg-white text-emerald-700 shadow-sm"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              Se connecter
            </button>
            <button
              type="button"
              onClick={() => {
                setMode("register");
                setError(null);
                setSuccessMsg(null);
              }}
              className={`flex-1 rounded-lg py-2 text-xs font-semibold transition-all ${
                mode === "register"
                  ? "bg-white text-emerald-700 shadow-sm"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              S'inscrire
            </button>
          </div>

          {/* Feedback messages */}
          {error && (
            <div className="mb-4 rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-700 flex items-start gap-2">
              <span className="font-bold">!</span>
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-800 flex items-start gap-2">
              <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* LOGIN FORM */}
          {mode === "login" && (
            <form onSubmit={handleLoginSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Identifiant ou E-mail
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    placeholder="ex: admin"
                    value={loginUsername}
                    onChange={(e) => setLoginUsername(e.target.value)}
                    required
                    className="w-full rounded-lg border border-slate-300 bg-slate-50/50 pl-9 pr-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Mot de passe
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="password"
                    placeholder="••••••••"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    required
                    className="w-full rounded-lg border border-slate-300 bg-slate-50/50 pl-9 pr-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between text-xs pt-1">
                <label className="flex items-center gap-2 cursor-pointer text-slate-600">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                  />
                  Se souvenir de moi
                </label>
                <button
                  type="button"
                  onClick={() => {
                    setShowForgotModal(true);
                    setForgotMsg(null);
                    setForgotEmail(loginUsername);
                  }}
                  className="text-emerald-700 hover:underline font-medium text-xs"
                >
                  Mot de passe oublié ?
                </button>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full mt-2 flex items-center justify-center gap-2 rounded-lg bg-emerald-600 py-2.5 px-4 text-sm font-semibold text-white shadow-md shadow-emerald-600/20 transition hover:bg-emerald-700 active:bg-emerald-800 disabled:opacity-50"
              >
                {loading ? (
                  <span>Connexion en cours...</span>
                ) : (
                  <>
                    <UserCheck className="w-4 h-4" />
                    <span>Se connecter</span>
                  </>
                )}
              </button>
            </form>
          )}

          {/* REGISTER FORM */}
          {mode === "register" && (
            <form onSubmit={handleRegisterSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Nom complet
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Jean Dupont"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                    className="w-full rounded-lg border border-slate-300 bg-slate-50/50 pl-9 pr-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Adresse e-mail
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="email"
                    placeholder="jean.dupont@entreprise.com"
                    value={registerEmail}
                    onChange={(e) => setRegisterEmail(e.target.value)}
                    required
                    className="w-full rounded-lg border border-slate-300 bg-slate-50/50 pl-9 pr-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Mot de passe
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="password"
                    placeholder="8+ caractères"
                    value={registerPassword}
                    onChange={(e) => setRegisterPassword(e.target.value)}
                    required
                    className="w-full rounded-lg border border-slate-300 bg-slate-50/50 pl-9 pr-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Confirmer le mot de passe
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="password"
                    placeholder="Confirmez votre mot de passe"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    className="w-full rounded-lg border border-slate-300 bg-slate-50/50 pl-9 pr-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition"
                  />
                </div>
              </div>

              {/* CHECKBOX CONDITIONS GENERALES */}
              <div className="rounded-lg border border-slate-200 bg-slate-50/80 p-3">
                <label className="flex items-start gap-2.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={acceptedTerms}
                    onChange={(e) => setAcceptedTerms(e.target.checked)}
                    className="mt-0.5 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500 h-4 w-4 shrink-0"
                  />
                  <span className="text-xs text-slate-600 leading-relaxed">
                    J'accepte expressément les{" "}
                    <button
                      type="button"
                      onClick={() => setShowCguModal(true)}
                      className="font-semibold text-emerald-700 hover:underline inline-flex items-center gap-0.5"
                    >
                      Conditions Générales d'Utilisation (CGU)
                      <FileText className="w-3 h-3 inline" />
                    </button>
                    {" "}et la politique de confidentialité.
                  </span>
                </label>
              </div>

              <button
                type="submit"
                disabled={loading || !acceptedTerms}
                className="w-full mt-2 flex items-center justify-center gap-2 rounded-lg bg-emerald-600 py-2.5 px-4 text-sm font-semibold text-white shadow-md shadow-emerald-600/20 transition hover:bg-emerald-700 active:bg-emerald-800 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <span>Création du compte...</span>
                ) : (
                  <>
                    <ShieldCheck className="w-4 h-4" />
                    <span>Créer mon compte</span>
                  </>
                )}
              </button>
            </form>
          )}
        </div>

        {/* Footer info */}
        <p className="mt-6 text-center text-xs text-slate-400">
          AssIA &copy; {new Date().getFullYear()} — Solution sécurisée certifiée RGPD
        </p>
      </div>

      {/* MODAL MOT DE PASSE OUBLIÉ */}
      {showForgotModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 animate-in fade-in">
          <div className="relative w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
              <div className="flex items-center gap-2 text-emerald-700">
                <KeyRound className="w-5 h-5" />
                <h3 className="text-base font-bold text-slate-900">
                  Réinitialisation du mot de passe
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowForgotModal(false)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleForgotPasswordSubmit} className="space-y-4">
              <p className="text-xs text-slate-600 leading-relaxed">
                Saisissez l'adresse e-mail ou l'identifiant associé à votre compte. Nous vous enverrons les instructions pour réinitialiser votre mot de passe.
              </p>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Adresse e-mail ou identifiant
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    placeholder="votre.email@entreprise.com"
                    value={forgotEmail}
                    onChange={(e) => setForgotEmail(e.target.value)}
                    required
                    className="w-full rounded-lg border border-slate-300 bg-slate-50/50 pl-9 pr-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition"
                  />
                </div>
              </div>

              {forgotMsg && (
                <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-800 flex items-start gap-2">
                  <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span>{forgotMsg}</span>
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowForgotModal(false)}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Fermer
                </button>
                <button
                  type="submit"
                  disabled={forgotLoading || !forgotEmail.trim()}
                  className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-emerald-700 flex items-center gap-2 disabled:opacity-50"
                >
                  {forgotLoading ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Envoi en cours...</span>
                    </>
                  ) : (
                    <span>Envoyer les instructions</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL CONDITIONS GENERALES */}
      {showCguModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="relative w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl border border-slate-200 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
              <div className="flex items-center gap-2 text-emerald-700">
                <FileText className="w-5 h-5" />
                <h3 className="text-base font-bold text-slate-900">
                  Conditions Générales d'Utilisation (CGU)
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowCguModal(false)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-4 text-xs text-slate-600 pr-2 leading-relaxed">
              <section>
                <h4 className="font-semibold text-slate-800 text-sm mb-1">1. Objet du service</h4>
                <p>
                  AssIA est un assistant intelligent dédié à la synthèse de réunions, le suivi d'incidents et la recherche documentaire d'entreprise.
                </p>
              </section>

              <section>
                <h4 className="font-semibold text-slate-800 text-sm mb-1">2. Confidentialité & Protection des données (RGPD)</h4>
                <p>
                  Les données stockées et analysées sur la plateforme demeurent la propriété stricte de votre organisation. Aucun document ni historique de conversation n'est transmis à des tiers non autorisés.
                </p>
              </section>

              <section>
                <h4 className="font-semibold text-slate-800 text-sm mb-1">3. Responsabilité de l'utilisateur</h4>
                <p>
                  L'utilisateur s'engage à ne pas transférer de contenus illicites ou malveillants et à conserver ses identifiants de manière strictement confidentielle.
                </p>
              </section>

              <section>
                <h4 className="font-semibold text-slate-800 text-sm mb-1">4. Modification des conditions</h4>
                <p>
                  AssIA se réserve le droit d'adapter à tout moment les présentes conditions afin de se conformer aux évolutions légales et techniques.
                </p>
              </section>
            </div>

            <div className="mt-6 border-t border-slate-100 pt-4 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowCguModal(false)}
                className="rounded-lg border border-slate-300 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
              >
                Fermer
              </button>
              <button
                type="button"
                onClick={() => {
                  setAcceptedTerms(true);
                  setShowCguModal(false);
                }}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-emerald-700 flex items-center gap-1.5"
              >
                <Check className="w-3.5 h-3.5" />
                J'accepte les CGU
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}