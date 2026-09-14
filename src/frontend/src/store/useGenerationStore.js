import { create } from 'zustand';

/**
 * Zustand store for the syllabus → course generation flow.
 * Used exclusively on the /create page; not shared across the app.
 */
const useGenerationStore = create((set) => ({
  // Form state
  courseTitle: '',
  courseCode: '',
  syllabusText: '',
  syllabusFile: null,

  // Generation state
  isGenerating: false,
  currentStage: null,   // one of GENERATION_STAGES[].id
  completedStages: [],
  generatedCourseId: null,
  generationError: null,

  // Form actions
  setField: (field, value) => set({ [field]: value }),
  setSyllabusFile: (file) => set({ syllabusFile: file }),

  // Generation lifecycle
  startGeneration: () => set({
    isGenerating: true,
    currentStage: 'analyzing',
    completedStages: [],
    generatedCourseId: null,
    generationError: null,
  }),
  advanceStage: (stageId) => set((s) => ({
    completedStages: [...s.completedStages, s.currentStage].filter(Boolean),
    currentStage: stageId,
  })),
  finishGeneration: (courseId) => set((s) => ({
    isGenerating: false,
    completedStages: [...s.completedStages, s.currentStage].filter(Boolean),
    currentStage: null,
    generatedCourseId: courseId,
  })),
  failGeneration: (error) => set({
    isGenerating: false,
    generationError: error,
  }),
  resetGeneration: () => set({
    isGenerating: false,
    currentStage: null,
    completedStages: [],
    generatedCourseId: null,
    generationError: null,
  }),
}));

export default useGenerationStore;
