import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getQuiz, generateQuiz, getRevision, generateRevision } from '../services/api/quizService.js';
import { adaptQuiz, adaptRevision } from '../services/adapters/quizAdapter.js';
import { MOCK_QUIZ, MOCK_REVISION } from '../mocks/mockData.js';

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

/**
 * Fetch existing quiz for a topic.
 * The backend returns 404 when no quiz has been generated yet — this is
 * normal (not an error). We return null so the page shows the EmptyState +
 * "Generate Quiz" button instead of an error screen.
 */
export function useQuiz(topicId) {
  return useQuery({
    queryKey: ['quiz', topicId],
    queryFn: async () => {
      if (USE_MOCKS) return MOCK_QUIZ;
      try {
        const data = await getQuiz(topicId);
        return adaptQuiz(data);
      } catch (err) {
        // 404 = quiz not generated yet → treat as empty, not an error
        if (err?.status === 404) return null;
        throw err;
      }
    },
    enabled: Boolean(topicId),
  });
}

export function useGenerateQuiz(topicId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => generateQuiz(topicId),
    onSuccess: (data) => {
      queryClient.setQueryData(['quiz', topicId], adaptQuiz(data));
    },
  });
}

/**
 * Fetch existing revision materials for a course.
 * The backend returns 404 when revision has not been generated yet — this is
 * normal (not an error). We return null so the page shows the EmptyState +
 * "Generate Revision" button instead of an error screen.
 */
export function useRevision(courseId) {
  return useQuery({
    queryKey: ['revision', courseId],
    queryFn: async () => {
      if (USE_MOCKS) return MOCK_REVISION;
      try {
        const data = await getRevision(courseId);
        return adaptRevision(data);
      } catch (err) {
        // 404 = revision not generated yet → treat as empty, not an error
        if (err?.status === 404) return null;
        throw err;
      }
    },
    enabled: Boolean(courseId),
  });
}

export function useGenerateRevision(courseId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => generateRevision(courseId),
    onSuccess: (data) => {
      queryClient.setQueryData(['revision', courseId], adaptRevision(data));
    },
  });
}
