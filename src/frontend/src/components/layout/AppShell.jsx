import React, { useState } from 'react';
import Navbar from './Navbar.jsx';
import Sidebar from './Sidebar.jsx';
import styles from './AppShell.module.css';

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

export default function AppShell({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className={styles.shell}>
      <Navbar onToggleSidebar={() => setSidebarOpen((v) => !v)} />
      <div className={styles.body}>
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <main className={styles.main} id="main-content">
          {USE_MOCKS && (
            <div className={styles.mockBanner} role="alert">
              ⚠️ Mock mode active — displaying demo data, not real AI output
            </div>
          )}
          <div className={styles.content}>
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
