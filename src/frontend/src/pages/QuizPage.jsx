import React, { useState, useCallback } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import styles from './QuizPage.module.css';
import { useQuiz, useGenerateQuiz } from '../hooks/useQuiz.js';
import { useCourse } from '../hooks/useCourses.js';
import { ROUTES } from '../constants/index.js';
import QuizQuestion from '../components/quiz/QuizQuestion.jsx';
import QuizCard from '../components/quiz/QuizCard.jsx';
import ScoreCard from '../components/quiz/ScoreCard.jsx';
import Button from '../components/common/Button.jsx';
import LoadingState from '../components/common/LoadingState.jsx';
import ErrorState from '../components/common/ErrorState.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import PageHeader from '../components/layout/PageHeader.jsx';

export default function QuizPage() {
  const { courseId, topicId } = useParams();
  const navigate = useNavigate();
  const { data: course } = useCourse(courseId);
  const { data: quiz, isLoading, isError, error, refetch } = useQuiz(topicId);
  const generate = useGenerateQuiz(topicId);

  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);

  const topic = course?.modules?.flatMap((m) => m.topics).find((t) => String(t.id) === String(topicId));
  const questions = quiz?.questions ?? [];
  const totalQ = questions.length;
  const current = questions[currentIdx];
  const selectedIndex = answers[currentIdx] ?? null;

  const handleSelect = useCallback((optIdx) => {
    if (!submitted) setAnswers((a) => ({ ...a, [currentIdx]: optIdx }));
  }, [currentIdx, submitted]);

  const handleSubmit = () => {
    if (Object.keys(answers).length === 0) return;
    setSubmitted(true);
  };

  const handleRetry = () => {
    setAnswers({});
    setSubmitted(false);
    setCurrentIdx(0);
  };

  const score = submitted
    ? questions.reduce((acc, q, i) => acc + (answers[i] === q.correctIndex ? 1 : 0), 0)
    : 0;

  const answeredCount = Object.keys(answers).length;

  if (isLoading) return <LoadingState message="Loading quiz…" size="lg" />;
  if (isError) return <ErrorState title="Couldn't load quiz" message={error?.message} onRetry={refetch} />;

  if (!quiz || totalQ === 0) {
    return (
      <div className={styles.page}>
        <PageHeader
          title={`Quiz: ${topic?.title ?? 'Topic'}`}
          breadcrumb={
            <>
              <Link to={ROUTES.COURSE_OVERVIEW(courseId)}>{course?.title ?? 'Course'}</Link>
              <span aria-hidden="true">›</span>
              <Link to={ROUTES.TOPIC_LEARNING(courseId, topicId)}>{topic?.title ?? 'Topic'}</Link>
              <span aria-hidden="true">›</span>
              <span aria-current="page">Quiz</span>
            </>
          }
        />
        <EmptyState
          icon="✅"
          title="Quiz not yet generated"
          description="Generate a quiz to test your understanding of this topic."
          actionLabel="Generate Quiz"
          onAction={() => generate.mutate()}
        />
        {generate.isPending && <LoadingState message="Generating quiz questions…" />}
        {generate.isError && <ErrorState title="Generation failed" message={generate.error?.message} onRetry={() => generate.mutate()} />}
      </div>
    );
  }

  // After regeneration, reset quiz-taking state so the professor
  // sees the new quiz from the beginning.
  const handleRegenerate = () => {
    generate.mutate(undefined, {
      onSuccess: () => {
        setAnswers({});
        setSubmitted(false);
        setCurrentIdx(0);
      },
    });
  };

  return (
    <div className={styles.page}>
      <PageHeader
        title={quiz.title ?? `Quiz: ${topic?.title ?? 'Topic'}`}
        breadcrumb={
          <>
            <Link to={ROUTES.COURSE_OVERVIEW(courseId)}>{course?.title ?? 'Course'}</Link>
            <span aria-hidden="true">›</span>
            <Link to={ROUTES.TOPIC_LEARNING(courseId, topicId)}>{topic?.title ?? 'Topic'}</Link>
            <span aria-hidden="true">›</span>
            <span aria-current="page">Quiz</span>
          </>
        }
        actions={
          <Button
            variant="secondary"
            size="sm"
            onClick={handleRegenerate}
            loading={generate.isPending}
            disabled={generate.isPending}
          >
            ↺ Regenerate Quiz
          </Button>
        }
      />
      {generate.isError && (
        <ErrorState
          title="Regeneration failed"
          message={generate.error?.message}
          onRetry={handleRegenerate}
        />
      )}

      {/* Score screen */}
      {submitted && (
        <div className={styles.scoreSection}>
          <ScoreCard
            score={score}
            total={totalQ}
            onRetry={handleRetry}
            onContinue={() => navigate(ROUTES.TOPIC_LEARNING(courseId, topicId))}
          />
          {/* Review all answers */}
          <div className={styles.reviewSection}>
            <h2 className={styles.reviewTitle}>Review your answers</h2>
            <div className={styles.reviewList}>
              {questions.map((q, i) => (
                <QuizCard
                  key={q.id}
                  question={q}
                  selectedIndex={answers[i] ?? null}
                  showFeedback={true}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Active quiz */}
      {!submitted && (
        <div className={styles.quizContainer}>
          {/* Progress bar */}
          <div className={styles.quizHeader}>
            <span className={styles.qCounter}>Question {currentIdx + 1} of {totalQ}</span>
            <div className={styles.qProgress} role="progressbar" aria-valuenow={currentIdx + 1} aria-valuemax={totalQ} aria-valuemin={1}>
              {questions.map((_, i) => (
                <div
                  key={i}
                  className={`${styles.qDot} ${i < currentIdx ? styles.qDotDone : ''} ${i === currentIdx ? styles.qDotActive : ''} ${answers[i] !== undefined ? styles.qDotAnswered : ''}`}
                  aria-hidden="true"
                />
              ))}
            </div>
            <span className={styles.qAnswered}>{answeredCount}/{totalQ} answered</span>
          </div>

          <div className={styles.questionWrap}>
            <QuizQuestion
              question={current}
              selectedIndex={selectedIndex}
              onSelect={handleSelect}
              disabled={submitted}
            />
          </div>

          <div className={styles.quizFooter}>
            <Button
              variant="secondary"
              onClick={() => setCurrentIdx((i) => Math.max(0, i - 1))}
              disabled={currentIdx === 0}
            >
              ← Previous
            </Button>
            <div className={styles.footerCenter}>
              {answeredCount === totalQ && !submitted && (
                <Button variant="primary" size="lg" onClick={handleSubmit}>
                  Submit Quiz
                </Button>
              )}
            </div>
            <Button
              variant="secondary"
              onClick={() => setCurrentIdx((i) => Math.min(totalQ - 1, i + 1))}
              disabled={currentIdx === totalQ - 1}
            >
              Next →
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
