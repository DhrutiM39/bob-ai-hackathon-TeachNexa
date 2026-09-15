/**
 * Tests for extractSyllabusText.js
 *
 * Run with:  npx vitest run src/frontend/src/utils/extractSyllabusText.test.js
 * (requires: npm install -D vitest @vitest/coverage-v8 jsdom)
 *
 * Vitest uses the native jsdom environment so FileReader is available.
 * All test cases are pure-function / pure-Promise — no browser needed.
 */

import { describe, it, expect } from 'vitest';
import { isExtractable, extractSyllabusText } from './extractSyllabusText.js';

// ─── helpers ─────────────────────────────────────────────────────────────────

function makeFile(content, filename, type) {
  return new File([content], filename, { type });
}

// ─── isExtractable ────────────────────────────────────────────────────────────

describe('isExtractable', () => {
  it('returns true for text/plain MIME type', () => {
    expect(isExtractable(makeFile('hello', 'syllabus.txt', 'text/plain'))).toBe(true);
  });

  it('returns true for .txt extension regardless of MIME type', () => {
    // Some OS / browsers report text files with an empty or generic MIME type
    expect(isExtractable(makeFile('hello', 'syllabus.txt', ''))).toBe(true);
    expect(isExtractable(makeFile('hello', 'syllabus.TXT', ''))).toBe(true);
  });

  it('returns false for PDF', () => {
    expect(isExtractable(makeFile('%PDF-1.4', 'syllabus.pdf', 'application/pdf'))).toBe(false);
  });

  it('returns false for DOCX', () => {
    const type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
    expect(isExtractable(makeFile('PK...', 'syllabus.docx', type))).toBe(false);
  });

  it('returns false for legacy DOC', () => {
    expect(isExtractable(makeFile('\xD0\xCF', 'syllabus.doc', 'application/msword'))).toBe(false);
  });

  it('returns false for null', () => {
    expect(isExtractable(null)).toBe(false);
  });
});

// ─── extractSyllabusText ──────────────────────────────────────────────────────

describe('extractSyllabusText', () => {
  it('resolves with text content for a .txt file', async () => {
    const content = 'Week 1: Introduction\nWeek 2: Data types\nWeek 3: Functions';
    const file = makeFile(content, 'syllabus.txt', 'text/plain');
    const result = await extractSyllabusText(file);
    expect(result).toBe(content);
  });

  it('resolves with text content for text/plain MIME regardless of extension', async () => {
    const content = 'Module 1: Intro. Module 2: Core concepts.';
    const file = makeFile(content, 'notes', 'text/plain');
    const result = await extractSyllabusText(file);
    expect(result).toBe(content);
  });

  it('rejects with a friendly message for a PDF file', async () => {
    const file = makeFile('%PDF-1.4', 'syllabus.pdf', 'application/pdf');
    await expect(extractSyllabusText(file)).rejects.toThrow(
      'syllabus.pdf" is a PDF file'
    );
    await expect(extractSyllabusText(file)).rejects.toThrow(
      'paste it into the text area'
    );
  });

  it('rejects with a friendly message for a DOCX file', async () => {
    const type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
    const file = makeFile('PK...', 'syllabus.docx', type);
    await expect(extractSyllabusText(file)).rejects.toThrow('DOCX');
  });

  it('rejects with a friendly message for a DOC file', async () => {
    const file = makeFile('\xD0\xCF', 'syllabus.doc', 'application/msword');
    await expect(extractSyllabusText(file)).rejects.toThrow('DOC');
  });

  it('rejects when no file is provided', async () => {
    await expect(extractSyllabusText(null)).rejects.toThrow('No file provided');
  });

  it('rejects when file content is empty', async () => {
    const file = makeFile('   ', 'empty.txt', 'text/plain');
    await expect(extractSyllabusText(file)).rejects.toThrow('appears to be empty');
  });
});

// ─── integration: both text and file ─────────────────────────────────────────

describe('text-vs-file priority logic (mirroring CreateCourse.jsx)', () => {
  /**
   * This test mirrors the priority logic in CreateCourse.jsx:
   *   if (syllabusText.trim()) → use syllabusText
   *   else if (syllabusFile)   → extractSyllabusText(syllabusFile)
   *   else                     → validation error (never reaches here)
   */

  async function resolveText(syllabusText, syllabusFile) {
    let text = syllabusText.trim();
    if (!text && syllabusFile) {
      text = await extractSyllabusText(syllabusFile);
    }
    return text;
  }

  it('uses typed text when both text and file are provided', async () => {
    const file = makeFile('File content', 'syllabus.txt', 'text/plain');
    const result = await resolveText('Typed content', file);
    expect(result).toBe('Typed content');
  });

  it('falls back to file content when text is empty', async () => {
    const file = makeFile('File syllabus content', 'syllabus.txt', 'text/plain');
    const result = await resolveText('', file);
    expect(result).toBe('File syllabus content');
  });

  it('falls back to file content when text is only whitespace', async () => {
    const file = makeFile('From file', 'syllabus.txt', 'text/plain');
    const result = await resolveText('   ', file);
    expect(result).toBe('From file');
  });

  it('throws for unsupported file when text is empty', async () => {
    const file = makeFile('%PDF', 'syllabus.pdf', 'application/pdf');
    await expect(resolveText('', file)).rejects.toThrow('PDF');
  });
});
