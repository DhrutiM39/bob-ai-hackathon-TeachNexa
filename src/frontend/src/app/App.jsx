import React, { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppShell from '../components/layout/AppShell.jsx';
import LoadingState from '../components/common/LoadingState.jsx';

const Dashboard = lazy(() => import('../pages/Dashboard.jsx'));
const CreateCourse = lazy(() => import('../pages/CreateCourse.jsx'));
const CourseOverview = lazy(() => import('../pages/CourseOverview.jsx'));
const TopicLearning = lazy(() => import('../pages/TopicLearning.jsx'));
const QuizPage = lazy(() => import('../pages/QuizPage.jsx'));
const RevisionCenter = lazy(() => import('../pages/RevisionCenter.jsx'));

const PageFallback = () => (
  <div style={{ padding: '4rem', display: 'flex', justifyContent: 'center' }}>
    <LoadingState message="Loading page…" />
  </div>
);

export default function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <Suspense fallback={<PageFallback />}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/create" element={<CreateCourse />} />
            <Route path="/courses/:courseId" element={<CourseOverview />} />
            <Route path="/courses/:courseId/topics/:topicId" element={<TopicLearning />} />
            <Route path="/courses/:courseId/topics/:topicId/quiz" element={<QuizPage />} />
            <Route path="/courses/:courseId/revision" element={<RevisionCenter />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </AppShell>
    </BrowserRouter>
  );
}
