import React, { useState } from 'react';
import styles from './QuestionBankList.module.css';
import QuizCard from '../quiz/QuizCard.jsx';

export default function QuestionBankList({ questions }) {
  const [revealed, setRevealed] = useState({});

  if (!questions?.length) {
    return <p className={styles.empty}>No questions in the bank yet.</p>;
  }

  return (
    <div className={styles.list}>
      {questions.map((q, i) => (
        <div key={q.id ?? i} className={styles.item}>
          <div className={styles.itemHeader}>
            <span className={styles.qNum}>Q{i + 1}</span>
            <button
              className={styles.revealBtn}
              onClick={() => setRevealed((r) => ({ ...r, [q.id ?? i]: !r[q.id ?? i] }))}
            >
              {revealed[q.id ?? i] ? 'Hide answer' : 'Show answer'}
            </button>
          </div>
          <QuizCard
            question={q}
            selectedIndex={revealed[q.id ?? i] ? q.correctIndex : null}
            showFeedback={revealed[q.id ?? i]}
          />
        </div>
      ))}
    </div>
  );
}
