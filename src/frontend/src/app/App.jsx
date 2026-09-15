import React, { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AppShell from '../components/layout/AppShell.jsx';
import LoadingState from '../components/common/LoadingState.jsx';
import { useAuthStore } from '../store/useAuthStore.js';

const Dashboard = lazy(() => import('../pages/Dashboard.jsx'));
const CreateCourse = lazy(() => import('../pages/CreateCourse.jsx'));
const CourseModules = lazy(() => import('../pages/CourseModules.jsx'));
const CourseOverview = lazy(() => import('../pages/CourseOverview.jsx'));
const TopicLearning = lazy(() => import('../pages/TopicLearning.jsx'));
const QuizPage = lazy(() => import('../pages/QuizPage.jsx'));
const RevisionCenter = lazy(() => import('../pages/RevisionCenter.jsx'));
const LoginPage = lazy(() => import('../pages/LoginPage.jsx'));
const SignupPage = lazy(() => import('../pages/SignupPage.jsx'));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
});

const PageFallback = () => (
  <div style={{ padding: '4rem', display: 'flex', justifyContent: 'center' }}>
    <LoadingState message="Loading page…" />
  </div>
);

function ProtectedRoute({ children }) {
  const token = useAuthStore((s) => s.token);
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

function PublicRoute({ children }) {
  const token = useAuthStore((s) => s.token);
  if (token) return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Suspense fallback={<PageFallback />}>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
            <Route path="/signup" element={<PublicRoute><SignupPage /></PublicRoute>} />

            {/* Protected routes — wrapped in AppShell */}
            <Route path="/" element={<ProtectedRoute><AppShell><Dashboard /></AppShell></ProtectedRoute>} />
            <Route path="/create" element={<ProtectedRoute><AppShell><CreateCourse /></AppShell></ProtectedRoute>} />
            <Route path="/courses/:courseId/modules" element={<ProtectedRoute><AppShell><CourseModules /></AppShell></ProtectedRoute>} />
            <Route path="/courses/:courseId" element={<ProtectedRoute><AppShell><CourseOverview /></AppShell></ProtectedRoute>} />
            <Route path="/courses/:courseId/topics/:topicId" element={<ProtectedRoute><AppShell><TopicLearning /></AppShell></ProtectedRoute>} />
            <Route path="/courses/:courseId/topics/:topicId/quiz" element={<ProtectedRoute><AppShell><QuizPage /></AppShell></ProtectedRoute>} />
            <Route path="/courses/:courseId/revision" element={<ProtectedRoute><AppShell><RevisionCenter /></AppShell></ProtectedRoute>} />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
