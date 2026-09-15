import React, { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import styles from './CourseModules.module.css';
import { useCourse, useUpdateCourse } from '../hooks/useCourses.js';
import { ROUTES } from '../constants/index.js';
import ModuleCard from '../components/course/ModuleCard.jsx';
import StepIndicator from '../components/common/StepIndicator.jsx';
import Button from '../components/common/Button.jsx';
import Modal from '../components/common/Modal.jsx';
import LoadingState from '../components/common/LoadingState.jsx';
import ErrorState from '../components/common/ErrorState.jsx';
import Skeleton from '../components/common/Skeleton.jsx';
import PageHeader from '../components/layout/PageHeader.jsx';

function ModulesSkeleton() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      {[1, 2, 3].map((i) => <Skeleton key={i} height="80px" />)}
    </div>
  );
}

export default function CourseModules() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const { data: course, isLoading, isError, error, refetch } = useCourse(courseId);
  const updateCourse = useUpdateCourse(courseId);

  const [editOpen, setEditOpen]   = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editDesc, setEditDesc]   = useState('');
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

  if (isLoading) return (
    <div className={styles.page}>
      <StepIndicator currentStep={2} />
      <ModulesSkeleton />
    </div>
  );

  if (isError) return (
    <div className={styles.page}>
      <StepIndicator currentStep={2} />
      <ErrorState title="Couldn't load course" message={error?.message} onRetry={refetch} />
    </div>
  );

  const totalModules = course?.modules?.length ?? 0;
  const totalTopics  = course?.modules?.reduce((n, m) => n + (m.topics?.length ?? 0), 0) ?? 0;

  return (
    <div className={styles.page}>
      {/* ── Workflow progress ── */}
      <StepIndicator currentStep={2} />

      <PageHeader
        title={course?.title ?? 'Module Review'}
        subtitle="Step 2 of 3 — Review and edit the AI-generated modules and topics before continuing to learning content."
        breadcrumb={
          <>
            <Link to={ROUTES.DASHBOARD}>Dashboard</Link>
            <span aria-hidden="true">›</span>
            <Link to={ROUTES.CREATE_COURSE}>Create Course</Link>
            <span aria-hidden="true">›</span>
            <span aria-current="page">Module Review</span>
          </>
        }
        actions={
          <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
            <Button variant="ghost" size="sm" onClick={openEdit} aria-label="Edit course title">
              ✎ Edit Course
            </Button>
          </div>
        }
      />

      {/* ── Stats strip ── */}
      <div className={styles.statsStrip}>
        <div className={styles.stat}>
          <span className={styles.statVal}>{totalModules}</span>
          <span className={styles.statLabel}>Modules</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statVal}>{totalTopics}</span>
          <span className={styles.statLabel}>Topics</span>
        </div>
        <div className={styles.statHint}>
          <span>✎ Click the pencil icon on any module or topic to edit its title and description.</span>
        </div>
      </div>

      {/* ── Module list (reuses existing ModuleCard with inline edit) ── */}
      <section aria-label="Generated modules">
        {totalModules === 0 ? (
          <div className={styles.empty}>
            <p>No modules were generated. Try going back and providing more detailed syllabus content.</p>
            <Button variant="secondary" onClick={() => navigate(ROUTES.CREATE_COURSE)} style={{ marginTop: 'var(--space-4)' }}>
              ← Back to Syllabus
            </Button>
          </div>
        ) : (
          course.modules.map((module) => (
            <ModuleCard key={module.id} module={module} courseId={courseId} />
          ))
        )}
      </section>

      {/* ── CTA: continue to Step 3 ── */}
      {totalModules > 0 && (
        <div className={styles.ctaRow}>
          <Button variant="secondary" size="md" onClick={() => navigate(ROUTES.CREATE_COURSE)}>
            ← Back to Syllabus
          </Button>
          <div className={styles.ctaRight}>
            <p className={styles.ctaHint}>
              Happy with the structure? Continue to generate learning content.
            </p>
            <Button
              variant="primary"
              size="lg"
              onClick={() => navigate(ROUTES.COURSE_OVERVIEW(courseId) + '?from=modules')}
            >
              Continue to Learning Content →
            </Button>
          </div>
        </div>
      )}

      {/* ── Edit course modal ── */}
      <Modal
        isOpen={editOpen}
        onClose={() => setEditOpen(false)}
        title="Edit Course"
        footer={
          <>
            <Button variant="secondary" onClick={() => setEditOpen(false)} disabled={updateCourse.isPending}>Cancel</Button>
            <Button variant="primary" onClick={handleSave} loading={updateCourse.isPending}>Save</Button>
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
