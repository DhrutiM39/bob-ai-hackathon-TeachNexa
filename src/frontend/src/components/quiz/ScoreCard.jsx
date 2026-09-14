import React from 'react';
import styles from './ScoreCard.module.css';
import Button from '../common/Button.jsx';

export default function ScoreCard({ score, total, onRetry, onContinue }) {
  const pct = Math.round((score / total) * 100);
  const passed = pct >= 70;

  return (
    <div className={`${styles.card} ${passed ? styles.passed : styles.failed}`} role="region" aria-label="Quiz results">
      <div className={styles.icon} aria-hidden="true">{passed ? '🏆' : '📝'}</div>
      <h2 className={styles.headline}>{passed ? 'Well done!' : 'Keep practicing'}</h2>
      <div className={styles.scoreDisplay} aria-label={`Score: ${score} out of ${total}`}>
        <span className={styles.scoreNum}>{score}</span>
        <span className={styles.scoreSep}>/</span>
        <span className={styles.scoreTotal}>{total}</span>
      </div>
      <p className={styles.pct}>{pct}% correct</p>
      <p className={styles.message}>
        {passed
          ? `You answered ${score} out of ${total} questions correctly. You passed this quiz!`
          : `You answered ${score} out of ${total} questions correctly. Review the explanations and try again.`}
      </p>
      <div className={styles.actions}>
        <Button variant="secondary" onClick={onRetry}>Retry Quiz</Button>
        {onContinue && <Button variant="primary" onClick={onContinue}>Continue Learning</Button>}
      </div>
    </div>
  );
}
