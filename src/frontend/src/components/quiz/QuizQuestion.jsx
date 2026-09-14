import React from 'react';
import styles from './QuizQuestion.module.css';

export default function QuizQuestion({ question, selectedIndex, onSelect, disabled }) {
  if (!question) return null;
  return (
    <fieldset className={styles.fieldset} disabled={disabled}>
      <legend className={styles.question}>{question.text}</legend>
      <div className={styles.options}>
        {question.options.map((opt, i) => (
          <label
            key={opt.id}
            className={`${styles.option} ${selectedIndex === i ? styles.selected : ''}`}
          >
            <input
              type="radio"
              name={`q-${question.id}`}
              value={opt.id}
              checked={selectedIndex === i}
              onChange={() => onSelect(i)}
              className={styles.radio}
            />
            <span className={styles.optionMarker} aria-hidden="true">
              {String.fromCharCode(65 + i)}
            </span>
            <span className={styles.optionText}>{opt.text}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
