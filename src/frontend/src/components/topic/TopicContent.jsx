import React from 'react';
import styles from './TopicContent.module.css';
import ContentSection from './ContentSection.jsx';

export default function TopicContent({ content }) {
  if (!content) return null;
  return (
    <article className={styles.article}>
      {/* Objectives */}
      {content.objectives?.length > 0 && (
        <ContentSection title="Learning Objectives" icon="🎯">
          <ul className={styles.objectiveList}>
            {content.objectives.map((obj, i) => (
              <li key={i} className={styles.objectiveItem}>{obj}</li>
            ))}
          </ul>
        </ContentSection>
      )}

      {/* Explanation */}
      {content.explanation && (
        <ContentSection title="Explanation" icon="📖">
          <div className={styles.prose}>
            {content.explanation.split('\n\n').map((para, i) => (
              <p key={i} className={styles.para} dangerouslySetInnerHTML={{ __html: para.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>') }} />
            ))}
          </div>
        </ContentSection>
      )}

      {/* Key Concepts */}
      {content.keyConcepts?.length > 0 && (
        <ContentSection title="Key Concepts" icon="🔑">
          <dl className={styles.conceptList}>
            {content.keyConcepts.map((c, i) => (
              <div key={i} className={styles.concept}>
                <dt className={styles.conceptTerm}>{c.term}</dt>
                {c.definition && <dd className={styles.conceptDef}>{c.definition}</dd>}
              </div>
            ))}
          </dl>
        </ContentSection>
      )}

      {/* Examples */}
      {content.examples?.length > 0 && (
        <ContentSection title="Examples" icon="💡">
          <div className={styles.examples}>
            {content.examples.map((ex, i) => (
              <div key={i} className={styles.example}>
                {ex.title && <h4 className={styles.exampleTitle}>{ex.title}</h4>}
                <p className={styles.exampleContent}>{ex.content}</p>
              </div>
            ))}
          </div>
        </ContentSection>
      )}

      {/* Summary */}
      {content.summary && (
        <ContentSection title="Summary" icon="📝">
          <p className={styles.summary}>{content.summary}</p>
        </ContentSection>
      )}

      {/* Further Reading */}
      {content.furtherReading?.length > 0 && (
        <ContentSection title="Further Reading" icon="📚">
          <ul className={styles.readingList}>
            {content.furtherReading.map((r, i) => (
              <li key={i} className={styles.readingItem}>{r}</li>
            ))}
          </ul>
        </ContentSection>
      )}
    </article>
  );
}
