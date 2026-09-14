import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './CreateCourse.module.css';
import useGenerationStore from '../store/useGenerationStore.js';
import { GENERATION_STAGES, ROUTES } from '../constants/index.js';
import { analyzeSyllabus, generateCourse } from '../services/api/syllabusService.js';
import { adaptCourse } from '../services/adapters/courseAdapter.js';
import FileUploader from '../components/syllabus/FileUploader.jsx';
import GenerationProgress from '../components/syllabus/GenerationProgress.jsx';
import Button from '../components/common/Button.jsx';
import PageHeader from '../components/layout/PageHeader.jsx';

const STAGE_IDS = GENERATION_STAGES.map((s) => s.id);

export default function CreateCourse() {
  const navigate = useNavigate();
  const store = useGenerationStore();
  const [formErrors, setFormErrors] = useState({});

  const validate = () => {
    const errs = {};
    if (!store.courseTitle.trim()) errs.courseTitle = 'Course title is required.';
    if (!store.syllabusText.trim() && !store.syllabusFile) {
      errs.syllabus = 'Please provide a syllabus — either paste text or upload a file.';
    }
    return errs;
  };

  const simulateStages = async (coursePayload) => {
    // In production, the backend handles actual stage timing.
    // We simulate progress updates here while awaiting the real API.
    store.startGeneration();

    // If mocks are active, simulate stage advancement
    if (import.meta.env.VITE_USE_MOCKS === 'true') {
      for (let i = 0; i < STAGE_IDS.length; i++) {
        store.advanceStage(STAGE_IDS[i]);
        await delay(900);
      }
      const mockId = 'mock-cs101';
      store.finishGeneration(mockId);
      await delay(600);
      navigate(ROUTES.COURSE_OVERVIEW(mockId));
      return;
    }

    try {
      // Stage 1: analyze
      store.advanceStage('analyzing');
      const analysisResult = await analyzeSyllabus({
        text: store.syllabusText,
        file: store.syllabusFile,
      });

      // Stage 2–3: modules & topics (simulate advancement while waiting)
      store.advanceStage('modules');
      await delay(400);
      store.advanceStage('topics');

      // Stage 4: generate course
      store.advanceStage('organizing');
      const courseData = await generateCourse({
        title: store.courseTitle,
        code: store.courseCode,
        analysis: analysisResult,
      });

      // Stage 5: finalize
      store.advanceStage('content');
      await delay(400);

      const course = adaptCourse(courseData);
      store.finishGeneration(course.id);
      await delay(800);
      navigate(ROUTES.COURSE_OVERVIEW(course.id));
    } catch (err) {
      store.failGeneration(err.message || 'Generation failed. Please try again.');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) {
      setFormErrors(errs);
      return;
    }
    setFormErrors({});
    await simulateStages();
  };

  const handleRetry = () => {
    store.resetGeneration();
  };

  // Render generation progress view
  if (store.isGenerating || store.generatedCourseId) {
    return (
      <div className={styles.page}>
        <GenerationProgress
          currentStage={store.currentStage}
          completedStages={store.completedStages}
          error={store.generationError}
        />
        {store.generationError && (
          <div className={styles.retryRow}>
            <Button variant="secondary" onClick={handleRetry}>← Back to form</Button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <PageHeader
        title="Create New Course"
        subtitle="Paste your syllabus or upload a file and let IBM watsonx.ai build a complete structured course for you."
      />

      {/* What AI does — explanation panel */}
      <div className={styles.aiExplanation} aria-label="What the AI will generate">
        <h2 className={styles.aiTitle}>What CourseGenie AI will generate</h2>
        <div className={styles.aiSteps}>
          {[
            { icon: '🧩', label: 'Structured modules', desc: 'Groups related topics into coherent learning modules' },
            { icon: '📖', label: 'Learning content', desc: 'Objectives, explanations, key concepts, and examples per topic' },
            { icon: '✅', label: 'Quizzes', desc: 'MCQ quiz with explanations for every topic' },
            { icon: '🔁', label: 'Revision materials', desc: 'Quick notes, key takeaways, and a full question bank' },
          ].map(({ icon, label, desc }) => (
            <div key={label} className={styles.aiStep}>
              <span className={styles.aiStepIcon} aria-hidden="true">{icon}</span>
              <div>
                <p className={styles.aiStepLabel}>{label}</p>
                <p className={styles.aiStepDesc}>{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className={styles.form} noValidate aria-label="Create course form">
        <div className={styles.formGrid}>
          <div className={styles.formField}>
            <label htmlFor="courseTitle" className={styles.label}>
              Course Title <span className={styles.required} aria-label="required">*</span>
            </label>
            <input
              id="courseTitle"
              type="text"
              className={`${styles.input} ${formErrors.courseTitle ? styles.inputError : ''}`}
              placeholder="e.g. Introduction to Computer Science"
              value={store.courseTitle}
              onChange={(e) => store.setField('courseTitle', e.target.value)}
              aria-required="true"
              aria-describedby={formErrors.courseTitle ? 'courseTitle-error' : undefined}
            />
            {formErrors.courseTitle && (
              <p id="courseTitle-error" className={styles.fieldError} role="alert">{formErrors.courseTitle}</p>
            )}
          </div>

          <div className={styles.formField}>
            <label htmlFor="courseCode" className={styles.label}>
              Course Code <span className={styles.optional}>(optional)</span>
            </label>
            <input
              id="courseCode"
              type="text"
              className={styles.input}
              placeholder="e.g. CS 101"
              value={store.courseCode}
              onChange={(e) => store.setField('courseCode', e.target.value)}
            />
          </div>
        </div>

        <div className={styles.syllabusSection}>
          <fieldset className={styles.syllabusFieldset}>
            <legend className={styles.legendLabel}>
              Syllabus Content <span className={styles.required} aria-label="required">*</span>
            </legend>
            {formErrors.syllabus && (
              <p className={styles.fieldError} role="alert">{formErrors.syllabus}</p>
            )}

            <div className={styles.syllabusOptions}>
              <div className={styles.syllabusOption}>
                <p className={styles.optionLabel}>Paste syllabus text</p>
                <textarea
                  id="syllabusText"
                  className={`${styles.textarea} ${formErrors.syllabus ? styles.inputError : ''}`}
                  placeholder="Paste your course syllabus here — topics, weeks, learning outcomes, reading lists, etc."
                  rows={10}
                  value={store.syllabusText}
                  onChange={(e) => store.setField('syllabusText', e.target.value)}
                  aria-label="Syllabus text"
                />
              </div>

              <div className={styles.orDivider} aria-hidden="true">
                <span>or</span>
              </div>

              <div className={styles.syllabusOption}>
                <p className={styles.optionLabel}>Upload a file</p>
                <FileUploader
                  file={store.syllabusFile}
                  onChange={(f) => store.setSyllabusFile(f)}
                />
              </div>
            </div>
          </fieldset>
        </div>

        <div className={styles.submitRow}>
          <p className={styles.submitNote}>
            Generation typically takes 30–90 seconds depending on syllabus length.
          </p>
          <Button type="submit" variant="primary" size="lg">
            Generate Course with AI →
          </Button>
        </div>
      </form>
    </div>
  );
}

function delay(ms) {
  return new Promise((res) => setTimeout(res, ms));
}
