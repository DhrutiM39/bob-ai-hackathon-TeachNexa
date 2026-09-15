import React from 'react';
import styles from './StepIndicator.module.css';

/**
 * Three-step progress indicator used across the course-creation workflow.
 *
 * Props:
 *   currentStep  — 1 | 2 | 3  (active step, 1-based)
 *
 * Steps are always:
 *   1. Syllabus Analysis
 *   2. Module Review
 *   3. Learning Content
 */
const STEPS = [
  { id: 1, label: 'Syllabus Analysis', icon: '📄' },
  { id: 2, label: 'Module Review',     icon: '🧩' },
  { id: 3, label: 'Learning Content',  icon: '📖' },
];

export default function StepIndicator({ currentStep = 1 }) {
  return (
    <div className={styles.wrapper} aria-label="Course creation progress">
      {STEPS.map((step, idx) => {
        const done    = step.id < currentStep;
        const active  = step.id === currentStep;
        const future  = step.id > currentStep;

        return (
          <React.Fragment key={step.id}>
            <div
              className={`${styles.step} ${done ? styles.done : ''} ${active ? styles.active : ''} ${future ? styles.future : ''}`}
              aria-current={active ? 'step' : undefined}
            >
              <div className={styles.circle}>
                {done ? (
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                    <path d="M2.5 7 L5.5 10 L11.5 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                ) : (
                  <span aria-hidden="true">{step.icon}</span>
                )}
              </div>
              <div className={styles.label}>
                <span className={styles.stepNum}>Step {step.id}</span>
                <span className={styles.stepName}>{step.label}</span>
              </div>
            </div>
            {idx < STEPS.length - 1 && (
              <div className={`${styles.connector} ${step.id < currentStep ? styles.connectorDone : ''}`} aria-hidden="true" />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}
