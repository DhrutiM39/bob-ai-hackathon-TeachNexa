/**
 * topicAdapter — normalizes topic content responses.
 */

export function adaptTopicContent(raw) {
  if (!raw) return null;
  return {
    topicId:          raw.topic_id ?? raw.topicId ?? raw.id ?? null,
    title:            raw.title ?? '',
    objectives:       toArray(raw.learning_objectives ?? raw.objectives ?? raw.learningObjectives),
    explanation:      raw.explanation ?? raw.content ?? raw.body ?? '',
    keyConcepts:      adaptKeyConcepts(raw.key_concepts ?? raw.keyConcepts ?? raw.concepts),
    examples:         toArray(raw.examples).map(adaptExample),
    summary:          raw.summary ?? raw.conclusion ?? '',
    furtherReading:   toArray(raw.further_reading ?? raw.furtherReading ?? raw.references),
    generatedAt:      raw.generated_at ?? raw.generatedAt ?? null,
  };
}

function adaptKeyConcepts(raw) {
  if (!raw) return [];
  if (Array.isArray(raw)) {
    return raw.map((item) => {
      if (typeof item === 'string') return { term: item, definition: '' };
      return {
        term:       item.term ?? item.concept ?? item.name ?? item.key ?? '',
        definition: item.definition ?? item.description ?? item.meaning ?? '',
      };
    });
  }
  if (typeof raw === 'object') {
    return Object.entries(raw).map(([term, definition]) => ({ term, definition: String(definition) }));
  }
  return [];
}

function adaptExample(raw) {
  if (!raw) return { title: '', content: '' };
  if (typeof raw === 'string') return { title: '', content: raw };
  return {
    title:   raw.title ?? raw.name ?? '',
    content: raw.content ?? raw.example ?? raw.description ?? '',
  };
}

function toArray(val) {
  if (!val) return [];
  if (Array.isArray(val)) return val;
  if (typeof val === 'string') return val.split('\n').filter(Boolean);
  return [val];
}
