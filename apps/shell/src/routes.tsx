import { ReferenceLayout } from "@sceneenglish/app-core";
import { RequireAuth } from "@sceneenglish/app-core";
import {
  ActivityPage,
  AppShell,
  AuthCallbackPage,
  ChatCallPage,
  ChatImmersivePage,
  ChatNewPage,
  ChatSessionPage,
  GeneratePage,
  HomePage,
  LoginPage,
  ProfilePage,
  ProgressPage,
  ReferenceGrammarPage,
  ReferenceIndexPage,
  ReferencePhoneticsPage,
  RegisterPage,
  ScenarioDetailPage,
  ScenarioPracticePage,
  WordsPage,
} from "@sceneenglish/app-core";
import { Navigate, Route, Routes } from "react-router-dom";

function ReferencePhoneticsRoute() {
  return (
    <ReferenceLayout>
      <ReferencePhoneticsPage />
    </ReferenceLayout>
  );
}

function ReferenceGrammarRoute() {
  return (
    <ReferenceLayout>
      <ReferenceGrammarPage />
    </ReferenceLayout>
  );
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/profile" element={<RequireAuth><ProfilePage /></RequireAuth>} />
      <Route path="/words" element={<WordsPage />} />
      <Route path="/activity" element={<ActivityPage />} />
      <Route path="/progress" element={<RequireAuth><ProgressPage /></RequireAuth>} />
      <Route path="/generate" element={<RequireAuth><GeneratePage /></RequireAuth>} />
      <Route path="/reference" element={<ReferenceIndexPage />} />
      <Route path="/reference/phonetics" element={<ReferencePhoneticsRoute />} />
      <Route path="/reference/grammar" element={<ReferenceGrammarRoute />} />
      <Route path="/scenarios/:id" element={<ScenarioDetailPage />} />
      <Route path="/scenarios/:id/practice" element={<ScenarioPracticePage />} />
      <Route path="/chat/new" element={<RequireAuth><ChatNewPage /></RequireAuth>} />
      <Route path="/chat/:sessionId" element={<RequireAuth><ChatSessionPage /></RequireAuth>} />
      <Route path="/chat/:sessionId/immersive" element={<RequireAuth><ChatImmersivePage /></RequireAuth>} />
      <Route path="/chat/:sessionId/call" element={<RequireAuth><ChatCallPage /></RequireAuth>} />
      <Route path="/auth/callback" element={<AuthCallbackPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export function ShellApp() {
  return (
    <AppShell>
      <AppRoutes />
    </AppShell>
  );
}
