import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getCourses, getCourse } from '../services/api/courseService.js';
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
