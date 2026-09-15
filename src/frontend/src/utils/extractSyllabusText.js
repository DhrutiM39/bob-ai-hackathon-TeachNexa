/**
 * extractSyllabusText.js
 *
 * Extracts plain text from an uploaded syllabus File object.
 *
 * Supported natively (no extra library needed):
 *   .txt / text/plain — FileReader.readAsText()
 *
 * Not supported client-side without additional libraries:
 *   .pdf  — binary format; requires pdf.js or server-side parsing
 *   .doc  — legacy binary Office format; not parseable in browser
 *   .docx — ZIP/XML Office Open format; requires mammoth.js or similar
 *
 * For unsupported types, a descriptive error is thrown so the caller
 * can show a friendly message and ask the user to paste text instead.
 */

/** MIME types / extensions we can actually extract text from in-browser. */
const EXTRACTABLE_TYPES = new Set(['text/plain']);
const EXTRACTABLE_EXTENSIONS = /\.(txt)$/i;

/**
 * Returns true when the browser can extract plain text from this file
 * without any additional library.
 *
 * @param {File} file
 * @returns {boolean}
 */
export function isExtractable(file) {
  if (!file) return false;
  return EXTRACTABLE_TYPES.has(file.type) || EXTRACTABLE_EXTENSIONS.test(file.name);
}

/**
 * Reads a File and resolves with its text content.
 *
 * @param {File} file
 * @returns {Promise<string>}
 * @throws {Error} if the file type is not extractable or reading fails
 */
export function extractSyllabusText(file) {
  if (!file) {
    return Promise.reject(new Error('No file provided.'));
  }

  if (!isExtractable(file)) {
    const ext = file.name.split('.').pop()?.toLowerCase() ?? 'unknown';
    return Promise.reject(
      new Error(
        `"${file.name}" is a ${ext.toUpperCase()} file — automatic text extraction is not supported for this format. ` +
          'Please open the file, select all text (Ctrl+A / Cmd+A), and paste it into the text area above.'
      )
    );
  }

  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result;
      if (typeof text !== 'string' || text.trim().length === 0) {
        reject(new Error(`"${file.name}" appears to be empty. Please check the file and try again.`));
      } else {
        resolve(text);
      }
    };
    reader.onerror = () => {
      reject(new Error(`Could not read "${file.name}". The file may be corrupted or inaccessible.`));
    };
    reader.readAsText(file);
  });
}
