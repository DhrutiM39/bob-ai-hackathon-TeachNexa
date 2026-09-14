import React from 'react';
import styles from './QuizCard.module.css';

/**
 * QuizCard — shows result feedback for a single question after submission.
 */
export default function QuizCard({ question, selectedIndex, showFeedback = false }) {
  if (!question) return null;
  const isCorrect = showFeedback && selectedIndex === question.correctIndex;
  const isWrong   = showFeedback && selectedIndex !== null && selectedIndex !== question.correctIndex;

  return (
    <div className={`${styles.card} ${showFeedback ? (isCorrect ? styles.correct : styles.incorrect) : ''}`}>
      <p className={styles.questionText}>{question.text}</p>
      <ol className={styles.options} type="A">
        {question.options.map((opt, i) => {
          const isSelected = selectedIndex === i;
          const isCorrectOpt = question.correctIndex === i;
          let optClass = styles.opt;
          if (showFeedback && isCorrectOpt) optClass += ` ${styles.optCorrect}`;
          if (showFeedback && isSelected && !isCorrectOpt) optClass += ` ${styles.optWrong}`;
          if (!showFeedback && isSelected) optClass += ` ${styles.optSelected}`;
          return (
            <li key={opt.id} className={optClass}>
              {opt.text}
            </li>
          );
        })}
      </ol>
      {showFeedback && question.explanation && (
        <div className={`${styles.explanation} ${isCorrect ? styles.expCorrect : styles.expWrong}`}>
          <span className={styles.expLabel} aria-hidden="true">{isCorrect ? '✓' : '✕'}</span>
          <span>{question.explanation}</span>
        </div>
      )}
    </div>
  );
}
