import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getTopicContent, generateTopicContent } from '../services/api/topicService.js';
import { adaptTopicContent } from '../services/adapters/topicAdapter.js';
import { MOCK_TOPIC_CONTENT } from '../mocks/mockData.js';

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

/**
 * Fetch existing topic content.
 * The backend returns 404 when content has not been generated yet — this is
 * normal (not an error). We return null so the page shows the EmptyState +
 * "Generate Content" button instead of an error screen.
 */
export function useTopicContent(topicId) {
  return useQuery({
    queryKey: ['topicContent', topicId],
    queryFn: async () => {
      if (USE_MOCKS) return MOCK_TOPIC_CONTENT;
      try {
        const data = await getTopicContent(topicId);
        return adaptTopicContent(data);
      } catch (err) {
        // 404 = content not generated yet → treat as empty, not an error
        if (err?.status === 404) return null;
        throw err;
      }
    },
    enabled: Boolean(topicId),
  });
}

export function useGenerateTopicContent(topicId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => generateTopicContent(topicId),
    onSuccess: (data) => {
      queryClient.setQueryData(['topicContent', topicId], adaptTopicContent(data));
    },
  });
}
