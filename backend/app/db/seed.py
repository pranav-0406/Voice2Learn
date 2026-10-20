"""
Class 6 Term 1 — Tamil Nadu State Board curriculum seed data.

Covers all four English-medium subjects:
  English · Mathematics · Science · Social Science

Content is grounded in the official 2024/2025 Samacheer Kalvi textbooks.
All inserts use INSERT OR IGNORE, so existing learner data is never overwritten.
"""

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


# ─────────────────────────────────────────────────────────────────────────────
# ENGLISH  (3 lessons · Unit 1–3)
# ─────────────────────────────────────────────────────────────────────────────

ENGLISH_LESSONS: tuple[LessonSeed, ...] = (
    {
        "id": "english-sea-turtles",
        "subject_id": "english",
        "subject_name": "English",
        "topic": "Marine Life",
        "title": "Sea Turtles",
        "content": {
            "summary": (
                "Sea turtles are ancient marine reptiles. There are seven species worldwide, "
                "and five are found in India's coastal waters. Despite spending almost their "
                "entire lives in the ocean, they must come ashore to lay eggs."
            ),
            "key_points": [
                "There are seven species of sea turtles in the world.",
                "Five species are found in India: Olive Ridley, Hawksbill, Green Sea Turtle, "
                "Loggerhead, and Leatherback.",
                "The Leatherback is the largest, growing up to 2.2 m and weighing 700 kg.",
                "Sea turtles come ashore only to lay eggs; the rest of their life is in the ocean.",
                "Arribada is a mass nesting event where thousands of Olive Ridleys nest together "
                "on one beach — Odisha is one of only three such places in the world.",
            ],
            "vocabulary": {
                "marine": "Found in or related to the sea.",
                "species": "A group of animals sharing common features and able to breed together.",
                "coastal": "Land by the edge of a sea.",
                "Arribada": "A Spanish word meaning 'arrival'; describes mass nesting of sea turtles.",
                "nesting": "The process of laying eggs in a prepared place.",
            },
            "try_it": (
                "List the five sea turtle species found in India. "
                "For each one, write one fact that makes it special."
            ),
            "quiz_ready_facts": [
                "The Olive Ridley is the smallest sea turtle species found in India.",
                "Sea turtles must return to land to lay their eggs.",
                "Odisha hosts one of only three Arribada nesting beaches in the world.",
            ],
        },
    },
    {
        "id": "english-when-trees-walked",
        "subject_id": "english",
        "subject_name": "English",
        "topic": "Nature and Environment",
        "title": "When the Trees Walked",
        "content": {
            "summary": (
                "Ruskin Bond's story tells how his grandfather passionately planted trees in the "
                "Doon valley. The narrator returns years later to discover that the trees have "
                "spread into a small forest, seeming almost as if they had walked across the land."
            ),
            "key_points": [
                "Grandfather planted trees in the Doon valley because he loved nature.",
                "Plants grow towards sunlight — their roots and stems spread in search of light.",
                "When the narrator returned after many years, the trees had spread to form a small forest.",
                "The title 'When the Trees Walked' is a metaphor for how plants spread and grow over time.",
                "The story shows that one person's love for nature can create lasting change.",
            ],
            "vocabulary": {
                "flourishing": "Growing healthily and successfully.",
                "metaphor": "A figure of speech describing one thing as if it were another.",
                "narrator": "The person who tells the story.",
                "passion": "A very strong feeling of enthusiasm or love for something.",
                "spread": "To extend over a wider area.",
            },
            "try_it": (
                "Think of a place near your home that could benefit from more trees. "
                "Write three sentences describing what you would plant and why."
            ),
            "quiz_ready_facts": [
                "Ruskin Bond is the author of 'When the Trees Walked'.",
                "Plants grow towards sunlight through a process called phototropism.",
                "The story is set in the Doon valley in India.",
            ],
        },
    },
    {
        "id": "english-visitor-distant-lands",
        "subject_id": "english",
        "subject_name": "English",
        "topic": "World Cultures and Trade",
        "title": "A Visitor from Distant Lands",
        "content": {
            "summary": (
                "This prose explains how ancient spice traders and explorers like Vasco da Gama "
                "and Columbus sailed across the world in search of spices. Many spices we use "
                "daily — chilli, pepper, cinnamon — have fascinating global travel stories."
            ),
            "key_points": [
                "Spices were highly valued in ancient and medieval times, often worth more than gold.",
                "Vasco da Gama sailed from Portugal to Calicut (Kozhikode) in 1497–1499, opening a "
                "sea route to India for Europe.",
                "Christopher Columbus sailed in 1492 looking for India but reached the Americas, "
                "discovering chillies and potatoes.",
                "Black pepper originally came from Kerala, India, and was a key item in ancient trade.",
                "Cinnamon, cardamom, and cloves were also major spice trade commodities.",
            ],
            "vocabulary": {
                "commodity": "A raw material or agricultural product that can be bought and sold.",
                "explorer": "A person who travels to unknown or unfamiliar places to discover new things.",
                "trade route": "A path used by merchants to transport goods between regions.",
                "merchant": "A person who buys and sells goods, especially in large quantities.",
                "spice": "A plant substance used to flavour food, often with strong aroma.",
            },
            "try_it": (
                "Choose one spice used in your home kitchen. Find out where it originally came from "
                "and write a short paragraph about its journey to your plate."
            ),
            "quiz_ready_facts": [
                "Vasco da Gama reached Calicut (India) in 1498 after sailing around Africa.",
                "Columbus reached the Americas in 1492 while searching for a sea route to India.",
                "Chilli and potato were introduced to India after Columbus's voyages to the Americas.",
            ],
        },
    },
)

ENGLISH_QUESTIONS: tuple[QuestionSeed, ...] = (
    # Sea Turtles
    {
        "id": "eng-turtles-species-count",
        "lesson_id": "english-sea-turtles",
        "subject_id": "english",
        "topic": "Marine Life",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "How many species of sea turtles are there in the world?",
        "choices": ["Five", "Seven", "Ten", "Three"],
        "accepted_answers": ["seven"],
    },
    {
        "id": "eng-turtles-india-species",
        "lesson_id": "english-sea-turtles",
        "subject_id": "english",
        "topic": "Marine Life",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "How many species of sea turtles are found in India's coastal waters?",
        "choices": ["Three", "Four", "Five", "Seven"],
        "accepted_answers": ["five"],
    },
    {
        "id": "eng-turtles-largest",
        "lesson_id": "english-sea-turtles",
        "subject_id": "english",
        "topic": "Marine Life",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "Which is the largest species of sea turtle?",
        "choices": ["Olive Ridley", "Hawksbill", "Leatherback", "Green Sea Turtle"],
        "accepted_answers": ["leatherback"],
    },
    {
        "id": "eng-turtles-arribada",
        "lesson_id": "english-sea-turtles",
        "subject_id": "english",
        "topic": "Marine Life",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "What is 'Arribada'?",
        "choices": [
            "A type of sea turtle found only in Spain",
            "Mass nesting of sea turtles on a single beach",
            "The migration path of Olive Ridleys",
            "A disease affecting sea turtles",
        ],
        "accepted_answers": [
            "mass nesting of sea turtles on a single beach",
            "mass nesting",
        ],
    },
    {
        "id": "eng-turtles-odisha",
        "lesson_id": "english-sea-turtles",
        "subject_id": "english",
        "topic": "Marine Life",
        "difficulty": "hard",
        "rating": 1100,
        "prompt": "Why is Odisha significant for Olive Ridley sea turtles?",
        "choices": [
            "It is the only place turtles are found in India",
            "It is one of three places in the world where Arribada nesting occurs",
            "It has the largest turtle rehabilitation centre",
            "Turtles were first discovered there",
        ],
        "accepted_answers": [
            "it is one of three places in the world where arribada nesting occurs",
            "one of three places",
            "arribada nesting",
        ],
    },
    # When the Trees Walked
    {
        "id": "eng-trees-author",
        "lesson_id": "english-when-trees-walked",
        "subject_id": "english",
        "topic": "Nature and Environment",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "Who wrote 'When the Trees Walked'?",
        "choices": ["R.K. Narayan", "Ruskin Bond", "Rabindranath Tagore", "Vijaya Ghose"],
        "accepted_answers": ["ruskin bond"],
    },
    {
        "id": "eng-trees-valley",
        "lesson_id": "english-when-trees-walked",
        "subject_id": "english",
        "topic": "Nature and Environment",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "In which valley did Grandfather plant his trees?",
        "choices": ["Brahmaputra valley", "Doon valley", "Narmada valley", "Indus valley"],
        "accepted_answers": ["doon valley", "doon"],
    },
    {
        "id": "eng-trees-metaphor",
        "lesson_id": "english-when-trees-walked",
        "subject_id": "english",
        "topic": "Nature and Environment",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "The title 'When the Trees Walked' is an example of which literary device?",
        "choices": ["Simile", "Rhyme", "Metaphor", "Alliteration"],
        "accepted_answers": ["metaphor"],
    },
    # Visitor from Distant Lands
    {
        "id": "eng-spice-vasco",
        "lesson_id": "english-visitor-distant-lands",
        "subject_id": "english",
        "topic": "World Cultures and Trade",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "Which explorer sailed from Portugal to Calicut, India in 1497–1499?",
        "choices": ["Christopher Columbus", "Ferdinand Magellan", "Vasco da Gama", "Marco Polo"],
        "accepted_answers": ["vasco da gama"],
    },
    {
        "id": "eng-spice-columbus-discovery",
        "lesson_id": "english-visitor-distant-lands",
        "subject_id": "english",
        "topic": "World Cultures and Trade",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "Which food items were introduced to India as a result of Columbus's voyages?",
        "choices": [
            "Black pepper and cinnamon",
            "Chilli and potato",
            "Rice and wheat",
            "Cardamom and cloves",
        ],
        "accepted_answers": ["chilli and potato", "chilli", "potato"],
    },
    {
        "id": "eng-spice-pepper-origin",
        "lesson_id": "english-visitor-distant-lands",
        "subject_id": "english",
        "topic": "World Cultures and Trade",
        "difficulty": "hard",
        "rating": 1100,
        "prompt": "Black pepper originally came from which region of India?",
        "choices": ["Punjab", "Kerala", "Rajasthan", "Bengal"],
        "accepted_answers": ["kerala"],
    },
)


# ─────────────────────────────────────────────────────────────────────────────
# MATHEMATICS  (6 lessons · Chapters 1–6)
# ─────────────────────────────────────────────────────────────────────────────

MATHEMATICS_LESSONS: tuple[LessonSeed, ...] = (
    {
        "id": "maths-numbers",
        "subject_id": "mathematics",
        "subject_name": "Mathematics",
        "topic": "Numbers",
        "title": "Large Numbers and Place Value",
        "content": {
            "summary": (
                "Numbers can be made very large. The Indian system uses lakhs and crores, "
                "while the International system uses millions and billions. Place value tells us "
                "the worth of each digit based on its position."
            ),
            "key_points": [
                "In the Indian system: 1 lakh = 1,00,000 and 1 crore = 1,00,00,000.",
                "In the International system: 1 million = 1,000,000 and 1 billion = 1,000,000,000.",
                "The order of operations (BIDMAS): Brackets, Indices, Division, Multiplication, "
                "Addition, Subtraction.",
                "Estimation means rounding numbers to the nearest ten, hundred, or thousand.",
                "Whole numbers start from 0 and go on forever: 0, 1, 2, 3, …",
            ],
            "vocabulary": {
                "place value": "The value of a digit based on its position in a number.",
                "lakh": "1,00,000 in the Indian number system.",
                "crore": "1,00,00,000 in the Indian number system.",
                "estimation": "Finding a value close to the exact answer by rounding.",
                "BIDMAS": "Order of operations: Brackets, Indices, Division, Multiplication, Addition, Subtraction.",
            },
            "try_it": (
                "Write the number 45,67,890 in words using the Indian system. "
                "Then write it in the International system."
            ),
            "quiz_ready_facts": [
                "1 lakh = 1,00,000",
                "1 crore = 1,00,00,000",
                "BIDMAS defines the correct order of mathematical operations.",
            ],
        },
    },
    {
        "id": "maths-algebra",
        "subject_id": "mathematics",
        "subject_name": "Mathematics",
        "topic": "Introduction to Algebra",
        "title": "Patterns, Variables, and Algebraic Expressions",
        "content": {
            "summary": (
                "Algebra uses letters to represent unknown or changing quantities. "
                "Patterns in numbers can be described using algebraic expressions. "
                "Solving for an unknown means finding the value of the letter."
            ),
            "key_points": [
                "A variable is a letter (like x, y, or n) that stands for a number that can change.",
                "An algebraic expression combines variables and numbers (e.g. 2n + 3).",
                "A pattern can be described with a rule — e.g. matchstick triangles: 3n sticks for n triangles.",
                "To frame an algebraic statement, translate words into symbols: "
                "'5 more than a number' → x + 5.",
                "To solve an unknown, substitute values or use the balance method.",
            ],
            "vocabulary": {
                "variable": "A letter used to represent an unknown or changing quantity.",
                "expression": "A combination of numbers, variables, and operations (no equals sign).",
                "equation": "A mathematical statement that two expressions are equal.",
                "pattern": "A sequence that follows a predictable rule.",
                "substitute": "To replace a variable with a specific number to find the value.",
            },
            "try_it": (
                "A square is made of 4 matchsticks. Write an expression for the number of "
                "matchsticks needed to make n squares arranged in a row."
            ),
            "quiz_ready_facts": [
                "A variable represents an unknown or changing quantity.",
                "2n + 3 is an example of an algebraic expression.",
                "To solve an equation, find the value of the variable that makes it true.",
            ],
        },
    },
    {
        "id": "maths-ratio-proportion",
        "subject_id": "mathematics",
        "subject_name": "Mathematics",
        "topic": "Ratio and Proportion",
        "title": "Ratio, Proportion, and Unitary Method",
        "content": {
            "summary": (
                "A ratio compares two quantities of the same kind by division. "
                "Proportion means two ratios are equal. "
                "The unitary method finds the value of many by first finding the value of one."
            ),
            "key_points": [
                "A ratio a:b compares quantity a to quantity b; both must be in the same units.",
                "To simplify a ratio, divide both terms by their HCF.",
                "Two ratios are in proportion if a:b = c:d, meaning a × d = b × c (cross-multiplication).",
                "In the unitary method: find the value of 1 unit first, then multiply.",
                "Example: If 5 pens cost ₹35, then 1 pen costs ₹7, so 8 pens cost ₹56.",
            ],
            "vocabulary": {
                "ratio": "A comparison of two quantities by division, written as a:b.",
                "proportion": "An equation stating that two ratios are equal.",
                "HCF": "Highest Common Factor — the largest number that divides two numbers exactly.",
                "unitary method": "Finding the value of many units by first finding the value of one.",
                "equivalent ratios": "Ratios that have the same value when simplified.",
            },
            "try_it": (
                "A recipe needs 2 cups of flour for every 3 cups of water. "
                "How many cups of water are needed for 8 cups of flour? Use the unitary method."
            ),
            "quiz_ready_facts": [
                "In a proportion a:b = c:d, the product of extremes equals the product of means (a×d = b×c).",
                "A ratio must compare quantities of the same kind and unit.",
                "To simplify 12:18, divide both by HCF (6) to get 2:3.",
            ],
        },
    },
    {
        "id": "maths-geometry",
        "subject_id": "mathematics",
        "subject_name": "Mathematics",
        "topic": "Geometry",
        "title": "Lines, Angles, and Points",
        "content": {
            "summary": (
                "Geometry studies shapes, sizes, and properties of figures and spaces. "
                "A point marks a location. Lines extend in both directions forever. "
                "Angles are formed when two rays share an endpoint."
            ),
            "key_points": [
                "A point has no size — it marks an exact location.",
                "A line extends infinitely in both directions; a line segment has two endpoints; "
                "a ray has one endpoint and extends in one direction.",
                "Parallel lines never meet; perpendicular lines meet at exactly 90°.",
                "Types of angles: Acute (<90°), Right (=90°), Obtuse (>90° and <180°), "
                "Straight (=180°), Reflex (>180°).",
                "A protractor is used to measure angles in degrees.",
            ],
            "vocabulary": {
                "point": "An exact location in space with no size.",
                "line segment": "A part of a line with two definite endpoints.",
                "ray": "A part of a line with one endpoint that extends infinitely in one direction.",
                "perpendicular": "Two lines that meet at a right angle (90°).",
                "acute angle": "An angle that measures less than 90°.",
                "obtuse angle": "An angle greater than 90° but less than 180°.",
            },
            "try_it": (
                "Draw a pair of parallel lines and a transversal crossing them. "
                "Use a protractor to measure all angles formed and note which angles are equal."
            ),
            "quiz_ready_facts": [
                "A right angle measures exactly 90°.",
                "Parallel lines never intersect, no matter how far they extend.",
                "A reflex angle is greater than 180° and less than 360°.",
            ],
        },
    },
    {
        "id": "maths-statistics",
        "subject_id": "mathematics",
        "subject_name": "Mathematics",
        "topic": "Statistics",
        "title": "Data Collection and Representation",
        "content": {
            "summary": (
                "Statistics is the study of collecting, organising, and interpreting data. "
                "Tally marks, pictographs, and bar graphs are common ways to display data clearly."
            ),
            "key_points": [
                "Data is a collection of facts or numbers gathered for analysis.",
                "Tally marks are grouped in fives to make counting easier (four vertical lines crossed by one diagonal).",
                "A pictograph uses pictures or symbols to represent data; each symbol stands for a fixed number.",
                "A bar graph uses rectangular bars of different heights to show quantities.",
                "When drawing a bar graph, choose a suitable scale so all data fits neatly on the graph.",
            ],
            "vocabulary": {
                "data": "A collection of facts, numbers, or information.",
                "tally": "A mark used to count; four vertical marks crossed by one diagonal represents 5.",
                "frequency": "How often a particular value occurs in a data set.",
                "pictograph": "A graph that uses pictures or symbols to represent data.",
                "bar graph": "A graph that uses rectangular bars to show and compare quantities.",
            },
            "try_it": (
                "Survey 10 classmates about their favourite subject. "
                "Record the results in a tally table, then draw a bar graph to display the data."
            ),
            "quiz_ready_facts": [
                "In a pictograph, one symbol can represent more than one item (called a key).",
                "The height of a bar in a bar graph shows the quantity or frequency.",
                "Data must be organised before it can be displayed or interpreted accurately.",
            ],
        },
    },
    {
        "id": "maths-information-processing",
        "subject_id": "mathematics",
        "subject_name": "Mathematics",
        "topic": "Information Processing",
        "title": "Systematic Listing and Combinations",
        "content": {
            "summary": (
                "Information processing is about organising possibilities in a systematic way "
                "so nothing is missed or repeated. Tree diagrams and ordered lists help count "
                "all possible outcomes."
            ),
            "key_points": [
                "Systematic listing means writing all possibilities in an organised order.",
                "A tree diagram shows all possible combinations by branching at each choice.",
                "When choosing 2 items from a set, list all pairs without repeating any combination.",
                "Organised lists ensure all outcomes are counted exactly once — no omissions, no duplicates.",
                "Example: Outfits from 2 shirts and 3 trousers → 2 × 3 = 6 possible combinations.",
            ],
            "vocabulary": {
                "systematic": "Following a fixed, organised plan or method.",
                "combination": "A selection of items where order does not matter.",
                "tree diagram": "A diagram that shows all possible outcomes by branching at each stage.",
                "outcome": "A possible result of a situation or experiment.",
                "listing": "Writing out all possibilities in an organised sequence.",
            },
            "try_it": (
                "You have 3 different caps (red, blue, green) and 2 scarves (striped, plain). "
                "Draw a tree diagram showing all possible cap-and-scarf combinations."
            ),
            "quiz_ready_facts": [
                "A tree diagram branches at each decision point to show all outcomes.",
                "Systematic listing avoids repeating or missing any possible combination.",
                "If you have m choices for one item and n choices for another, total combinations = m × n.",
            ],
        },
    },
)

MATHEMATICS_QUESTIONS: tuple[QuestionSeed, ...] = (
    # Numbers
    {
        "id": "maths-numbers-lakh",
        "lesson_id": "maths-numbers",
        "subject_id": "mathematics",
        "topic": "Numbers",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "How many zeros are in 1 lakh in the Indian number system?",
        "choices": ["4", "5", "6", "7"],
        "accepted_answers": ["5"],
    },
    {
        "id": "maths-numbers-bidmas",
        "lesson_id": "maths-numbers",
        "subject_id": "mathematics",
        "topic": "Numbers",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "Using BIDMAS, what is the value of 3 + 4 × 2?",
        "choices": ["14", "11", "10", "16"],
        "accepted_answers": ["11"],
    },
    {
        "id": "maths-numbers-crore",
        "lesson_id": "maths-numbers",
        "subject_id": "mathematics",
        "topic": "Numbers",
        "difficulty": "hard",
        "rating": 1100,
        "prompt": "How is 1 crore written in the International number system?",
        "choices": ["1 million", "10 million", "1 billion", "100 thousand"],
        "accepted_answers": ["10 million"],
    },
    # Algebra
    {
        "id": "maths-algebra-variable",
        "lesson_id": "maths-algebra",
        "subject_id": "mathematics",
        "topic": "Introduction to Algebra",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "In algebra, what does a variable represent?",
        "choices": [
            "A fixed known number",
            "An unknown or changing quantity",
            "The result of an equation",
            "A type of graph",
        ],
        "accepted_answers": ["an unknown or changing quantity", "unknown or changing quantity"],
    },
    {
        "id": "maths-algebra-expression",
        "lesson_id": "maths-algebra",
        "subject_id": "mathematics",
        "topic": "Introduction to Algebra",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "Which of these is an algebraic expression for '5 more than a number n'?",
        "choices": ["5n", "n − 5", "n + 5", "5 ÷ n"],
        "accepted_answers": ["n + 5"],
    },
    {
        "id": "maths-algebra-matchstick",
        "lesson_id": "maths-algebra",
        "subject_id": "mathematics",
        "topic": "Introduction to Algebra",
        "difficulty": "hard",
        "rating": 1100,
        "prompt": "Each square needs 4 matchsticks. How many matchsticks are needed for n squares in a row?",
        "choices": ["4n", "3n + 1", "4n − 1", "n + 4"],
        "accepted_answers": ["3n + 1"],
    },
    # Ratio and Proportion
    {
        "id": "maths-ratio-simplify",
        "lesson_id": "maths-ratio-proportion",
        "subject_id": "mathematics",
        "topic": "Ratio and Proportion",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "What is the simplest form of the ratio 12:18?",
        "choices": ["6:9", "2:3", "4:6", "3:2"],
        "accepted_answers": ["2:3"],
    },
    {
        "id": "maths-ratio-proportion-check",
        "lesson_id": "maths-ratio-proportion",
        "subject_id": "mathematics",
        "topic": "Ratio and Proportion",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "Are 3:4 and 9:12 in proportion?",
        "choices": [
            "Yes, because 3 × 12 = 4 × 9",
            "No, because 3 + 4 ≠ 9 + 12",
            "Yes, because 3 + 12 = 4 + 9",
            "No, because 3 × 9 ≠ 4 × 12",
        ],
        "accepted_answers": ["yes, because 3 × 12 = 4 × 9", "yes"],
    },
    {
        "id": "maths-unitary-method",
        "lesson_id": "maths-ratio-proportion",
        "subject_id": "mathematics",
        "topic": "Ratio and Proportion",
        "difficulty": "hard",
        "rating": 1100,
        "prompt": "If 6 notebooks cost ₹90, what is the cost of 10 notebooks?",
        "choices": ["₹120", "₹150", "₹180", "₹100"],
        "accepted_answers": ["₹150", "150"],
    },
    # Geometry
    {
        "id": "maths-geometry-right-angle",
        "lesson_id": "maths-geometry",
        "subject_id": "mathematics",
        "topic": "Geometry",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "How many degrees does a right angle measure?",
        "choices": ["45°", "90°", "180°", "360°"],
        "accepted_answers": ["90°", "90"],
    },
    {
        "id": "maths-geometry-angle-type",
        "lesson_id": "maths-geometry",
        "subject_id": "mathematics",
        "topic": "Geometry",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "An angle that measures 135° is called a what?",
        "choices": ["Acute angle", "Right angle", "Obtuse angle", "Reflex angle"],
        "accepted_answers": ["obtuse angle", "obtuse"],
    },
    {
        "id": "maths-geometry-parallel",
        "lesson_id": "maths-geometry",
        "subject_id": "mathematics",
        "topic": "Geometry",
        "difficulty": "hard",
        "rating": 1100,
        "prompt": "Which statement correctly describes parallel lines?",
        "choices": [
            "They meet at one point",
            "They are always perpendicular",
            "They never meet, no matter how far they extend",
            "They form a right angle when they cross",
        ],
        "accepted_answers": ["they never meet, no matter how far they extend", "they never meet"],
    },
    # Statistics
    {
        "id": "maths-stats-tally",
        "lesson_id": "maths-statistics",
        "subject_id": "mathematics",
        "topic": "Statistics",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "In tally marks, how many marks make a group of five?",
        "choices": ["Four vertical lines", "Five vertical lines", "Four lines with one diagonal", "Five dots"],
        "accepted_answers": ["four lines with one diagonal", "four vertical lines crossed by one diagonal"],
    },
    {
        "id": "maths-stats-pictograph",
        "lesson_id": "maths-statistics",
        "subject_id": "mathematics",
        "topic": "Statistics",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "In a pictograph, one apple symbol represents 5 fruits. How many apples represent 25 fruits?",
        "choices": ["3", "4", "5", "6"],
        "accepted_answers": ["5"],
    },
    {
        "id": "maths-stats-bar-graph",
        "lesson_id": "maths-statistics",
        "subject_id": "mathematics",
        "topic": "Statistics",
        "difficulty": "hard",
        "rating": 1100,
        "prompt": "In a bar graph, what does the height of each bar represent?",
        "choices": [
            "The category name",
            "The frequency or quantity for that category",
            "The total of all data",
            "The number of bars in the graph",
        ],
        "accepted_answers": ["the frequency or quantity for that category", "frequency", "quantity"],
    },
    # Information Processing
    {
        "id": "maths-ip-tree-diagram",
        "lesson_id": "maths-information-processing",
        "subject_id": "mathematics",
        "topic": "Information Processing",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "What is the purpose of a tree diagram in information processing?",
        "choices": [
            "To draw pictures of trees",
            "To show all possible outcomes systematically",
            "To find the highest common factor",
            "To measure angles",
        ],
        "accepted_answers": ["to show all possible outcomes systematically", "show all possible outcomes"],
    },
    {
        "id": "maths-ip-combinations",
        "lesson_id": "maths-information-processing",
        "subject_id": "mathematics",
        "topic": "Information Processing",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "You have 3 shirts and 2 trousers. How many different outfits can you make?",
        "choices": ["5", "6", "8", "3"],
        "accepted_answers": ["6"],
    },
    {
        "id": "maths-ip-systematic",
        "lesson_id": "maths-information-processing",
        "subject_id": "mathematics",
        "topic": "Information Processing",
        "difficulty": "hard",
        "rating": 1100,
        "prompt": "Why is systematic listing important when counting combinations?",
        "choices": [
            "It makes the list look neat",
            "It ensures no outcome is missed or repeated",
            "It is faster than any other method",
            "It requires fewer calculations",
        ],
        "accepted_answers": ["it ensures no outcome is missed or repeated", "no outcome is missed or repeated"],
    },
)


# ─────────────────────────────────────────────────────────────────────────────
# SCIENCE  (7 lessons — Unit 1 kept + original matter-basics preserved)
# ─────────────────────────────────────────────────────────────────────────────

SCIENCE_LESSONS: tuple[LessonSeed, ...] = (
    # Original demo lesson — preserved exactly
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
    {
        "id": "science-measurements",
        "subject_id": "science",
        "subject_name": "Science",
        "topic": "Measurements",
        "title": "Measurements",
        "content": {
            "summary": (
                "Measurement is the comparison of an unknown quantity with a known standard. "
                "Scientists use the International System of Units (SI units) to ensure "
                "measurements are consistent worldwide."
            ),
            "key_points": [
                "The SI unit of length is the metre (m), mass is kilogram (kg), and time is second (s).",
                "Common prefixes: kilo (1000×), centi (1/100), milli (1/1000).",
                "Parallax error occurs when the eye is not directly above the measurement point on a scale.",
                "Zero error occurs when a measuring instrument shows a reading other than zero when measuring nothing.",
                "A beam balance measures mass; a measuring cylinder measures volume of liquids.",
            ],
            "vocabulary": {
                "SI unit": "International System of Units — the global standard for measurement.",
                "metre": "The SI unit of length.",
                "kilogram": "The SI unit of mass.",
                "parallax error": "An error caused by viewing a scale from an angle instead of directly above.",
                "zero error": "An error when an instrument reads a value other than zero when at rest.",
            },
            "try_it": (
                "Use a ruler to measure the length and width of your textbook in centimetres. "
                "Convert your measurements to millimetres and then to metres."
            ),
            "quiz_ready_facts": [
                "1 kilometre = 1000 metres.",
                "1 centimetre = 10 millimetres.",
                "Parallax error is avoided by keeping the eye directly above the scale marking.",
            ],
        },
    },
    {
        "id": "science-force-motion",
        "subject_id": "science",
        "subject_name": "Science",
        "topic": "Force and Motion",
        "title": "Force and Motion",
        "content": {
            "summary": (
                "A force is a push or pull that can cause an object to move, stop, change direction, "
                "or change shape. Motion is a change in position of an object over time."
            ),
            "key_points": [
                "Contact forces require physical touch: friction, muscular force, spring force.",
                "Non-contact forces act at a distance: gravitational force, magnetic force, electrostatic force.",
                "Types of motion: linear (straight line), circular, oscillatory (back and forth), rotatory (spinning).",
                "Speed = Distance ÷ Time. The SI unit of speed is metres per second (m/s).",
                "Uniform motion: equal distances in equal time intervals. Non-uniform: unequal distances.",
            ],
            "vocabulary": {
                "force": "A push or pull acting on an object.",
                "friction": "A contact force that opposes the motion of surfaces sliding against each other.",
                "gravity": "A non-contact force that attracts objects towards the centre of the Earth.",
                "speed": "The distance covered by an object per unit of time.",
                "oscillatory motion": "Motion that repeats back and forth around a fixed point, like a pendulum.",
            },
            "try_it": (
                "Push a book across a table. Observe it slowing down. "
                "What force caused it to slow down? How could you reduce that force?"
            ),
            "quiz_ready_facts": [
                "Gravity is a non-contact force that pulls objects towards Earth.",
                "Speed = Distance ÷ Time.",
                "A pendulum swinging is an example of oscillatory motion.",
            ],
        },
    },
    {
        "id": "science-world-of-plants",
        "subject_id": "science",
        "subject_name": "Science",
        "topic": "World of Plants",
        "title": "The World of Plants",
        "content": {
            "summary": (
                "Plants have two main systems: the root system below the ground and the shoot system "
                "above. Leaves carry out photosynthesis, making food from sunlight, water, and carbon dioxide."
            ),
            "key_points": [
                "Tap root systems have one main root with smaller branches (e.g. carrot, mango).",
                "Fibrous root systems have many thin roots of similar size spreading from the stem (e.g. grass, paddy).",
                "Leaves have a petiole (stalk), lamina (blade), and veins that carry water and food.",
                "Photosynthesis: 6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂ (glucose and oxygen produced).",
                "Stomata are tiny pores on leaves that allow gas exchange and transpiration (water loss).",
            ],
            "vocabulary": {
                "tap root": "A main central root from which smaller roots branch out.",
                "fibrous root": "A system of many thin roots of equal size with no main root.",
                "photosynthesis": "The process by which green plants make food using sunlight, water, and carbon dioxide.",
                "stomata": "Tiny pores on leaves through which gases and water vapour pass.",
                "transpiration": "The process of water evaporating from plant leaves through the stomata.",
            },
            "try_it": (
                "Carefully uproot two different plants — one with a tap root and one with fibrous roots. "
                "Draw both root systems and label the differences."
            ),
            "quiz_ready_facts": [
                "Grass has a fibrous root system; carrots have a tap root system.",
                "Photosynthesis produces glucose and oxygen.",
                "Stomata open during the day to allow gas exchange for photosynthesis.",
            ],
        },
    },
    {
        "id": "science-world-of-animals",
        "subject_id": "science",
        "subject_name": "Science",
        "topic": "World of Animals",
        "title": "The World of Animals",
        "content": {
            "summary": (
                "Animals are diverse — from single-celled organisms like Amoeba to complex multicellular "
                "animals. Each animal has adaptations that help it survive in its specific habitat."
            ),
            "key_points": [
                "Unicellular organisms have just one cell: Amoeba (pseudopodia), Paramecium (cilia), Euglena (flagellum).",
                "Fish are adapted for aquatic life: streamlined body, gills for dissolved oxygen, fins, swim bladder.",
                "Frogs are amphibians — they breathe through skin in water and through lungs on land.",
                "Birds have hollow (pneumatic) bones that reduce body weight for flight.",
                "Camels store fat in their humps (not water), have wide padded feet for sand, and long eyelashes to block sand.",
            ],
            "vocabulary": {
                "adaptation": "A feature of an organism that helps it survive in its environment.",
                "unicellular": "Made of only one cell.",
                "amphibian": "An animal that can live both on land and in water.",
                "pneumatic bones": "Hollow, air-filled bones found in birds that reduce weight for flight.",
                "pseudopodia": "Temporary arm-like extensions of an amoeba used for movement and feeding.",
            },
            "try_it": (
                "Choose one animal from your neighbourhood. "
                "List three ways its body is adapted to survive in its environment."
            ),
            "quiz_ready_facts": [
                "A camel's hump stores fat, not water.",
                "Birds have hollow bones to reduce weight for flight.",
                "Amoeba moves using pseudopodia — temporary extensions of its cell.",
            ],
        },
    },
    {
        "id": "science-health-hygiene",
        "subject_id": "science",
        "subject_name": "Science",
        "topic": "Health and Hygiene",
        "title": "Health and Hygiene",
        "content": {
            "summary": (
                "Good health depends on balanced nutrition, personal hygiene, and preventing disease. "
                "Nutrients in food provide energy, build the body, and protect against illness."
            ),
            "key_points": [
                "Carbohydrates (rice, bread) provide energy; fats (oil, butter) are the body's energy bank.",
                "Proteins (dal, eggs, meat) build and repair body tissues.",
                "Vitamins and minerals are protective foods — deficiencies cause specific diseases.",
                "Vitamin C deficiency → Scurvy; Vitamin D → Rickets; Iodine deficiency → Goitre; Iron → Anaemia.",
                "Communicable diseases spread from person to person (cholera, tuberculosis, common cold); "
                "non-communicable diseases do not (diabetes, asthma).",
            ],
            "vocabulary": {
                "nutrient": "A substance in food that the body needs to grow and stay healthy.",
                "deficiency": "A lack of a necessary nutrient or substance in the body.",
                "communicable disease": "A disease that can spread from one person to another.",
                "hygiene": "Practices that keep the body clean and prevent illness.",
                "Scurvy": "A disease caused by Vitamin C deficiency, causing bleeding gums and weakness.",
            },
            "try_it": (
                "Plan a healthy meal for one day — breakfast, lunch, and dinner. "
                "List the nutrients provided by each food item in your meal."
            ),
            "quiz_ready_facts": [
                "Vitamin C deficiency causes Scurvy.",
                "Vitamin D deficiency causes Rickets.",
                "Carbohydrates are the primary source of energy for the body.",
            ],
        },
    },
    {
        "id": "science-computer-intro",
        "subject_id": "science",
        "subject_name": "Science",
        "topic": "Computer Science",
        "title": "Computer — An Introduction",
        "content": {
            "summary": (
                "A computer is an electronic device that processes data and gives useful output. "
                "Computers have evolved through five generations and consist of hardware and software."
            ),
            "key_points": [
                "Charles Babbage is called the Father of the Computer; Lady Ada Lovelace was the first programmer; "
                "Alan Turing is the Father of Computer Science.",
                "Five generations: 1st (vacuum tubes), 2nd (transistors), 3rd (integrated circuits), "
                "4th (microprocessors), 5th (artificial intelligence).",
                "Hardware: physical parts — Input (keyboard, mouse, microphone), CPU, Output (monitor, printer).",
                "CPU has three parts: ALU (Arithmetic and Logic Unit), CU (Control Unit), MU (Memory Unit).",
                "Software: programs and instructions — System software (operating system) and Application software.",
            ],
            "vocabulary": {
                "hardware": "The physical, tangible parts of a computer that you can touch.",
                "software": "Programs and instructions that tell the computer what to do.",
                "CPU": "Central Processing Unit — the 'brain' of the computer that processes instructions.",
                "ALU": "Arithmetic and Logic Unit — performs calculations and logical decisions.",
                "operating system": "System software that manages all hardware and other software (e.g. Windows, macOS).",
            },
            "try_it": (
                "List five input devices and five output devices you can find in a school computer lab. "
                "For each, explain what type of data it inputs or outputs."
            ),
            "quiz_ready_facts": [
                "Charles Babbage is called the Father of the Computer.",
                "The CPU consists of the ALU, Control Unit, and Memory Unit.",
                "The first generation of computers used vacuum tubes.",
            ],
        },
    },
)

SCIENCE_QUESTIONS: tuple[QuestionSeed, ...] = (
    # Original demo questions — preserved exactly
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
    # Measurements
    {
        "id": "sci-measure-si-length",
        "lesson_id": "science-measurements",
        "subject_id": "science",
        "topic": "Measurements",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "What is the SI unit of length?",
        "choices": ["Centimetre", "Kilometre", "Metre", "Foot"],
        "accepted_answers": ["metre", "meter"],
    },
    {
        "id": "sci-measure-prefix-kilo",
        "lesson_id": "science-measurements",
        "subject_id": "science",
        "topic": "Measurements",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "How many metres are in 1 kilometre?",
        "choices": ["10", "100", "1000", "10000"],
        "accepted_answers": ["1000"],
    },
    {
        "id": "sci-measure-parallax",
        "lesson_id": "science-measurements",
        "subject_id": "science",
        "topic": "Measurements",
        "difficulty": "hard",
        "rating": 1100,
        "prompt": "How is parallax error avoided when using a ruler?",
        "choices": [
            "By using a longer ruler",
            "By keeping the eye directly above the measurement point",
            "By measuring in millimetres only",
            "By using a digital scale instead",
        ],
        "accepted_answers": ["by keeping the eye directly above the measurement point", "eye directly above"],
    },
    # Force and Motion
    {
        "id": "sci-force-gravity",
        "lesson_id": "science-force-motion",
        "subject_id": "science",
        "topic": "Force and Motion",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "Which of these is a non-contact force?",
        "choices": ["Friction", "Muscular force", "Gravity", "Spring force"],
        "accepted_answers": ["gravity"],
    },
    {
        "id": "sci-force-speed-formula",
        "lesson_id": "science-force-motion",
        "subject_id": "science",
        "topic": "Force and Motion",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "A car travels 150 km in 3 hours. What is its speed?",
        "choices": ["30 km/h", "50 km/h", "75 km/h", "450 km/h"],
        "accepted_answers": ["50 km/h", "50"],
    },
    {
        "id": "sci-force-oscillatory",
        "lesson_id": "science-force-motion",
        "subject_id": "science",
        "topic": "Force and Motion",
        "difficulty": "hard",
        "rating": 1100,
        "prompt": "Which of the following is an example of oscillatory motion?",
        "choices": ["A ball rolling on the floor", "A pendulum swinging", "A car driving straight", "Earth rotating"],
        "accepted_answers": ["a pendulum swinging", "pendulum swinging"],
    },
    # World of Plants
    {
        "id": "sci-plants-tap-root",
        "lesson_id": "science-world-of-plants",
        "subject_id": "science",
        "topic": "World of Plants",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "Which plant has a tap root system?",
        "choices": ["Grass", "Wheat", "Carrot", "Paddy"],
        "accepted_answers": ["carrot"],
    },
    {
        "id": "sci-plants-photosynthesis",
        "lesson_id": "science-world-of-plants",
        "subject_id": "science",
        "topic": "World of Plants",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "What are the two products of photosynthesis?",
        "choices": [
            "Carbon dioxide and water",
            "Glucose and oxygen",
            "Nitrogen and glucose",
            "Oxygen and carbon dioxide",
        ],
        "accepted_answers": ["glucose and oxygen"],
    },
    {
        "id": "sci-plants-stomata",
        "lesson_id": "science-world-of-plants",
        "subject_id": "science",
        "topic": "World of Plants",
        "difficulty": "hard",
        "rating": 1100,
        "prompt": "What is the role of stomata in a leaf?",
        "choices": [
            "Absorbing water from soil",
            "Producing chlorophyll",
            "Allowing gas exchange and transpiration",
            "Converting sunlight to electricity",
        ],
        "accepted_answers": ["allowing gas exchange and transpiration", "gas exchange and transpiration"],
    },
    # World of Animals
    {
        "id": "sci-animals-camel-hump",
        "lesson_id": "science-world-of-animals",
        "subject_id": "science",
        "topic": "World of Animals",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "What does a camel store in its hump?",
        "choices": ["Water", "Salt", "Fat", "Air"],
        "accepted_answers": ["fat"],
    },
    {
        "id": "sci-animals-bird-bones",
        "lesson_id": "science-world-of-animals",
        "subject_id": "science",
        "topic": "World of Animals",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "Why do birds have hollow bones?",
        "choices": [
            "To store water for long flights",
            "To reduce body weight for flight",
            "To make them swim better",
            "To protect them from predators",
        ],
        "accepted_answers": ["to reduce body weight for flight", "reduce body weight", "reduce weight for flight"],
    },
    {
        "id": "sci-animals-amoeba",
        "lesson_id": "science-world-of-animals",
        "subject_id": "science",
        "topic": "World of Animals",
        "difficulty": "hard",
        "rating": 1100,
        "prompt": "How does an Amoeba move from place to place?",
        "choices": [
            "Using cilia",
            "Using flagella",
            "Using pseudopodia",
            "By jumping",
        ],
        "accepted_answers": ["using pseudopodia", "pseudopodia"],
    },
    # Health and Hygiene
    {
        "id": "sci-health-scurvy",
        "lesson_id": "science-health-hygiene",
        "subject_id": "science",
        "topic": "Health and Hygiene",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "Which vitamin deficiency causes Scurvy?",
        "choices": ["Vitamin A", "Vitamin B", "Vitamin C", "Vitamin D"],
        "accepted_answers": ["vitamin c"],
    },
    {
        "id": "sci-health-protein",
        "lesson_id": "science-health-hygiene",
        "subject_id": "science",
        "topic": "Health and Hygiene",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "What is the primary function of proteins in the body?",
        "choices": ["Provide energy", "Build and repair body tissues", "Regulate temperature", "Store fat"],
        "accepted_answers": ["build and repair body tissues", "build and repair tissues", "body building"],
    },
    {
        "id": "sci-health-communicable",
        "lesson_id": "science-health-hygiene",
        "subject_id": "science",
        "topic": "Health and Hygiene",
        "difficulty": "hard",
        "rating": 1100,
        "prompt": "Which of these is a communicable disease?",
        "choices": ["Diabetes", "Asthma", "Cholera", "Arthritis"],
        "accepted_answers": ["cholera"],
    },
    # Computer
    {
        "id": "sci-computer-father",
        "lesson_id": "science-computer-intro",
        "subject_id": "science",
        "topic": "Computer Science",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "Who is called the Father of the Computer?",
        "choices": ["Alan Turing", "Charles Babbage", "Ada Lovelace", "Bill Gates"],
        "accepted_answers": ["charles babbage"],
    },
    {
        "id": "sci-computer-cpu-parts",
        "lesson_id": "science-computer-intro",
        "subject_id": "science",
        "topic": "Computer Science",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "Which of these is NOT a part of the CPU?",
        "choices": ["ALU", "Control Unit", "Monitor", "Memory Unit"],
        "accepted_answers": ["monitor"],
    },
    {
        "id": "sci-computer-gen1",
        "lesson_id": "science-computer-intro",
        "subject_id": "science",
        "topic": "Computer Science",
        "difficulty": "hard",
        "rating": 1100,
        "prompt": "Which technology was used in first generation computers?",
        "choices": ["Transistors", "Integrated Circuits", "Vacuum Tubes", "Microprocessors"],
        "accepted_answers": ["vacuum tubes"],
    },
)


# ─────────────────────────────────────────────────────────────────────────────
# SOCIAL SCIENCE  (8 lessons — History × 4, Geography × 2, Civics × 2)
# ─────────────────────────────────────────────────────────────────────────────

SOCIAL_SCIENCE_LESSONS: tuple[LessonSeed, ...] = (
    {
        "id": "social-what-is-history",
        "subject_id": "social_science",
        "subject_name": "Social Science",
        "topic": "History",
        "title": "What is History?",
        "content": {
            "summary": (
                "History is the study of the past based on evidence. The word 'history' comes from "
                "the Greek word 'Historia', meaning learning by inquiry. Historians use sources like "
                "inscriptions, coins, monuments, and written records."
            ),
            "key_points": [
                "The word 'History' comes from the Greek word 'Historia', meaning 'learning by enquiry'.",
                "Archaeological sources: coins, inscriptions, sculptures, monuments, pottery, tools.",
                "Literary sources: epics (Ramayana, Mahabharata), Vedas, and foreign travelogues.",
                "Pre-history refers to the period before writing was invented; evidence comes from stone tools "
                "and cave paintings (e.g. Bhimbetka rock shelters in Madhya Pradesh).",
                "Emperor Ashoka's Dharma Chakra (with 24 spokes) appears on India's national flag after the "
                "Kalinga war changed his life towards peace.",
            ],
            "vocabulary": {
                "history": "The study of past events, particularly in human affairs.",
                "archaeology": "The study of human history through the excavation of sites and analysis of artefacts.",
                "inscription": "Writing carved into stone, metal, or another durable surface.",
                "artefact": "An object made and used by people in the past.",
                "Dharma Chakra": "The wheel of law; appears on India's national flag with 24 spokes.",
            },
            "try_it": (
                "Imagine you found a very old coin in your backyard. "
                "List three things you could learn about history from just examining that coin."
            ),
            "quiz_ready_facts": [
                "The word 'history' comes from the Greek word 'Historia'.",
                "Emperor Ashoka's Dharma Chakra appears on India's national flag.",
                "Pre-history refers to the time before written records were kept.",
            ],
        },
    },
    {
        "id": "social-human-evolution",
        "subject_id": "social_science",
        "subject_name": "Social Science",
        "topic": "History",
        "title": "Human Evolution",
        "content": {
            "summary": (
                "Human beings evolved over millions of years from earlier primates. "
                "Early humans were hunter-gatherers who later learned farming, "
                "which led to permanent settlements and civilization."
            ),
            "key_points": [
                "Evolution of humans: Australopithecus → Homo habilis → Homo erectus → Neanderthals → Homo sapiens (modern humans).",
                "Early humans discovered fire by striking flint stones; fire provided warmth, protection, and cooked food.",
                "The wheel was one of the most important early inventions — it transformed transport and farming.",
                "Humans transitioned from nomadic hunter-gatherers to settled farmers (Neolithic revolution).",
                "Cave paintings in Tamil Nadu (Nilgiri hills, Keezhvalai, Usilampatti) record early human life.",
            ],
            "vocabulary": {
                "evolution": "A gradual process of change over many generations.",
                "Homo sapiens": "The scientific name for modern humans, meaning 'wise person'.",
                "hunter-gatherer": "A person who lives by hunting animals and collecting wild plants for food.",
                "Neolithic": "The 'New Stone Age' period when humans began farming and making polished stone tools.",
                "nomadic": "Moving from place to place rather than living in a permanent settlement.",
            },
            "try_it": (
                "Draw a timeline showing the five stages of human evolution from Australopithecus "
                "to Homo sapiens. Add one key skill or tool developed at each stage."
            ),
            "quiz_ready_facts": [
                "Modern humans are called Homo sapiens, meaning 'wise person'.",
                "The discovery of fire was a major turning point in early human history.",
                "The wheel was one of the most transformative inventions of early humans.",
            ],
        },
    },
    {
        "id": "social-indus-civilisation",
        "subject_id": "social_science",
        "subject_name": "Social Science",
        "topic": "History",
        "title": "Indus Civilisation",
        "content": {
            "summary": (
                "The Indus Valley Civilisation (also called Harappan Civilisation) was one of the "
                "world's earliest urban civilisations, flourishing around 2600–1900 BCE. "
                "It was known for advanced town planning and a sophisticated drainage system."
            ),
            "key_points": [
                "Discovered in the 1920s; Sir John Marshall led early excavations at Harappa and Mohenjo-daro.",
                "Major sites: Harappa (Punjab, Pakistan) and Mohenjo-daro (Sindh, Pakistan); "
                "Lothal (Gujarat, India) had a remarkable dockyard.",
                "Town planning: grid-pattern streets, citadel on higher ground, lower town for common people, "
                "covered drainage network.",
                "Famous artefacts: the Great Bath, Bronze Dancing Girl, Priest-King statue, standardised weights.",
                "The script has not yet been deciphered; the civilisation declined around 1900 BCE.",
            ],
            "vocabulary": {
                "civilisation": "A complex human society with cities, writing, and organised government.",
                "citadel": "A fortress at the highest point of a city, used for protection and governance.",
                "grid pattern": "Streets arranged in straight lines crossing at right angles, like a grid.",
                "Great Bath": "A large public bathing tank at Mohenjo-daro, used for ritual bathing.",
                "Lothal": "An Indus Valley site in Gujarat, India, known for its ancient dockyard.",
            },
            "try_it": (
                "Compare a modern city road map with the grid pattern of Mohenjo-daro. "
                "What similarities and differences do you notice in how streets are arranged?"
            ),
            "quiz_ready_facts": [
                "Mohenjo-daro had the famous Great Bath, used for ritual purposes.",
                "Lothal in Gujarat had one of the world's earliest dockyards.",
                "The Indus Valley script has not been deciphered yet.",
            ],
        },
    },
    {
        "id": "social-ancient-tamilagam",
        "subject_id": "social_science",
        "subject_name": "Social Science",
        "topic": "History",
        "title": "Ancient Cities of Tamilagam",
        "content": {
            "summary": (
                "Tamilagam was the ancient Tamil-speaking land of South India. "
                "Three great cities — Poompuhar, Madurai, and Kanchi — were centres of trade, "
                "literature, and learning during the Sangam period."
            ),
            "key_points": [
                "Poompuhar (Kaveripoompattinam): Sangam-era port city of the Chola kings; mentioned in "
                "Silappathikaram and Manimekalai; traded with Greece and Rome.",
                "Madurai: Capital of the Pandya kingdom; centre of the Tamil Sangam (literary academy); "
                "known for pearl trade; had two markets — Naalangadi (day) and Allangadi (evening).",
                "Kanchi (Kanchipuram): City of learning and temples; visited by Chinese traveller Xuanzang; "
                "birthplace of scholars Dharmapala and Bodhidharma.",
                "Sangam literature (5th century BCE to 3rd century CE) gives us rich information about "
                "these cities and their trade, society, and rulers.",
            ],
            "vocabulary": {
                "Sangam": "An ancient Tamil literary academy; Sangam period refers to the era of this literature.",
                "Chola": "An ancient Tamil dynasty; Poompuhar was their major port city.",
                "Pandya": "An ancient Tamil dynasty; Madurai was their capital.",
                "Xuanzang": "A Chinese Buddhist monk and traveller who visited India in the 7th century CE.",
                "Kanchipuram": "Ancient city known as 'Kanchi'; a major centre of learning, silk weaving, and temples.",
            },
            "try_it": (
                "Imagine you are a trader visiting Poompuhar from Rome. "
                "Write a short diary entry describing the city, the goods you want to buy, and what you notice."
            ),
            "quiz_ready_facts": [
                "Poompuhar was the port city of the Chola kings during the Sangam period.",
                "Madurai was the capital of the Pandya kingdom and home to the Tamil Sangam.",
                "Chinese traveller Xuanzang visited Kanchi in the 7th century CE.",
            ],
        },
    },
    {
        "id": "social-universe-solar-system",
        "subject_id": "social_science",
        "subject_name": "Social Science",
        "topic": "Geography",
        "title": "The Universe and Solar System",
        "content": {
            "summary": (
                "The universe began with the Big Bang about 13.8 billion years ago. "
                "Our solar system is part of the Milky Way galaxy, with the Sun at its centre "
                "and eight planets orbiting around it."
            ),
            "key_points": [
                "The Big Bang theory: the universe began from an extremely hot, dense point 13.8 billion years ago.",
                "The Milky Way is our galaxy — it contains over 200 billion stars, including our Sun.",
                "Eight planets in order from Sun: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune.",
                "Earth's Rotation (24 hours approx.) causes Day and Night; "
                "Earth's Revolution (365.25 days) around the Sun causes the Seasons.",
                "Earth's four spheres: Lithosphere (land), Hydrosphere (water), Atmosphere (air), Biosphere (life).",
            ],
            "vocabulary": {
                "Big Bang": "The theory that the universe began from a single point of extremely high temperature and density.",
                "galaxy": "A huge collection of stars, gas, and dust held together by gravity.",
                "rotation": "Earth spinning on its own axis — causes day and night.",
                "revolution": "Earth travelling around the Sun — causes the seasons.",
                "Milky Way": "The galaxy that contains our solar system.",
            },
            "try_it": (
                "Memorise the order of the eight planets using the mnemonic: "
                "'My Very Educated Mother Just Served Us Nachos' "
                "(Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune). "
                "Write the planets from memory."
            ),
            "quiz_ready_facts": [
                "Earth rotates on its axis in approximately 24 hours, causing day and night.",
                "Earth revolves around the Sun in 365.25 days, causing the seasons.",
                "Our solar system is part of the Milky Way galaxy.",
            ],
        },
    },
    {
        "id": "social-land-oceans",
        "subject_id": "social_science",
        "subject_name": "Social Science",
        "topic": "Geography",
        "title": "Land and Oceans",
        "content": {
            "summary": (
                "Earth's surface is divided into continents (land) and oceans (water). "
                "There are 7 continents and 5 oceans. Landforms vary from mountains and plateaus "
                "to plains and valleys."
            ),
            "key_points": [
                "7 Continents (largest to smallest): Asia, Africa, North America, South America, "
                "Antarctica, Europe, Australia.",
                "5 Oceans (largest to smallest): Pacific, Atlantic, Indian, Southern, Arctic.",
                "Mountains: large, steep landforms; the Himalayas are the world's tallest mountain range.",
                "Plateau: a flat-topped highland; the Tibetan Plateau is called the 'Roof of the World'.",
                "Plains: flat, low-lying land ideal for farming; the Gangetic Plain is one of the most fertile.",
            ],
            "vocabulary": {
                "continent": "One of the seven main large landmasses on Earth.",
                "ocean": "A vast body of salt water covering most of Earth's surface.",
                "plateau": "A flat-topped elevated area of land; also called a tableland.",
                "plain": "A flat, low area of land, often fertile and good for farming.",
                "Himalaya": "The world's highest mountain range, located in Asia.",
            },
            "try_it": (
                "Draw a simple outline map of the world from memory. "
                "Label as many of the 7 continents and 5 oceans as you can."
            ),
            "quiz_ready_facts": [
                "Asia is the largest continent; Australia is the smallest.",
                "The Pacific Ocean is the world's largest ocean.",
                "The Tibetan Plateau is called the 'Roof of the World'.",
            ],
        },
    },
    {
        "id": "social-understanding-diversity",
        "subject_id": "social_science",
        "subject_name": "Social Science",
        "topic": "Civics",
        "title": "Understanding Diversity",
        "content": {
            "summary": (
                "India is one of the most diverse countries in the world — diverse in geography, "
                "language, religion, and culture. This diversity is a source of strength. "
                "Jawaharlal Nehru described India as 'Unity in Diversity'."
            ),
            "key_points": [
                "'Unity in Diversity' — a phrase coined by India's first Prime Minister Jawaharlal Nehru "
                "in his book 'Discovery of India'.",
                "India has 22 officially recognised languages in the 8th Schedule of the Constitution.",
                "Major religions in India: Hinduism, Islam, Christianity, Sikhism, Buddhism, Jainism.",
                "India's geographical diversity ranges from the Himalayas in the north to coastal beaches, "
                "deserts, and tropical forests.",
                "Cultural diversity is seen in festivals, food, clothing, music, and dance forms across states.",
            ],
            "vocabulary": {
                "diversity": "The presence of many different types of people, languages, or cultures.",
                "unity": "Being together as one, despite differences.",
                "8th Schedule": "List of 22 officially recognised languages in India's Constitution.",
                "Constitution": "The supreme law of India, which defines citizens' rights and the government's structure.",
                "Jawaharlal Nehru": "India's first Prime Minister; coined 'Unity in Diversity' for India.",
            },
            "try_it": (
                "List five different ways you can see diversity in your own school or community. "
                "Explain how each example shows that different people can live together peacefully."
            ),
            "quiz_ready_facts": [
                "India has 22 officially recognised languages in the 8th Schedule of the Constitution.",
                "'Unity in Diversity' was coined by Jawaharlal Nehru in 'Discovery of India'.",
                "India's diversity includes geographical, linguistic, religious, and cultural variety.",
            ],
        },
    },
    {
        "id": "social-achieving-equality",
        "subject_id": "social_science",
        "subject_name": "Social Science",
        "topic": "Civics",
        "title": "Achieving Equality",
        "content": {
            "summary": (
                "The Indian Constitution guarantees equality to all citizens. "
                "Despite constitutional protections, inequality and discrimination still exist in society. "
                "Dr. B.R. Ambedkar was the key architect of the Constitution and a champion of equality."
            ),
            "key_points": [
                "Article 14 of the Indian Constitution: 'The State shall not deny to any person equality "
                "before the law or the equal protection of the laws.'",
                "Article 17 abolishes untouchability in all forms.",
                "Dr. B.R. Ambedkar chaired the Constitution Drafting Committee; awarded Bharat Ratna posthumously in 1990.",
                "Discrimination based on caste, gender, religion, or disability is unconstitutional.",
                "Prejudice means holding unfair opinions without facts; stereotype means over-generalising "
                "about a group of people.",
            ],
            "vocabulary": {
                "equality": "The state of being equal in rights, status, and opportunities.",
                "discrimination": "Treating people unfairly based on characteristics like caste, gender, or religion.",
                "Constitution": "The supreme legal document of a country that defines its laws and citizens' rights.",
                "Article 14": "Constitutional provision guaranteeing equality before the law to all persons in India.",
                "untouchability": "The practice of treating certain people as inferior based on their caste; abolished by Article 17.",
            },
            "try_it": (
                "Write a short speech (5 sentences) that Dr. B.R. Ambedkar might give to your class "
                "about why equality is important for a strong nation."
            ),
            "quiz_ready_facts": [
                "Article 14 guarantees equality before the law for all people in India.",
                "Article 17 of the Constitution abolishes untouchability.",
                "Dr. B.R. Ambedkar chaired the Drafting Committee of the Indian Constitution.",
            ],
        },
    },
)

SOCIAL_SCIENCE_QUESTIONS: tuple[QuestionSeed, ...] = (
    # What is History?
    {
        "id": "soc-history-meaning",
        "lesson_id": "social-what-is-history",
        "subject_id": "social_science",
        "topic": "History",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "From which Greek word does the word 'history' come?",
        "choices": ["Historikos", "Historia", "Histos", "Histo"],
        "accepted_answers": ["historia"],
    },
    {
        "id": "soc-history-ashoka",
        "lesson_id": "social-what-is-history",
        "subject_id": "social_science",
        "topic": "History",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "How many spokes does the Dharma Chakra on India's national flag have?",
        "choices": ["12", "16", "24", "36"],
        "accepted_answers": ["24"],
    },
    {
        "id": "soc-history-sources",
        "lesson_id": "social-what-is-history",
        "subject_id": "social_science",
        "topic": "History",
        "difficulty": "hard",
        "rating": 1100,
        "prompt": "Bhimbetka rock shelters (prehistoric cave paintings) are located in which Indian state?",
        "choices": ["Tamil Nadu", "Rajasthan", "Madhya Pradesh", "Gujarat"],
        "accepted_answers": ["madhya pradesh"],
    },
    # Human Evolution
    {
        "id": "soc-evolution-homo-sapiens",
        "lesson_id": "social-human-evolution",
        "subject_id": "social_science",
        "topic": "History",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "What is the scientific name for modern human beings?",
        "choices": ["Homo habilis", "Homo erectus", "Homo sapiens", "Australopithecus"],
        "accepted_answers": ["homo sapiens"],
    },
    {
        "id": "soc-evolution-fire",
        "lesson_id": "social-human-evolution",
        "subject_id": "social_science",
        "topic": "History",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "How did early humans first produce fire?",
        "choices": [
            "By using a magnifying glass",
            "By striking flint stones together",
            "By rubbing plastic sticks",
            "By boiling water",
        ],
        "accepted_answers": ["by striking flint stones together", "striking flint stones"],
    },
    {
        "id": "soc-evolution-neolithic",
        "lesson_id": "social-human-evolution",
        "subject_id": "social_science",
        "topic": "History",
        "difficulty": "hard",
        "rating": 1100,
        "prompt": "What major change in lifestyle marks the beginning of the Neolithic period?",
        "choices": [
            "Using iron tools",
            "Learning to write",
            "Transitioning from hunter-gathering to settled farming",
            "Building the first cities",
        ],
        "accepted_answers": [
            "transitioning from hunter-gathering to settled farming",
            "settled farming",
            "farming",
        ],
    },
    # Indus Civilisation
    {
        "id": "soc-indus-great-bath",
        "lesson_id": "social-indus-civilisation",
        "subject_id": "social_science",
        "topic": "History",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "At which Indus Valley site was the famous Great Bath discovered?",
        "choices": ["Harappa", "Lothal", "Mohenjo-daro", "Dholavira"],
        "accepted_answers": ["mohenjo-daro", "mohenjo daro"],
    },
    {
        "id": "soc-indus-lothal",
        "lesson_id": "social-indus-civilisation",
        "subject_id": "social_science",
        "topic": "History",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "Which Indus Valley site in India is famous for its ancient dockyard?",
        "choices": ["Harappa", "Mohenjo-daro", "Kalibangan", "Lothal"],
        "accepted_answers": ["lothal"],
    },
    {
        "id": "soc-indus-script",
        "lesson_id": "social-indus-civilisation",
        "subject_id": "social_science",
        "topic": "History",
        "difficulty": "hard",
        "rating": 1100,
        "prompt": "What is a major unsolved mystery about the Indus Valley Civilisation?",
        "choices": [
            "The location of their capital city",
            "Their Indus script has not been deciphered",
            "Who discovered their ruins",
            "The year the civilisation began",
        ],
        "accepted_answers": ["their indus script has not been deciphered", "script not deciphered"],
    },
    # Ancient Cities of Tamilagam
    {
        "id": "soc-tamilagam-chola-port",
        "lesson_id": "social-ancient-tamilagam",
        "subject_id": "social_science",
        "topic": "History",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "Which ancient city was the port city of the Chola kings during the Sangam period?",
        "choices": ["Madurai", "Kanchi", "Poompuhar", "Thanjavur"],
        "accepted_answers": ["poompuhar", "kaveripoompattinam"],
    },
    {
        "id": "soc-tamilagam-xuanzang",
        "lesson_id": "social-ancient-tamilagam",
        "subject_id": "social_science",
        "topic": "History",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "Which ancient city in Tamil Nadu was visited by the Chinese traveller Xuanzang?",
        "choices": ["Poompuhar", "Madurai", "Kanchi (Kanchipuram)", "Chennai"],
        "accepted_answers": ["kanchi", "kanchipuram", "kanchi (kanchipuram)"],
    },
    {
        "id": "soc-tamilagam-pandya",
        "lesson_id": "social-ancient-tamilagam",
        "subject_id": "social_science",
        "topic": "History",
        "difficulty": "hard",
        "rating": 1100,
        "prompt": "Madurai was the capital of which ancient Tamil dynasty?",
        "choices": ["Chola", "Pandya", "Pallava", "Chera"],
        "accepted_answers": ["pandya"],
    },
    # Universe and Solar System
    {
        "id": "soc-geo-rotation",
        "lesson_id": "social-universe-solar-system",
        "subject_id": "social_science",
        "topic": "Geography",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "Earth's rotation on its own axis causes which phenomenon?",
        "choices": ["The Seasons", "Day and Night", "Tides", "Eclipses"],
        "accepted_answers": ["day and night"],
    },
    {
        "id": "soc-geo-planet-order",
        "lesson_id": "social-universe-solar-system",
        "subject_id": "social_science",
        "topic": "Geography",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "Which planet is fourth from the Sun?",
        "choices": ["Venus", "Earth", "Mars", "Jupiter"],
        "accepted_answers": ["mars"],
    },
    {
        "id": "soc-geo-revolution",
        "lesson_id": "social-universe-solar-system",
        "subject_id": "social_science",
        "topic": "Geography",
        "difficulty": "hard",
        "rating": 1100,
        "prompt": "Earth's revolution around the Sun takes approximately how long?",
        "choices": ["24 hours", "28 days", "365.25 days", "100 years"],
        "accepted_answers": ["365.25 days", "365 days", "one year"],
    },
    # Land and Oceans
    {
        "id": "soc-geo-largest-continent",
        "lesson_id": "social-land-oceans",
        "subject_id": "social_science",
        "topic": "Geography",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "Which is the largest continent in the world?",
        "choices": ["Africa", "Europe", "Asia", "North America"],
        "accepted_answers": ["asia"],
    },
    {
        "id": "soc-geo-tibetan",
        "lesson_id": "social-land-oceans",
        "subject_id": "social_science",
        "topic": "Geography",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "Which plateau is known as the 'Roof of the World'?",
        "choices": ["Deccan Plateau", "Tibetan Plateau", "Colorado Plateau", "Ethiopian Plateau"],
        "accepted_answers": ["tibetan plateau", "tibetan"],
    },
    {
        "id": "soc-geo-largest-ocean",
        "lesson_id": "social-land-oceans",
        "subject_id": "social_science",
        "topic": "Geography",
        "difficulty": "hard",
        "rating": 1100,
        "prompt": "Arrange the five oceans in order from largest to smallest.",
        "choices": [
            "Atlantic, Pacific, Indian, Southern, Arctic",
            "Pacific, Atlantic, Indian, Southern, Arctic",
            "Indian, Pacific, Atlantic, Arctic, Southern",
            "Pacific, Indian, Atlantic, Arctic, Southern",
        ],
        "accepted_answers": ["pacific, atlantic, indian, southern, arctic"],
    },
    # Understanding Diversity
    {
        "id": "soc-civics-unity-diversity",
        "lesson_id": "social-understanding-diversity",
        "subject_id": "social_science",
        "topic": "Civics",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "Who coined the phrase 'Unity in Diversity' for India?",
        "choices": ["Mahatma Gandhi", "Jawaharlal Nehru", "Dr. B.R. Ambedkar", "Sardar Patel"],
        "accepted_answers": ["jawaharlal nehru", "nehru"],
    },
    {
        "id": "soc-civics-languages",
        "lesson_id": "social-understanding-diversity",
        "subject_id": "social_science",
        "topic": "Civics",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "How many languages are officially recognised in the 8th Schedule of India's Constitution?",
        "choices": ["14", "18", "22", "28"],
        "accepted_answers": ["22"],
    },
    {
        "id": "soc-civics-diversity-types",
        "lesson_id": "social-understanding-diversity",
        "subject_id": "social_science",
        "topic": "Civics",
        "difficulty": "hard",
        "rating": 1100,
        "prompt": "Which of the following is NOT a type of diversity mentioned in Indian society?",
        "choices": ["Linguistic diversity", "Religious diversity", "Astronomical diversity", "Geographical diversity"],
        "accepted_answers": ["astronomical diversity"],
    },
    # Achieving Equality
    {
        "id": "soc-civics-article14",
        "lesson_id": "social-achieving-equality",
        "subject_id": "social_science",
        "topic": "Civics",
        "difficulty": "easy",
        "rating": 900,
        "prompt": "What does Article 14 of the Indian Constitution guarantee?",
        "choices": [
            "Freedom of speech",
            "Right to education",
            "Equality before the law",
            "Right to vote",
        ],
        "accepted_answers": ["equality before the law", "equality"],
    },
    {
        "id": "soc-civics-ambedkar",
        "lesson_id": "social-achieving-equality",
        "subject_id": "social_science",
        "topic": "Civics",
        "difficulty": "medium",
        "rating": 1000,
        "prompt": "What role did Dr. B.R. Ambedkar play in the creation of India's Constitution?",
        "choices": [
            "He was India's first President",
            "He chaired the Constitution Drafting Committee",
            "He was the first Prime Minister",
            "He proposed the Indian flag design",
        ],
        "accepted_answers": [
            "he chaired the constitution drafting committee",
            "chaired the drafting committee",
            "chairman of drafting committee",
        ],
    },
    {
        "id": "soc-civics-article17",
        "lesson_id": "social-achieving-equality",
        "subject_id": "social_science",
        "topic": "Civics",
        "difficulty": "hard",
        "rating": 1100,
        "prompt": "Which Article of the Indian Constitution abolishes untouchability?",
        "choices": ["Article 12", "Article 14", "Article 17", "Article 21"],
        "accepted_answers": ["article 17", "17"],
    },
)


# ─────────────────────────────────────────────────────────────────────────────
# Aggregated exports consumed by database.py
# ─────────────────────────────────────────────────────────────────────────────

ALL_LESSONS: tuple[LessonSeed, ...] = (
    *ENGLISH_LESSONS,
    *MATHEMATICS_LESSONS,
    *SCIENCE_LESSONS,
    *SOCIAL_SCIENCE_LESSONS,
)

ALL_QUESTIONS: tuple[QuestionSeed, ...] = (
    *ENGLISH_QUESTIONS,
    *MATHEMATICS_QUESTIONS,
    *SCIENCE_QUESTIONS,
    *SOCIAL_SCIENCE_QUESTIONS,
)
