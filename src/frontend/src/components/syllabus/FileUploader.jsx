import React, { useRef, useState } from 'react';
import styles from './FileUploader.module.css';
import { ACCEPTED_FILE_TYPES, MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB } from '../../constants/index.js';
import { formatFileSize } from '../../utils/index.js';

export default function FileUploader({ file, onChange, disabled }) {
  const inputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState('');

  const validate = (f) => {
    if (!ACCEPTED_FILE_TYPES.includes(f.type) && !f.name.match(/\.(pdf|txt|doc|docx)$/i)) {
      return 'Unsupported file type. Please upload a PDF, TXT, DOC, or DOCX file.';
    }
    if (f.size > MAX_FILE_SIZE_BYTES) {
      return `File is too large. Maximum size is ${MAX_FILE_SIZE_MB} MB.`;
    }
    return '';
  };

  const handleFile = (f) => {
    if (!f) return;
    const err = validate(f);
    setError(err);
    if (!err) onChange(f);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (disabled) return;
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const handleChange = (e) => {
    const f = e.target.files[0];
    if (f) handleFile(f);
    e.target.value = '';
  };

  const removeFile = () => {
    onChange(null);
    setError('');
  };

  return (
    <div className={styles.wrapper}>
      {file ? (
        <div className={styles.filePreview}>
          <span className={styles.fileIcon} aria-hidden="true">📄</span>
          <div className={styles.fileInfo}>
            <span className={styles.fileName}>{file.name}</span>
            <span className={styles.fileSize}>{formatFileSize(file.size)}</span>
          </div>
          <button
            type="button"
            className={styles.removeBtn}
            onClick={removeFile}
            aria-label={`Remove file ${file.name}`}
            disabled={disabled}
          >
            ✕
          </button>
        </div>
      ) : (
        <div
          className={`${styles.dropzone} ${dragOver ? styles.dragOver : ''} ${disabled ? styles.disabled : ''}`}
          onDragOver={(e) => { e.preventDefault(); if (!disabled) setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => !disabled && inputRef.current?.click()}
          role="button"
          tabIndex={disabled ? -1 : 0}
          aria-label="Upload syllabus file. Drag and drop or click to browse."
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); inputRef.current?.click(); } }}
        >
          <span className={styles.uploadIcon} aria-hidden="true">↑</span>
          <p className={styles.primary}>Drag & drop your syllabus file</p>
          <p className={styles.secondary}>or <span className={styles.browse}>browse to upload</span></p>
          <p className={styles.hint}>TXT auto-extracted · PDF/DOC/DOCX: paste text instead · max {MAX_FILE_SIZE_MB} MB</p>
        </div>
      )}
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.txt,.doc,.docx"
        onChange={handleChange}
        className={styles.hiddenInput}
        aria-hidden="true"
        tabIndex={-1}
        disabled={disabled}
      />
      {error && <p className={styles.error} role="alert">{error}</p>}
    </div>
  );
}
