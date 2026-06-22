import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "@/features/auth/context/AuthContext";
import { RedirectIfAuthed } from "@/features/auth/guards/RedirectIfAuthed";
import { RequireAuth } from "@/features/auth/guards/RequireAuth";
import AppLayout from "@/pages/app/AppLayout";
import AppIndexPage from "@/pages/app/AppIndexPage";
import ChatPage from "@/pages/app/ChatPage";
import DocumentsPage from "@/pages/app/DocumentsPage";
import SettingsPage from "@/pages/app/SettingsPage";
import AuthCallbackPage from "@/pages/auth/AuthCallbackPage";
import LoginPage from "@/pages/auth/LoginPage";
import RegisterPage from "@/pages/auth/RegisterPage";
import LandingPage from "@/pages/landing/LandingPage";
import OnboardingPage from "@/pages/onboarding/OnboardingPage";
import NotFound from "@/pages/NotFound";

export function AppRouter() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route element={<RedirectIfAuthed />}>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
          </Route>

          <Route path="/auth/callback" element={<AuthCallbackPage />} />

          <Route element={<RequireAuth />}>
            <Route path="/onboarding" element={<OnboardingPage />} />
            <Route path="/app" element={<AppLayout />}>
              <Route index element={<AppIndexPage />} />
              <Route path="chats/:chatId" element={<ChatPage />} />
              <Route path="documents" element={<DocumentsPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>
          </Route>

          <Route path="/404" element={<NotFound />} />
          <Route path="*" element={<Navigate to="/404" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
