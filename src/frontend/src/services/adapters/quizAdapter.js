/**
 * quizAdapter — normalizes quiz and revision responses.
 */

export function adaptQuiz(raw) {
  if (!raw) return null;
  const questionList = raw.questions ?? raw.quiz_questions ?? raw.items ?? [];
  return {
    id:          raw.id ?? raw.quiz_id ?? null,
    topicId:     raw.topic_id ?? raw.topicId ?? null,
    title:       raw.title ?? 'Topic Quiz',
    questions:   Array.isArray(questionList) ? questionList.map(adaptQuestion) : [],
    generatedAt: raw.generated_at ?? raw.generatedAt ?? null,
  };
}

export function adaptQuestion(raw, index = 0) {
  if (!raw) return null;
  const options = adaptOptions(raw.options ?? raw.choices ?? raw.answers ?? []);
  return {
    id:           raw.id ?? raw.question_id ?? `q_${index}`,
    text:         raw.question ?? raw.text ?? raw.question_text ?? '',
    options,
    correctIndex: findCorrectIndex(raw, options),
    explanation:  raw.explanation ?? raw.rationale ?? raw.reason ?? '',
  };
}

function adaptOptions(raw) {
  if (!Array.isArray(raw)) return [];
  return raw.map((opt, i) => {
    if (typeof opt === 'string') return { id: String(i), text: opt };
    return {
      id:   String(opt.id ?? opt.value ?? i),
      text: opt.text ?? opt.label ?? opt.option ?? opt.content ?? String(opt),
    };
  });
}

function findCorrectIndex(raw, options) {
  // Backend may give: correct_answer (text), correct_index (number), correct_option_id
  if (typeof raw.correct_index === 'number') return raw.correct_index;
  if (typeof raw.correct_option_index === 'number') return raw.correct_option_index;
  if (raw.correct_answer) {
    const idx = options.findIndex(
      (o) => o.text === raw.correct_answer || o.id === String(raw.correct_answer)
    );
    return idx >= 0 ? idx : 0;
  }
  if (raw.correct_option_id != null) {
    const idx = options.findIndex((o) => o.id === String(raw.correct_option_id));
    return idx >= 0 ? idx : 0;
  }
  return 0;
}

export function adaptRevision(raw) {
  if (!raw) return null;
  return {
    courseId:         raw.course_id ?? raw.courseId ?? null,
    quickNotes:       toArray(raw.quick_notes ?? raw.quickNotes ?? raw.revision_notes),
    keyTakeaways:     toArray(raw.key_takeaways ?? raw.keyTakeaways ?? raw.takeaways),
    practiceQuestions: Array.isArray(raw.practice_questions ?? raw.practiceQuestions)
      ? (raw.practice_questions ?? raw.practiceQuestions).map(adaptQuestion)
      : [],
    questionBank:     Array.isArray(raw.question_bank ?? raw.questionBank)
      ? (raw.question_bank ?? raw.questionBank).map(adaptQuestion)
      : [],
    generatedAt:      raw.generated_at ?? raw.generatedAt ?? null,
  };
}

function toArray(val) {
  if (!val) return [];
  if (Array.isArray(val)) return val;
  if (typeof val === 'string') return val.split('\n').filter(Boolean);
  return [val];
}
