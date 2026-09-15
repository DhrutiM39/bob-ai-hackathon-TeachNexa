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
 *
 * Uses a 3-minute per-request timeout (overrides the shared 60 s default)
 * because DeepSeek syllabus analysis can take longer than 60 seconds on
 * large syllabi.
 */
export async function generateCourse({ title, syllabus_text }) {
  const { data } = await client.post(
    '/api/v1/courses/generate',
    { title, syllabus_text },
    { timeout: 180000 }, // 3 min — AI generation can exceed 60 s
  );
  return data;
}
