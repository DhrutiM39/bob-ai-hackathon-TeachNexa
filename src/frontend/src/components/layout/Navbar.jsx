import React, { useState } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import styles from './Navbar.module.css';
import { ROUTES } from '../../constants/index.js';
import { useAuthStore } from '../../store/useAuthStore.js';

export default function Navbar({ onToggleSidebar }) {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <header className={styles.navbar} role="banner">
      <div className={styles.left}>
        <button
          className={styles.menuBtn}
          onClick={onToggleSidebar}
          aria-label="Toggle navigation"
        >
          <span className={styles.menuIcon} aria-hidden="true">
            <span /><span /><span />
          </span>
        </button>
        <Link to={ROUTES.DASHBOARD} className={styles.brand} aria-label="CourseGenie AI — go to dashboard">
          <span className={styles.brandIcon} aria-hidden="true">🎓</span>
          <span className={styles.brandName}>CourseGenie AI</span>
        </Link>
      </div>
      <nav className={styles.center} aria-label="Main navigation">
        <NavLink to={ROUTES.DASHBOARD} className={({ isActive }) => `${styles.navLink} ${isActive ? styles.active : ''}`} end>
          Dashboard
        </NavLink>
        <NavLink to={ROUTES.CREATE_COURSE} className={({ isActive }) => `${styles.navLink} ${isActive ? styles.active : ''}`}>
          New Course
        </NavLink>
      </nav>
      <div className={styles.right}>
        {user && (
          <span className={styles.userName} title={user.email}>{user.name}</span>
        )}
        <button
          className={styles.createBtn}
          onClick={() => navigate(ROUTES.CREATE_COURSE)}
          aria-label="Create new course"
        >
          + Create
        </button>
        <button
          className={styles.logoutBtn}
          onClick={handleLogout}
          aria-label="Sign out"
        >
          Sign out
        </button>
      </div>
    </header>
  );
}
