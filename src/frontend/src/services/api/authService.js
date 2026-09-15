import client from './client.js';

export async function signup({ name, email, password }) {
  const { data } = await client.post('/api/auth/signup', { name, email, password });
  return data;
}

export async function login({ email, password }) {
  const { data } = await client.post('/api/auth/login', { email, password });
  return data;
}

export async function getMe() {
  const { data } = await client.get('/api/auth/me');
  return data;
}
