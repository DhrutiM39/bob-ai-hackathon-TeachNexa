import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getQuiz, generateQuiz, getRevision, generateRevision } from '../services/api/quizService.js';
import { adaptQuiz, adaptRevision } from '../services/adapters/quizAdapter.js';
import { MOCK_QUIZ, MOCK_REVISION } from '../mocks/mockData.js';

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

export function useQuiz(topicId) {
  return useQuery({
    queryKey: ['quiz', topicId],
    queryFn: async () => {
      if (USE_MOCKS) return MOCK_QUIZ;
      const data = await getQuiz(topicId);
      return adaptQuiz(data);
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

export function useRevision(courseId) {
  return useQuery({
    queryKey: ['revision', courseId],
    queryFn: async () => {
      if (USE_MOCKS) return MOCK_REVISION;
      const data = await getRevision(courseId);
      return adaptRevision(data);
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
