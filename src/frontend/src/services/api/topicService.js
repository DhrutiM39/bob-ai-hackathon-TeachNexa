import client from './client.js';

/**
 * POST /api/topics/:id/generate-content
 * Triggers AI generation and persists the content.
 */
export async function generateTopicContent(topicId) {
  const { data } = await client.post(`/api/topics/${topicId}/generate-content`);
  return data;
}

/**
 * GET /api/topics/:id/content
 * Fetch previously-generated content for a topic.
 */
export async function getTopicContent(topicId) {
  const { data } = await client.get(`/api/topics/${topicId}/content`);
  return data;
}
