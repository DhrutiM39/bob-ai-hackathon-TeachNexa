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
 * POST /api/v1/courses/generate
 * Sends { title, syllabus_text } and returns the full course hierarchy.
 * owner_id is assigned server-side — clients must not send it.
 */
export async function generateCourse({ title, syllabus_text }) {
  const { data } = await client.post('/api/v1/courses/generate', {
    title,
    syllabus_text,
  });
  return data;
}
