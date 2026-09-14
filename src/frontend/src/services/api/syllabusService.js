import client from './client.js';

/**
 * POST /api/syllabus/analyze
 * Accepts either a text body or a form-data file upload.
 */
export async function analyzeSyllabus({ text, file }) {
  if (file) {
    const form = new FormData();
    form.append('file', file);
    const { data } = await client.post('/api/syllabus/analyze', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  }
  const { data } = await client.post('/api/syllabus/analyze', { text });
  return data;
}

/**
 * POST /api/course/generate
 */
export async function generateCourse(payload) {
  const { data } = await client.post('/api/course/generate', payload);
  return data;
}
