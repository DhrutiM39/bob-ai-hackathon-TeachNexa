import React, { useEffect, useRef } from 'react';
import styles from './Modal.module.css';
import Button from './Button.jsx';

export default function Modal({ isOpen, onClose, title, children, footer }) {
  const overlayRef = useRef(null);
  const firstFocusRef = useRef(null);

  useEffect(() => {
    if (!isOpen) return;
    const previouslyFocused = document.activeElement;
    firstFocusRef.current?.focus();
    const handleKey = (e) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleKey);
      document.body.style.overflow = '';
      previouslyFocused?.focus();
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className={styles.overlay}
      ref={overlayRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}
    >
      <div className={styles.modal}>
        <div className={styles.header}>
          <h2 id="modal-title" className={styles.title}>{title}</h2>
          <button
            className={styles.closeBtn}
            onClick={onClose}
            aria-label="Close dialog"
            ref={firstFocusRef}
          >
            ✕
          </button>
        </div>
        <div className={styles.body}>{children}</div>
        {footer && <div className={styles.footer}>{footer}</div>}
      </div>
    </div>
  );
}
