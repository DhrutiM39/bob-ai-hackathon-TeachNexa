import client from './client.js';

/**
 * POST /api/topics/:id/generate-quiz
 */
export async function generateQuiz(topicId) {
  const { data } = await client.post(`/api/topics/${topicId}/generate-quiz`);
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
 * POST /api/topics/:id/generate-revision
 */
export async function generateRevision(topicId) {
  const { data } = await client.post(`/api/topics/${topicId}/generate-revision`);
  return data;
}

/**
 * GET /api/courses/:courseId/revision
 */
export async function getRevision(courseId) {
  const { data } = await client.get(`/api/courses/${courseId}/revision`);
  return data;
}
