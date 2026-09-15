import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getCourses, getCourse, updateCourse, updateModule, updateTopic } from '../services/api/courseService.js';
import { adaptCourse, adaptCourseList } from '../services/adapters/courseAdapter.js';
import { MOCK_COURSES } from '../mocks/mockData.js';

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

export function useCourses() {
  return useQuery({
    queryKey: ['courses'],
    queryFn: async () => {
      if (USE_MOCKS) return MOCK_COURSES;
      const data = await getCourses();
      return adaptCourseList(data);
    },
  });
}

/**
 * PATCH /api/courses/:id  — update title/description.
 * On success invalidates both ['courses'] list and ['courses', courseId] detail
 * so CourseOverview and Dashboard both reflect the new values.
 */
export function useUpdateCourse(courseId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (patch) => updateCourse(courseId, patch),
    onSuccess: (data) => {
      const adapted = adaptCourse(data);
      queryClient.setQueryData(['courses', courseId], adapted);
      queryClient.invalidateQueries({ queryKey: ['courses'] });
    },
  });
}

/**
 * PATCH /api/modules/:id  — update title/description.
 * Invalidates the parent course so ModuleCard re-renders with fresh data.
 */
export function useUpdateModule(moduleId, courseId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (patch) => updateModule(moduleId, patch),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['courses', courseId] });
    },
  });
}

/**
 * PATCH /api/topics/:id  — update title/description.
 * Invalidates the parent course so TopicCard re-renders.
 */
export function useUpdateTopic(topicId, courseId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (patch) => updateTopic(topicId, patch),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['courses', courseId] });
    },
  });
}

export function useCourse(courseId) {
  return useQuery({
    queryKey: ['courses', courseId],
    queryFn: async () => {
      if (USE_MOCKS) {
        const course = MOCK_COURSES.find((c) => c.id === courseId);
        return course ?? null;
      }
      const data = await getCourse(courseId);
      return adaptCourse(data);
    },
    enabled: Boolean(courseId),
  });
}
