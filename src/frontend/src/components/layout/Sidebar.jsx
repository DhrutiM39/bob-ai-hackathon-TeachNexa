import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import styles from './Sidebar.module.css';
import { ROUTES } from '../../constants/index.js';
import { useCourses } from '../../hooks/useCourses.js';
import { computeProgress } from '../../utils/index.js';

export default function Sidebar({ isOpen, onClose }) {
  const { data: courses } = useCourses();

  return (
    <>
      {isOpen && <div className={styles.backdrop} onClick={onClose} aria-hidden="true" />}
      <aside className={`${styles.sidebar} ${isOpen ? styles.open : ''}`} aria-label="Sidebar navigation">
        <nav>
          <section className={styles.section}>
            <p className={styles.sectionLabel}>Navigation</p>
            <SidebarLink to={ROUTES.DASHBOARD} icon="⊞" label="Dashboard" onClick={onClose} end />
            <SidebarLink to={ROUTES.CREATE_COURSE} icon="+" label="Create Course" onClick={onClose} />
          </section>

          {courses && courses.length > 0 && (
            <section className={styles.section}>
              <p className={styles.sectionLabel}>My Courses</p>
              {courses.map((course) => (
                <SidebarCourse key={course.id} course={course} onClick={onClose} />
              ))}
            </section>
          )}
        </nav>
      </aside>
    </>
  );
}

function SidebarLink({ to, icon, label, onClick, end }) {
  return (
    <NavLink
      to={to}
      end={end}
      onClick={onClick}
      className={({ isActive }) => `${styles.link} ${isActive ? styles.linkActive : ''}`}
    >
      <span className={styles.linkIcon} aria-hidden="true">{icon}</span>
      <span>{label}</span>
    </NavLink>
  );
}

function SidebarCourse({ course, onClick }) {
  const progress = computeProgress(course.completedTopics, course.totalTopics);
  return (
    <Link
      to={ROUTES.COURSE_OVERVIEW(course.id)}
      className={styles.courseLink}
      onClick={onClick}
    >
      <div className={styles.courseInfo}>
        <span className={styles.courseName} title={course.title}>{course.title}</span>
        {course.code && <span className={styles.courseCode}>{course.code}</span>}
      </div>
      <div className={styles.progressBar} role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
        <div className={styles.progressFill} style={{ width: `${progress}%` }} />
      </div>
    </Link>
  );
}
