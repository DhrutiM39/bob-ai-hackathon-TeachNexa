import client from './client.js';

// Per-request timeout for AI generation calls (overrides the shared 60 s default).
const AI_TIMEOUT = 180000; // 3 min

/**
 * POST /api/topics/:id/generate-quiz
 * Uses a 3-minute timeout — DeepSeek generation can exceed 60 s.
 */
export async function generateQuiz(topicId) {
  const { data } = await client.post(
    `/api/topics/${topicId}/generate-quiz`,
    undefined,
    { timeout: AI_TIMEOUT },
  );
  return data;
}

/**
 * GET /api/topics/:id/quiz
 */
export async function getQuiz(topicId) {
  const { data } = await client.get(`/api/topics/${topicId}/quiz`);
  return data;
}

/**
 * POST /api/courses/:courseId/generate-revision
 * Revision is generated at the course level, not per-topic.
 * Uses a 3-minute timeout — DeepSeek generation can exceed 60 s.
 */
export async function generateRevision(courseId) {
  const { data } = await client.post(
    `/api/courses/${courseId}/generate-revision`,
    undefined,
    { timeout: AI_TIMEOUT },
  );
  return data;
}

/**
 * GET /api/courses/:courseId/revision
 */
export async function getRevision(courseId) {
  const { data } = await client.get(`/api/courses/${courseId}/revision`);
  return data;
}
