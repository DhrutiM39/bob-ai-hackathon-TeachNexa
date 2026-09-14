import client from './client.js';

/**
 * POST /api/topics/:id/generate-content
 */
export async function generateTopicContent(topicId) {
  const { data } = await client.post(`/api/topics/${topicId}/generate-content`);
  return data;
}

/**
 * GET /api/topics/:id/content  (fetch already-generated content)
 */
export async function getTopicContent(topicId) {
  const { data } = await client.get(`/api/topics/${topicId}/content`);
  return data;
}
