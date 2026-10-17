"""Original demo lesson content seeded into the local SQLite database."""

from typing import TypedDict


class LessonSeed(TypedDict):
    id: str
    subject_id: str
    subject_name: str
    topic: str
    title: str
    content: dict[str, object]


class QuestionSeed(TypedDict):
    id: str
    lesson_id: str
    subject_id: str
    topic: str
    difficulty: str
    rating: int
    prompt: str
    choices: list[str]
    accepted_answers: list[str]


SCIENCE_LESSONS: tuple[LessonSeed, ...] = (
    {
        "id": "science-matter-basics",
        "subject_id": "science",
        "subject_name": "Science",
        "topic": "States of Matter",
        "title": "Matter Around Us",
        "content": {
            "summary": "Matter is anything that has mass and takes up space. Solids, liquids, and gases are common states of matter.",
            "key_points": [
                "A solid keeps its own shape because its particles stay close together.",
                "A liquid can flow and takes the shape of its container.",
                "A gas spreads out to fill the available space.",
            ],
            "vocabulary": {
                "matter": "Anything that has mass and occupies space.",
                "particle": "A tiny piece of matter.",
                "state": "A form that matter can take, such as solid, liquid, or gas.",
            },
            "try_it": "Compare an ice cube, a glass of water, and the air in a balloon. Describe how each one keeps or changes its shape.",
            "quiz_ready_facts": [
                "Water can be ice, liquid water, or water vapour.",
                "Heating or cooling can change the state of matter.",
            ],
        },
    },
)


SCIENCE_QUESTIONS: tuple[QuestionSeed, ...] = (
    {
        "id": "matter-solid-shape",
        "lesson_id": "science-matter-basics",
        "subject_id": "science",
        "topic": "States of Matter",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "Which state of matter keeps its own shape?",
        "choices": ["Solid", "Liquid", "Gas"],
        "accepted_answers": ["solid"],
    },
    {
        "id": "matter-liquid-container",
        "lesson_id": "science-matter-basics",
        "subject_id": "science",
        "topic": "States of Matter",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "A liquid usually takes the shape of its what?",
        "choices": ["Container", "Colour", "Shadow"],
        "accepted_answers": ["container"],
    },
    {
        "id": "matter-gas-space",
        "lesson_id": "science-matter-basics",
        "subject_id": "science",
        "topic": "States of Matter",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "Why can a gas fill a balloon?",
        "choices": ["Its particles spread out", "It has a fixed shape", "It has no mass"],
        "accepted_answers": ["its particles spread out", "particles spread out"],
    },
    {
        "id": "matter-water-states",
        "lesson_id": "science-matter-basics",
        "subject_id": "science",
        "topic": "States of Matter",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "Which change can turn liquid water into water vapour?",
        "choices": ["Heating", "Freezing", "Breaking"],
        "accepted_answers": ["heating"],
    },
    {
        "id": "matter-solid-particles",
        "lesson_id": "science-matter-basics",
        "subject_id": "science",
        "topic": "States of Matter",
        "difficulty": "hard",
        "rating": 1100,
        "prompt": "Which description best explains why a solid has a fixed shape?",
        "choices": [
            "Its particles stay close together and only vibrate",
            "Its particles move freely far apart",
            "It has no particles",
        ],
        "accepted_answers": ["its particles stay close together and only vibrate"],
    },
    {
        "id": "matter-freezing-particles",
        "lesson_id": "science-matter-basics",
        "subject_id": "science",
        "topic": "States of Matter",
        "difficulty": "hard",
        "rating": 1100,
        "prompt": "When liquid water freezes, what happens to its particles?",
        "choices": [
            "They move less and arrange more closely",
            "They disappear",
            "They spread to fill all space",
        ],
        "accepted_answers": ["they move less and arrange more closely"],
    },
)
