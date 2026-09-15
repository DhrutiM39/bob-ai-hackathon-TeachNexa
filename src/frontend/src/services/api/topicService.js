import client from './client.js';

// Per-request timeout for AI generation calls (overrides the shared 60 s default).
const AI_TIMEOUT = 180000; // 3 min

/**
 * POST /api/topics/:id/generate-content
 * Triggers AI generation and persists the content.
 * Uses a 3-minute timeout — DeepSeek generation can exceed 60 s.
 */
export async function generateTopicContent(topicId) {
  const { data } = await client.post(
    `/api/topics/${topicId}/generate-content`,
    undefined,
    { timeout: AI_TIMEOUT },
  );
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
