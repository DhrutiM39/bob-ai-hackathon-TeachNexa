import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getTopicContent, generateTopicContent } from '../services/api/topicService.js';
import { adaptTopicContent } from '../services/adapters/topicAdapter.js';
import { MOCK_TOPIC_CONTENT } from '../mocks/mockData.js';

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

export function useTopicContent(topicId) {
  return useQuery({
    queryKey: ['topicContent', topicId],
    queryFn: async () => {
      if (USE_MOCKS) return MOCK_TOPIC_CONTENT;
      const data = await getTopicContent(topicId);
      return adaptTopicContent(data);
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
