import React, { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import styles from './RevisionCenter.module.css';
import { useRevision, useGenerateRevision } from '../hooks/useQuiz.js';
import { useCourse } from '../hooks/useCourses.js';
import { ROUTES } from '../constants/index.js';
import RevisionCard from '../components/revision/RevisionCard.jsx';
import QuestionBankList from '../components/revision/QuestionBankList.jsx';
import QuizCard from '../components/quiz/QuizCard.jsx';
import Button from '../components/common/Button.jsx';
import LoadingState from '../components/common/LoadingState.jsx';
import ErrorState from '../components/common/ErrorState.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import PageHeader from '../components/layout/PageHeader.jsx';

const TABS = [
  { id: 'notes',     label: 'Quick Notes' },
  { id: 'takeaways', label: 'Key Takeaways' },
  { id: 'practice',  label: 'Practice Questions' },
  { id: 'bank',      label: 'Question Bank' },
];

export default function RevisionCenter() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('notes');
  const { data: course } = useCourse(courseId);
  const { data: revision, isLoading, isError, error, refetch } = useRevision(courseId);
  const generate = useGenerateRevision(courseId);

  const handleGenerate = () => generate.mutate();

  return (
    <div className={styles.page}>
      <PageHeader
        title="Revision Center"
        subtitle={course ? `${course.title}` : undefined}
        breadcrumb={
          <>
            <Link to={ROUTES.DASHBOARD}>Dashboard</Link>
            <span aria-hidden="true">›</span>
            <Link to={ROUTES.COURSE_OVERVIEW(courseId)}>{course?.title ?? 'Course'}</Link>
            <span aria-hidden="true">›</span>
            <span aria-current="page">Revision Center</span>
          </>
        }
        actions={
          <Button variant="secondary" size="sm" onClick={handleGenerate} loading={generate.isPending}>
            Regenerate
          </Button>
        }
      />

      {isLoading && <LoadingState message="Loading revision materials…" size="lg" />}
      {isError && <ErrorState title="Couldn't load revision" message={error?.message} onRetry={refetch} />}
      {generate.isError && <ErrorState title="Generation failed" message={generate.error?.message} onRetry={handleGenerate} />}

      {!isLoading && !isError && !revision && (
        <EmptyState
          icon="🔁"
          title="Revision materials not yet generated"
          description="Generate revision notes, key takeaways, and a question bank for this course."
          actionLabel="Generate Revision Materials"
          onAction={handleGenerate}
        />
      )}

      {!isLoading && revision && (
        <>
          {/* Tab bar */}
          <div className={styles.tabBar} role="tablist" aria-label="Revision sections">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                role="tab"
                className={`${styles.tab} ${activeTab === tab.id ? styles.tabActive : ''}`}
                onClick={() => setActiveTab(tab.id)}
                aria-selected={activeTab === tab.id}
                aria-controls={`tabpanel-${tab.id}`}
                id={`tab-${tab.id}`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab panels */}
          <div
            role="tabpanel"
            id={`tabpanel-${activeTab}`}
            aria-labelledby={`tab-${activeTab}`}
            className={styles.panel}
          >
            {activeTab === 'notes' && (
              <RevisionCard
                title="Quick Revision Notes"
                items={revision.quickNotes}
                variant="notes"
              />
            )}

            {activeTab === 'takeaways' && (
              <RevisionCard
                title="Key Takeaways"
                items={revision.keyTakeaways}
                variant="takeaways"
              />
            )}

            {activeTab === 'practice' && (
              <div className={styles.practiceList}>
                <h3 className={styles.subheading}>Practice Questions</h3>
                {revision.practiceQuestions?.length ? (
                  revision.practiceQuestions.map((q, i) => (
                    <QuizCard
                      key={q.id ?? i}
                      question={q}
                      selectedIndex={q.correctIndex}
                      showFeedback={true}
                    />
                  ))
                ) : (
                  <p className={styles.empty}>No practice questions available.</p>
                )}
              </div>
            )}

            {activeTab === 'bank' && (
              <div>
                <h3 className={styles.subheading}>Question Bank</h3>
                <p className={styles.bankNote}>
                  Click "Show answer" to reveal the correct answer and explanation.
                </p>
                <QuestionBankList questions={revision.questionBank} />
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
