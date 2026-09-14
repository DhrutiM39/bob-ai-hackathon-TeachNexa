import React from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import styles from './TopicLearning.module.css';
import { useTopicContent, useGenerateTopicContent } from '../hooks/useTopicContent.js';
import { useCourse } from '../hooks/useCourses.js';
import { ROUTES } from '../constants/index.js';
import TopicContent from '../components/topic/TopicContent.jsx';
import Button from '../components/common/Button.jsx';
import LoadingState from '../components/common/LoadingState.jsx';
import ErrorState from '../components/common/ErrorState.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import PageHeader from '../components/layout/PageHeader.jsx';
import { SkeletonText } from '../components/common/Skeleton.jsx';

export default function TopicLearning() {
  const { courseId, topicId } = useParams();
  const navigate = useNavigate();
  const { data: course } = useCourse(courseId);
  const { data: content, isLoading, isError, error, refetch } = useTopicContent(topicId);
  const generate = useGenerateTopicContent(topicId);

  // Find the topic in the course to get its title
  const topic = course?.modules?.flatMap((m) => m.topics).find((t) => t.id === topicId);

  const handleGenerate = () => generate.mutate();

  const sidebar = (
    <aside className={styles.sidebar} aria-label="Topic information">
      {course && (
        <div className={styles.sidebarCard}>
          <p className={styles.sidebarLabel}>Course</p>
          <Link to={ROUTES.COURSE_OVERVIEW(courseId)} className={styles.sidebarCourse}>
            {course.title}
          </Link>
        </div>
      )}
      {content?.objectives?.length > 0 && (
        <div className={styles.sidebarCard}>
          <p className={styles.sidebarLabel}>Learning Objectives</p>
          <ul className={styles.sidebarList}>
            {content.objectives.map((obj, i) => <li key={i}>{obj}</li>)}
          </ul>
        </div>
      )}
      <div className={styles.sidebarActions}>
        <Button
          variant="primary"
          size="md"
          onClick={() => navigate(ROUTES.QUIZ(courseId, topicId))}
          style={{ width: '100%' }}
        >
          Take Quiz →
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={handleGenerate}
          loading={generate.isPending}
          style={{ width: '100%' }}
        >
          Regenerate Content
        </Button>
      </div>
    </aside>
  );

  return (
    <div className={styles.page}>
      <PageHeader
        title={topic?.title ?? content?.title ?? 'Topic'}
        breadcrumb={
          <>
            <Link to={ROUTES.DASHBOARD}>Dashboard</Link>
            <span aria-hidden="true">›</span>
            <Link to={ROUTES.COURSE_OVERVIEW(courseId)}>{course?.title ?? 'Course'}</Link>
            <span aria-hidden="true">›</span>
            <span aria-current="page">{topic?.title ?? 'Topic'}</span>
          </>
        }
      />

      <div className={styles.layout}>
        <div className={styles.main}>
          {isLoading && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
              <SkeletonText lines={2} />
              <SkeletonText lines={5} />
              <SkeletonText lines={4} />
            </div>
          )}

          {isError && (
            <ErrorState title="Couldn't load topic content" message={error?.message} onRetry={refetch} />
          )}

          {generate.isError && (
            <ErrorState title="Generation failed" message={generate.error?.message} onRetry={handleGenerate} />
          )}

          {!isLoading && !isError && !content && (
            <EmptyState
              icon="📖"
              title="Content not yet generated"
              description="Click 'Generate Content' to let IBM watsonx.ai create learning material for this topic."
              actionLabel="Generate Content"
              onAction={handleGenerate}
            />
          )}

          {!isLoading && content && (
            <TopicContent content={content} />
          )}
        </div>
        {sidebar}
      </div>
    </div>
  );
}
