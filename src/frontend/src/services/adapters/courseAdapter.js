/**
 * courseAdapter — normalizes GET /api/courses and GET /api/courses/:id responses.
 * Field names are defensive: each falls back gracefully if the backend uses
 * a different naming convention.
 */

export function adaptCourse(raw) {
  if (!raw) return null;
  return {
    id:          raw.id ?? raw.course_id ?? raw._id ?? null,
    title:       raw.title ?? raw.course_title ?? raw.name ?? 'Untitled Course',
    code:        raw.code ?? raw.course_code ?? raw.courseCode ?? '',
    description: raw.description ?? raw.summary ?? '',
    createdAt:   raw.created_at ?? raw.createdAt ?? raw.created ?? null,
    updatedAt:   raw.updated_at ?? raw.updatedAt ?? null,
    modules:     Array.isArray(raw.modules) ? raw.modules.map(adaptModule) : [],
    status:      raw.status ?? 'ready',
    totalTopics: raw.total_topics ?? raw.totalTopics ?? computeTotalTopics(raw.modules),
    completedTopics: raw.completed_topics ?? raw.completedTopics ?? 0,
  };
}

export function adaptModule(raw) {
  if (!raw) return null;
  return {
    id:          raw.id ?? raw.module_id ?? raw._id ?? null,
    title:       raw.title ?? raw.module_title ?? raw.name ?? 'Untitled Module',
    description: raw.description ?? '',
    order:       raw.order ?? raw.sequence ?? raw.index ?? 0,
    topics:      Array.isArray(raw.topics) ? raw.topics.map(adaptTopic) : [],
  };
}

export function adaptTopic(raw) {
  if (!raw) return null;
  return {
    id:          raw.id ?? raw.topic_id ?? raw._id ?? null,
    title:       raw.title ?? raw.topic_title ?? raw.name ?? 'Untitled Topic',
    description: raw.description ?? raw.summary ?? '',
    order:       raw.order ?? raw.sequence ?? raw.index ?? 0,
    status:      raw.status ?? 'not_started',
    hasContent:  raw.has_content ?? raw.hasContent ?? raw.content_generated ?? false,
    hasQuiz:     raw.has_quiz ?? raw.hasQuiz ?? raw.quiz_generated ?? false,
  };
}

export function adaptCourseList(raw) {
  if (!raw) return [];
  const list = Array.isArray(raw) ? raw : (raw.courses ?? raw.data ?? raw.results ?? []);
  return list.map(adaptCourse);
}

function computeTotalTopics(modules) {
  if (!Array.isArray(modules)) return 0;
  return modules.reduce((sum, m) => sum + (Array.isArray(m?.topics) ? m.topics.length : 0), 0);
}
