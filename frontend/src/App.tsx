import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import ChatPage from "./pages/ChatPage";
import Bibliotheque from "./pages/Bibliotheque";
import Meetings from "./pages/Meetings";
import Incidents from "./pages/Incidents";
import Projects from "./pages/Projects";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Navigate to="/chat" replace />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/chat/:conversationId" element={<ChatPage />} />
        <Route path="/bibliotheque" element={<Bibliotheque />} />
        <Route path="/reunions" element={<Meetings />} />
        <Route path="/incidents" element={<Incidents />} />
        <Route path="/projets" element={<Projects />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}