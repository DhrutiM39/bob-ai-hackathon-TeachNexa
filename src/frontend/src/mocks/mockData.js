/**
 * MOCK DATA — only used when VITE_USE_MOCKS=true
 * These are clearly labelled demo fixtures, NOT real AI output.
 */

export const MOCK_COURSES = [
  {
    id: 'mock-cs101',
    title: 'Introduction to Computer Science',
    code: 'CS 101',
    description: 'Foundational concepts of computing, algorithms, and programming.',
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-03-20T14:30:00Z',
    status: 'ready',
    totalTopics: 12,
    completedTopics: 7,
    modules: [
      {
        id: 'mock-m1',
        title: 'Foundations of Computing',
        description: 'History and fundamentals of computation.',
        order: 0,
        topics: [
          { id: 'mock-t1', title: 'History of Computing', description: 'From Turing to the Internet age.', order: 0, status: 'completed', hasContent: true, hasQuiz: true },
          { id: 'mock-t2', title: 'Binary & Number Systems', description: 'How computers represent data.', order: 1, status: 'completed', hasContent: true, hasQuiz: true },
          { id: 'mock-t3', title: 'Logic Gates & Circuits', description: 'Boolean algebra and digital circuits.', order: 2, status: 'in_progress', hasContent: true, hasQuiz: false },
        ],
      },
      {
        id: 'mock-m2',
        title: 'Programming Fundamentals',
        description: 'Core programming concepts with Python.',
        order: 1,
        topics: [
          { id: 'mock-t4', title: 'Variables and Data Types', description: 'Storing and manipulating data.', order: 0, status: 'completed', hasContent: true, hasQuiz: true },
          { id: 'mock-t5', title: 'Control Flow', description: 'If/else, loops, and iteration patterns.', order: 1, status: 'completed', hasContent: true, hasQuiz: true },
          { id: 'mock-t6', title: 'Functions and Modularity', description: 'Defining and calling functions.', order: 2, status: 'not_started', hasContent: false, hasQuiz: false },
        ],
      },
      {
        id: 'mock-m3',
        title: 'Data Structures',
        description: 'Organizing and storing data efficiently.',
        order: 2,
        topics: [
          { id: 'mock-t7', title: 'Arrays and Lists', description: 'Sequential data structures.', order: 0, status: 'not_started', hasContent: false, hasQuiz: false },
          { id: 'mock-t8', title: 'Stacks and Queues', description: 'LIFO and FIFO structures.', order: 1, status: 'not_started', hasContent: false, hasQuiz: false },
          { id: 'mock-t9', title: 'Hash Tables', description: 'Key-value storage and collision handling.', order: 2, status: 'not_started', hasContent: false, hasQuiz: false },
        ],
      },
    ],
  },
  {
    id: 'mock-ds201',
    title: 'Data Science Fundamentals',
    code: 'DS 201',
    description: 'Introduction to data analysis, visualization, and machine learning.',
    createdAt: '2024-02-01T09:00:00Z',
    updatedAt: '2024-03-18T11:00:00Z',
    status: 'ready',
    totalTopics: 9,
    completedTopics: 2,
    modules: [
      {
        id: 'mock-m4',
        title: 'Data Analysis with Python',
        description: 'NumPy, Pandas, and data wrangling.',
        order: 0,
        topics: [
          { id: 'mock-t10', title: 'Introduction to NumPy', description: 'Numerical computing fundamentals.', order: 0, status: 'completed', hasContent: true, hasQuiz: true },
          { id: 'mock-t11', title: 'Pandas DataFrames', description: 'Tabular data manipulation.', order: 1, status: 'completed', hasContent: true, hasQuiz: false },
          { id: 'mock-t12', title: 'Data Cleaning', description: 'Handling missing and messy data.', order: 2, status: 'not_started', hasContent: false, hasQuiz: false },
        ],
      },
    ],
  },
];

export const MOCK_TOPIC_CONTENT = {
  topicId: 'mock-t1',
  title: 'History of Computing',
  objectives: [
    'Understand the key milestones in computing history',
    'Identify the contributions of pioneers like Turing and Von Neumann',
    'Explain how hardware has evolved from vacuum tubes to microchips',
  ],
  explanation: `Computing as we know it emerged from a convergence of mathematical theory, wartime necessity, and engineering ingenuity. The conceptual foundations were laid by **Charles Babbage**, who designed the Analytical Engine in the 1830s — a mechanical device capable of general-purpose computation. Ada Lovelace, working alongside Babbage, is widely credited as the first programmer for her notes on how the engine could compute Bernoulli numbers.

The 20th century saw computation leap from theory into physical reality. **Alan Turing's** 1936 paper "On Computable Numbers" defined what it means for a problem to be mechanically solvable, giving birth to the concept of the universal Turing machine. During World War II, this theory was pressed into service: Turing led the team at Bletchley Park that cracked the Enigma cipher using electro-mechanical devices called Bombes.

The first fully electronic, general-purpose computers arrived in the late 1940s. **ENIAC** (1945) used 18,000 vacuum tubes and filled an entire room. Shortly after, the **Von Neumann architecture** — with a CPU, memory, and stored programs — became the blueprint that virtually every computer still follows today.

The transistor revolution of the 1950s shrank computing from room-sized machines to desktop devices. Intel's introduction of the microprocessor in 1971 placed a complete CPU on a single chip, enabling the personal computer era of the 1980s and the internet-connected world of the 1990s and beyond.`,
  keyConcepts: [
    { term: 'Turing Machine', definition: 'A theoretical computational model that defines the limits of what is mechanically computable.' },
    { term: 'Von Neumann Architecture', definition: 'A computer design model with a CPU, memory, and stored-program concept, foundational to modern computers.' },
    { term: 'Transistor', definition: 'A semiconductor device that replaced vacuum tubes, enabling miniaturization and modern microelectronics.' },
    { term: 'Microprocessor', definition: 'An entire CPU integrated onto a single silicon chip, first produced commercially by Intel in 1971.' },
  ],
  examples: [
    { title: 'ENIAC (1945)', content: 'One of the first general-purpose electronic computers. It weighed 30 tons, contained 18,000 vacuum tubes, and could perform 5,000 additions per second.' },
    { title: 'Moore\'s Law', content: 'Gordon Moore observed in 1965 that transistor counts on chips doubled roughly every two years — a prediction that held true for over five decades and drove exponential performance improvements.' },
  ],
  summary: 'Computing history is a story of successive abstractions: from mechanical gears, to vacuum tubes, to transistors, to integrated circuits, to microprocessors. Each leap dramatically increased capability while reducing cost and size.',
  furtherReading: [
    '"The Dream Machine" by M. Mitchell Waldrop',
    '"The Man from the Future" by Ananyo Bhattacharya (biography of Von Neumann)',
    'ACM Digital Library — Turing Award lectures',
  ],
  generatedAt: '2024-01-16T08:00:00Z',
};

export const MOCK_QUIZ = {
  id: 'mock-q1',
  topicId: 'mock-t1',
  title: 'History of Computing — Quiz',
  questions: [
    {
      id: 'mq1',
      text: 'Who is credited with designing the first general-purpose mechanical computer, the Analytical Engine?',
      options: [
        { id: '0', text: 'Alan Turing' },
        { id: '1', text: 'Charles Babbage' },
        { id: '2', text: 'John Von Neumann' },
        { id: '3', text: 'Ada Lovelace' },
      ],
      correctIndex: 1,
      explanation: 'Charles Babbage designed the Analytical Engine in the 1830s. Ada Lovelace, while often called the first programmer, was a collaborator who wrote notes on Babbage\'s machine.',
    },
    {
      id: 'mq2',
      text: 'What is the key insight of the Von Neumann architecture?',
      options: [
        { id: '0', text: 'Using vacuum tubes instead of mechanical relays' },
        { id: '1', text: 'Parallel processing with multiple CPUs' },
        { id: '2', text: 'Storing programs in the same memory as data' },
        { id: '3', text: 'Using binary instead of decimal arithmetic' },
      ],
      correctIndex: 2,
      explanation: 'The Von Neumann architecture\'s critical innovation was the stored-program concept: keeping both instructions and data in the same memory, allowing programs to be changed without rewiring hardware.',
    },
    {
      id: 'mq3',
      text: 'Approximately how many vacuum tubes did the ENIAC computer contain?',
      options: [
        { id: '0', text: '1,800' },
        { id: '1', text: '18,000' },
        { id: '2', text: '180,000' },
        { id: '3', text: '1,800,000' },
      ],
      correctIndex: 1,
      explanation: 'ENIAC (1945) contained approximately 18,000 vacuum tubes. Its scale made it groundbreaking but also fragile — a tube failure halted the machine.',
    },
    {
      id: 'mq4',
      text: 'What did Moore\'s Law originally predict?',
      options: [
        { id: '0', text: 'Internet bandwidth doubles every 18 months' },
        { id: '1', text: 'CPU clock speeds double every year' },
        { id: '2', text: 'Transistor counts on chips double approximately every two years' },
        { id: '3', text: 'Software complexity doubles every decade' },
      ],
      correctIndex: 2,
      explanation: 'Gordon Moore observed in 1965 that the number of transistors on integrated circuits doubled roughly every two years, a trend that predicted exponential improvements in computing power.',
    },
  ],
  generatedAt: '2024-01-16T08:05:00Z',
};

export const MOCK_REVISION = {
  courseId: 'mock-cs101',
  quickNotes: [
    'Babbage designed the Analytical Engine; Lovelace wrote the first algorithm.',
    'Turing\'s 1936 paper defined computability — foundation of computer science theory.',
    'ENIAC (1945) was the first electronic general-purpose computer — 18,000 vacuum tubes.',
    'Von Neumann architecture: CPU + Memory + Stored Programs — still the standard today.',
    'Transistors replaced vacuum tubes in the 1950s, enabling miniaturization.',
    'Intel 4004 (1971) — first commercial microprocessor, started the PC revolution.',
  ],
  keyTakeaways: [
    'Computing is built on successive layers of abstraction over 200 years.',
    'Theory (Turing) and engineering (Von Neumann) equally shaped modern computers.',
    'Moore\'s Law drove exponential growth but is now reaching physical limits.',
    'The stored-program concept is the single most important architectural insight in computing.',
  ],
  practiceQuestions: [
    {
      id: 'pq1',
      text: 'Explain the significance of the stored-program concept in modern computing.',
      options: [
        { id: '0', text: 'It eliminated the need for input devices' },
        { id: '1', text: 'It allowed programs to be changed without rewiring hardware' },
        { id: '2', text: 'It doubled the processing speed of computers' },
        { id: '3', text: 'It reduced power consumption significantly' },
      ],
      correctIndex: 1,
      explanation: 'The stored-program concept meant that instructions lived in memory alongside data, making computers flexible and reprogrammable — the foundation of software as we know it.',
    },
  ],
  questionBank: [
    {
      id: 'bq1',
      text: 'Which device directly preceded the transistor in electronic computers?',
      options: [
        { id: '0', text: 'Punch cards' },
        { id: '1', text: 'Mechanical relays' },
        { id: '2', text: 'Vacuum tubes' },
        { id: '3', text: 'Integrated circuits' },
      ],
      correctIndex: 2,
      explanation: 'Vacuum tubes were the primary switching/amplifying components in early electronic computers like ENIAC, before transistors replaced them in the late 1940s–1950s.',
    },
    {
      id: 'bq2',
      text: 'What year did Intel release the first commercial microprocessor?',
      options: [
        { id: '0', text: '1965' },
        { id: '1', text: '1971' },
        { id: '2', text: '1981' },
        { id: '3', text: '1985' },
      ],
      correctIndex: 1,
      explanation: 'Intel released the 4004 microprocessor in 1971, the first commercially available microprocessor, containing 2,300 transistors.',
    },
  ],
  generatedAt: '2024-01-16T08:10:00Z',
};
