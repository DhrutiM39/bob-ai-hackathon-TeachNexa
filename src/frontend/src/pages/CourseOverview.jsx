import React, { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import styles from './CourseOverview.module.css';
import { useCourse, useUpdateCourse } from '../hooks/useCourses.js';
import { ROUTES } from '../constants/index.js';
import { computeProgress, pluralize } from '../utils/index.js';
import ModuleCard from '../components/course/ModuleCard.jsx';
import CourseProgress from '../components/course/CourseProgress.jsx';
import Button from '../components/common/Button.jsx';
import Modal from '../components/common/Modal.jsx';
import LoadingState from '../components/common/LoadingState.jsx';
import ErrorState from '../components/common/ErrorState.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import Skeleton from '../components/common/Skeleton.jsx';
import PageHeader from '../components/layout/PageHeader.jsx';

function CourseSkeleton() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      <Skeleton height="60px" />
      {[1, 2, 3].map((i) => <Skeleton key={i} height="80px" />)}
    </div>
  );
}

export default function CourseOverview() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const { data: course, isLoading, isError, error, refetch } = useCourse(courseId);
  const updateCourse = useUpdateCourse(courseId);

  const [editOpen, setEditOpen] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [editError, setEditError] = useState('');

  const openEdit = () => {
    setEditTitle(course.title ?? '');
    setEditDesc(course.description ?? '');
    setEditError('');
    setEditOpen(true);
  };

  const handleSave = () => {
    const trimmed = editTitle.trim();
    if (!trimmed) { setEditError('Title is required.'); return; }
    updateCourse.mutate(
      { title: trimmed, description: editDesc.trim() || null },
      {
        onSuccess: () => setEditOpen(false),
        onError: (err) => setEditError(err.message || 'Save failed.'),
      },
    );
  };

  if (isLoading) return <CourseSkeleton />;
  if (isError) return <ErrorState title="Couldn't load course" message={error?.message} onRetry={refetch} />;
  if (!course) return <EmptyState icon="📚" title="Course not found" description="This course doesn't exist or was removed." actionLabel="Go to Dashboard" onAction={() => navigate(ROUTES.DASHBOARD)} />;

  const progress = computeProgress(course.completedTopics, course.totalTopics);

  return (
    <div className={styles.page}>
      <PageHeader
        title={course.title}
        subtitle={course.description}
        breadcrumb={
          <>
            <Link to={ROUTES.DASHBOARD}>Dashboard</Link>
            <span aria-hidden="true">›</span>
            <span aria-current="page">{course.title}</span>
          </>
        }
        actions={
          <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
            <Button variant="ghost" size="sm" onClick={openEdit} aria-label="Edit course">
              ✎ Edit
            </Button>
            <Button variant="secondary" size="sm" onClick={() => navigate(ROUTES.REVISION(courseId))}>
              Revision Center
            </Button>
          </div>
        }
      />

      {/* Course stats bar */}
      <div className={styles.statsBar}>
        <div className={styles.stat}>
          <span className={styles.statValue}>{course.modules?.length ?? 0}</span>
          <span className={styles.statLabel}>Modules</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statValue}>{course.totalTopics}</span>
          <span className={styles.statLabel}>Topics</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statValue}>{course.completedTopics}</span>
          <span className={styles.statLabel}>Completed</span>
        </div>
        <div className={`${styles.stat} ${styles.statProgress}`}>
          <span className={styles.statValue}>{progress}%</span>
          <span className={styles.statLabel}>Progress</span>
        </div>
        <div className={styles.progressWide}>
          <CourseProgress value={progress} size="md" />
        </div>
      </div>

      {/* Modules list */}
      <section aria-label="Course modules">
        {course.modules?.length === 0 ? (
          <EmptyState icon="🧩" title="No modules yet" description="Modules will appear once course generation is complete." />
        ) : (
          course.modules?.map((module) => (
            <ModuleCard key={module.id} module={module} courseId={courseId} />
          ))
        )}
      </section>

      {/* Edit course modal */}
      <Modal
        isOpen={editOpen}
        onClose={() => setEditOpen(false)}
        title="Edit Course"
        footer={
          <>
            <Button variant="secondary" onClick={() => setEditOpen(false)} disabled={updateCourse.isPending}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleSave} loading={updateCourse.isPending}>
              Save
            </Button>
          </>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {editError && (
            <p role="alert" style={{ color: 'var(--color-error)', fontSize: 'var(--text-sm)' }}>{editError}</p>
          )}
          <label style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)', fontSize: 'var(--text-sm)', fontWeight: 'var(--font-medium)' }}>
            Title <span style={{ color: 'var(--color-error)' }} aria-hidden="true">*</span>
            <input
              type="text"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              maxLength={500}
              style={inputStyle}
              aria-required="true"
            />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)', fontSize: 'var(--text-sm)', fontWeight: 'var(--font-medium)' }}>
            Description <span style={{ color: 'var(--color-text-muted)', fontWeight: 'var(--font-normal)' }}>(optional)</span>
            <textarea
              value={editDesc}
              onChange={(e) => setEditDesc(e.target.value)}
              maxLength={2000}
              rows={3}
              style={{ ...inputStyle, resize: 'vertical' }}
            />
          </label>
        </div>
      </Modal>
    </div>
  );
}

const inputStyle = {
  width: '100%',
  padding: 'var(--space-2) var(--space-3)',
  border: '1px solid var(--color-border-strong)',
  borderRadius: 'var(--radius-md)',
  fontSize: 'var(--text-base)',
  fontFamily: 'inherit',
  background: 'var(--color-surface)',
  color: 'var(--color-text-primary)',
};
