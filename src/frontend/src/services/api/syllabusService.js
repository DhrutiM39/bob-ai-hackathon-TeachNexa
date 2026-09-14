import client from './client.js';

/**
 * POST /api/v1/syllabus
 * Validate and register a raw syllabus submission.
 * Returns { status, syllabus_id, course_name, syllabus_text, character_count, message }.
 */
export async function submitSyllabus({ course_name, syllabus_text }) {
  const { data } = await client.post('/api/v1/syllabus', { course_name, syllabus_text });
  return data;
}

/**
 * POST /api/v1/courses/generate
 * Matches GenerateCourseRequest: { title, syllabus_text, owner_id }
 * Returns a full course object that courseAdapter can normalise.
 */
export async function generateCourse({ title, syllabus_text, owner_id = null }) {
  const { data } = await client.post('/api/v1/courses/generate', {
    title,
    syllabus_text,
    owner_id,
  });
  return data;
}
