export const ROUTES = {
  DASHBOARD: '/',
  CREATE_COURSE: '/create',
  COURSE_OVERVIEW: (id) => `/courses/${id}`,
  TOPIC_LEARNING: (courseId, topicId) => `/courses/${courseId}/topics/${topicId}`,
  QUIZ: (courseId, topicId) => `/courses/${courseId}/topics/${topicId}/quiz`,
  REVISION: (courseId) => `/courses/${courseId}/revision`,
};

export const GENERATION_STAGES = [
  { id: 'analyzing', label: 'Analyzing syllabus', description: 'Parsing course structure and requirements' },
  { id: 'modules', label: 'Identifying modules', description: 'Grouping related topics into coherent modules' },
  { id: 'topics', label: 'Extracting topics', description: 'Identifying individual learning topics' },
  { id: 'organizing', label: 'Organizing course', description: 'Building course hierarchy and dependencies' },
  { id: 'content', label: 'Preparing content', description: 'Setting up content generation pipeline' },
];

export const TOPIC_STATUS = {
  NOT_STARTED: 'not_started',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
};

export const QUIZ_STATUS = {
  NOT_TAKEN: 'not_taken',
  IN_PROGRESS: 'in_progress',
  PASSED: 'passed',
  FAILED: 'failed',
};

export const ACCEPTED_FILE_TYPES = [
  'application/pdf',
  'text/plain',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
];

export const MAX_FILE_SIZE_MB = 10;
export const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;
