import React from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './Dashboard.module.css';
import { useCourses } from '../hooks/useCourses.js';
import { ROUTES } from '../constants/index.js';
import CourseCard from '../components/course/CourseCard.jsx';
import Button from '../components/common/Button.jsx';
import LoadingState from '../components/common/LoadingState.jsx';
import ErrorState from '../components/common/ErrorState.jsx';
import EmptyState from '../components/common/EmptyState.jsx';
import Skeleton from '../components/common/Skeleton.jsx';

function CourseCardSkeleton() {
  return (
    <div className={styles.skeletonCard}>
      <Skeleton height="20px" width="60px" />
      <Skeleton height="24px" className={styles.mt2} />
      <Skeleton variant="text" />
      <Skeleton variant="text" width="80%" />
      <Skeleton height="6px" className={styles.mt3} />
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const { data: courses, isLoading, isError, error, refetch } = useCourses();

  return (
    <div className={styles.page}>
      {/* Welcome Header */}
      <div className={styles.welcomeSection}>
        <div className={styles.welcomeText}>
          <h1 className={styles.welcomeTitle}>
            Welcome to <span className={styles.accent}>CourseGenie AI</span>
          </h1>
          <p className={styles.welcomeSubtitle}>
            Transform your college syllabus into a complete, structured course — powered by AI.
          </p>
        </div>
        <Button
          variant="primary"
          size="lg"
          onClick={() => navigate(ROUTES.CREATE_COURSE)}
          aria-label="Create a new AI-generated course"
        >
          + Create New Course
        </Button>
      </div>

      {/* Feature pills */}
      <div className={styles.featurePills} aria-label="What CourseGenie AI does">
        {[
          { icon: '📄', label: 'Syllabus Analysis', onClick: () => navigate(ROUTES.CREATE_COURSE) },
          { icon: '🧩', label: 'Module Generation', onClick: () => navigate(ROUTES.CREATE_COURSE) },
          { icon: '📖', label: 'Learning Content', onClick: () => navigate(ROUTES.CREATE_COURSE) },
          {
            icon: '✅', label: 'Quizzes',
            onClick: () => courses?.length > 0
              ? navigate(ROUTES.COURSE_OVERVIEW(courses[0].id))
              : navigate(ROUTES.CREATE_COURSE),
          },
          {
            icon: '🔁', label: 'Revision Center',
            onClick: () => courses?.length > 0
              ? navigate(ROUTES.REVISION(courses[0].id))
              : navigate(ROUTES.CREATE_COURSE),
          },
        ].map(({ icon, label, onClick }) => (
          <div key={label} className={styles.pill} onClick={onClick} style={{ cursor: 'pointer' }}>
            <span aria-hidden="true">{icon}</span>
            <span>{label}</span>
          </div>
        ))}
      </div>

      {/* Courses Section */}
      <section aria-labelledby="courses-heading">
        <div className={styles.sectionHeader}>
          <h2 id="courses-heading" className={styles.sectionTitle}>Your Courses</h2>
          {!isLoading && courses?.length > 0 && (
            <Button variant="ghost" size="sm" onClick={() => navigate(ROUTES.CREATE_COURSE)}>
              + New Course
            </Button>
          )}
        </div>

        {isLoading && (
          <div className={styles.grid}>
            {[1, 2, 3].map((i) => <CourseCardSkeleton key={i} />)}
          </div>
        )}

        {isError && (
          <ErrorState
            title="Couldn't load courses"
            message={error?.message}
            onRetry={refetch}
          />
        )}

        {!isLoading && !isError && courses?.length === 0 && (
          <EmptyState
            icon="🎓"
            title="No courses yet"
            description="Create your first AI-generated course by uploading or pasting your syllabus."
            actionLabel="Create Your First Course"
            onAction={() => navigate(ROUTES.CREATE_COURSE)}
          />
        )}

        {!isLoading && !isError && courses?.length > 0 && (
          <div className={styles.grid}>
            {courses.map((course) => (
              <CourseCard key={course.id} course={course} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
