import React, { useEffect, useRef } from 'react';
import styles from './GenerationProgress.module.css';
import { GENERATION_STAGES } from '../../constants/index.js';

export default function GenerationProgress({ currentStage, completedStages = [], error }) {
  const liveRef = useRef(null);

  const currentLabel = GENERATION_STAGES.find((s) => s.id === currentStage)?.label;
  useEffect(() => {
    if (currentLabel && liveRef.current) {
      liveRef.current.textContent = `Now processing: ${currentLabel}`;
    }
  }, [currentLabel]);

  return (
    <div className={styles.wrapper} aria-label="Course generation progress">
      <div className={styles.header}>
        <h2 className={styles.title}>Generating your course…</h2>
        <p className={styles.subtitle}>IBM watsonx.ai is analyzing your syllabus and building a structured course.</p>
      </div>

      {/* Screen-reader live region */}
      <div ref={liveRef} aria-live="polite" aria-atomic="true" className="sr-only" />

      <ol className={styles.stages} aria-label="Generation stages">
        {GENERATION_STAGES.map((stage, index) => {
          const isCompleted = completedStages.includes(stage.id);
          const isActive    = currentStage === stage.id;
          const isPending   = !isCompleted && !isActive;

          return (
            <li key={stage.id} className={`${styles.stage} ${isCompleted ? styles.completed : ''} ${isActive ? styles.active : ''} ${isPending ? styles.pending : ''}`}>
              <div className={styles.stageLeft}>
                <div className={styles.stageIndicator} aria-hidden="true">
                  {isCompleted ? (
                    <span className={styles.checkIcon}>✓</span>
                  ) : isActive ? (
                    <span className={styles.spinner} />
                  ) : (
                    <span className={styles.stepNum}>{index + 1}</span>
                  )}
                </div>
                {index < GENERATION_STAGES.length - 1 && (
                  <div className={`${styles.connector} ${isCompleted ? styles.connectorDone : ''}`} aria-hidden="true" />
                )}
              </div>
              <div className={styles.stageContent}>
                <span className={styles.stageName}>{stage.label}</span>
                {(isActive || isCompleted) && (
                  <span className={styles.stageDesc}>{stage.description}</span>
                )}
              </div>
              <div className={styles.stageStatus} aria-label={isCompleted ? 'Complete' : isActive ? 'In progress' : 'Pending'}>
                {isCompleted && <span className={styles.doneTag}>Done</span>}
                {isActive    && <span className={styles.runningTag}>Running…</span>}
              </div>
            </li>
          );
        })}
      </ol>

      {error && (
        <div className={styles.error} role="alert">
          <span>⚠️</span>
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
