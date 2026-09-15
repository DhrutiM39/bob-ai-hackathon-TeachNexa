import client from './client.js';

/**
 * GET /api/courses
 */
export async function getCourses() {
  const { data } = await client.get('/api/courses');
  return data;
}

/**
 * GET /api/courses/:id
 */
export async function getCourse(id) {
  const { data } = await client.get(`/api/courses/${id}`);
  return data;
}

/**
 * PATCH /api/courses/:id
 * { title?, description? }
 */
export async function updateCourse(id, patch) {
  const { data } = await client.patch(`/api/courses/${id}`, patch);
  return data;
}

/**
 * PATCH /api/modules/:id
 * { title?, description? }
 */
export async function updateModule(id, patch) {
  const { data } = await client.patch(`/api/modules/${id}`, patch);
  return data;
}

/**
 * PATCH /api/topics/:id
 * { title?, description? }
 */
export async function updateTopic(id, patch) {
  const { data } = await client.patch(`/api/topics/${id}`, patch);
  return data;
}
