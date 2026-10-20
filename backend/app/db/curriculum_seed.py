"""Curriculum seed data for Class 6 Tamil Nadu State Board (English-medium)."""

from typing import TypedDict


class SubjectSeed(TypedDict):
    id: str
    name: str
    code: str
    icon: str
    accent_color: str
    display_order: int


class ChapterSeed(TypedDict):
    id: str
    subject_id: str
    term: int
    chapter_number: int
    title: str
    description: str
    textbook_pages: str
    lesson_id: str | None


class ConceptSeed(TypedDict):
    id: str
    chapter_id: str
    title: str
    summary: str
    key_points: list[str]
    display_order: int


CURRICULUM_SUBJECTS: tuple[SubjectSeed, ...] = (
    {
        "id": "english",
        "name": "English",
        "code": "ENG",
        "icon": "BookOpen",
        "accent_color": "#3B82F6",
        "display_order": 1,
    },
    {
        "id": "mathematics",
        "name": "Mathematics",
        "code": "MATH",
        "icon": "Calculator",
        "accent_color": "#10B981",
        "display_order": 2,
    },
    {
        "id": "science",
        "name": "Science",
        "code": "SCI",
        "icon": "Atom",
        "accent_color": "#8B5CF6",
        "display_order": 3,
    },
    {
        "id": "social_science",
        "name": "Social Science",
        "code": "SOC",
        "icon": "Globe",
        "accent_color": "#F59E0B",
        "display_order": 4,
    },
)


CURRICULUM_CHAPTERS: tuple[ChapterSeed, ...] = (
    # English (Term 1: 3 Units)
    {
        "id": "eng-term1-ch01",
        "subject_id": "english",
        "term": 1,
        "chapter_number": 1,
        "title": "Unit 1: Marine Life & Sea Turtles",
        "description": "Prose: Sea Turtles, Poem: The Crocodile, Supplementary: Owlie, Grammar: Nouns & Prefixes",
        "textbook_pages": "pp. 85-112",
        "lesson_id": "english-sea-turtles",
    },
    {
        "id": "eng-term1-ch02",
        "subject_id": "english",
        "term": 1,
        "chapter_number": 2,
        "title": "Unit 2: Nature & When the Trees Walked",
        "description": "Prose: When the Trees Walked by Ruskin Bond, Poem: Trees by Joyce Kilmer, Grammar: Adjectives",
        "textbook_pages": "pp. 113-138",
        "lesson_id": "english-trees-walked",
    },
    {
        "id": "eng-term1-ch03",
        "subject_id": "english",
        "term": 1,
        "chapter_number": 3,
        "title": "Unit 3: World Cultures & Spices",
        "description": "Prose: A Visitor from Distant Lands, Poem: I Dream of Spices, Grammar: Prepositions & Conjunctions",
        "textbook_pages": "pp. 139-166",
        "lesson_id": "english-spices-lands",
    },

    # Mathematics (Term 1: 6 Chapters)
    {
        "id": "math-term1-ch01",
        "subject_id": "mathematics",
        "term": 1,
        "chapter_number": 1,
        "title": "Chapter 1: Numbers",
        "description": "Large numbers, Indian & International systems, place values, BIDMAS order of operations, and whole number properties.",
        "textbook_pages": "pp. 1-28",
        "lesson_id": "math-large-numbers",
    },
    {
        "id": "math-term1-ch02",
        "subject_id": "mathematics",
        "term": 1,
        "chapter_number": 2,
        "title": "Chapter 2: Introduction to Algebra",
        "description": "Patterns in shapes and numbers, algebraic variables, expressions, and solving unknowns.",
        "textbook_pages": "pp. 29-46",
        "lesson_id": "math-algebra-intro",
    },
    {
        "id": "math-term1-ch03",
        "subject_id": "mathematics",
        "term": 1,
        "chapter_number": 3,
        "title": "Chapter 3: Ratio and Proportion",
        "description": "Ratio comparison, simplest form, proportions, product of extremes and means, and unitary method.",
        "textbook_pages": "pp. 47-68",
        "lesson_id": "math-ratio-proportion",
    },
    {
        "id": "math-term1-ch04",
        "subject_id": "mathematics",
        "term": 1,
        "chapter_number": 4,
        "title": "Chapter 4: Geometry",
        "description": "Lines, line segments, rays, parallel and perpendicular lines, angles classification, and collinear points.",
        "textbook_pages": "pp. 69-92",
        "lesson_id": None,
    },
    {
        "id": "math-term1-ch05",
        "subject_id": "mathematics",
        "term": 1,
        "chapter_number": 5,
        "title": "Chapter 5: Statistics",
        "description": "Data collection, tally marks, frequency distribution, pictographs, and bar graphs.",
        "textbook_pages": "pp. 93-114",
        "lesson_id": None,
    },
    {
        "id": "math-term1-ch06",
        "subject_id": "mathematics",
        "term": 1,
        "chapter_number": 6,
        "title": "Chapter 6: Information Processing",
        "description": "Systematic listing, tree diagrams, counting principles, and organizing combinations without omission.",
        "textbook_pages": "pp. 115-130",
        "lesson_id": None,
    },

    # Science (Term 1: 7 Units)
    {
        "id": "sci-term1-ch01",
        "subject_id": "science",
        "term": 1,
        "chapter_number": 1,
        "title": "Unit 1: Measurements",
        "description": "Physical quantities, SI base units, prefixes and submultiples, parallax error prevention, and laboratory measurement tools.",
        "textbook_pages": "pp. 1-16",
        "lesson_id": "science-measurements",
    },
    {
        "id": "sci-term1-ch02",
        "subject_id": "science",
        "term": 1,
        "chapter_number": 2,
        "title": "Unit 2: Force and Motion",
        "description": "Contact vs non-contact forces, types of motion (linear, circular, rotatory, oscillatory), and speed calculation.",
        "textbook_pages": "pp. 17-34",
        "lesson_id": None,
    },
    {
        "id": "sci-term1-ch03",
        "subject_id": "science",
        "term": 1,
        "chapter_number": 3,
        "title": "Unit 3: Matter Around Us",
        "description": "Solids, liquids, gases, particle arrangement, diffusion, and separation methods for mixtures.",
        "textbook_pages": "pp. 35-54",
        "lesson_id": "science-matter-basics",
    },
    {
        "id": "sci-term1-ch04",
        "subject_id": "science",
        "term": 1,
        "chapter_number": 4,
        "title": "Unit 4: The World of Plants",
        "description": "Plant morphology, root systems, shoot systems, leaf anatomy, photosynthesis, transpiration, and adaptations.",
        "textbook_pages": "pp. 55-74",
        "lesson_id": "science-plant-world",
    },
    {
        "id": "sci-term1-ch05",
        "subject_id": "science",
        "term": 1,
        "chapter_number": 5,
        "title": "Unit 5: The World of Animals",
        "description": "Unicellular vs multicellular organisms, Amoeba, Paramecium, Euglena, and animal adaptations in fish, frogs, birds, and camels.",
        "textbook_pages": "pp. 75-92",
        "lesson_id": None,
    },
    {
        "id": "sci-term1-ch06",
        "subject_id": "science",
        "term": 1,
        "chapter_number": 6,
        "title": "Unit 6: Health and Hygiene",
        "description": "Nutrients (carbs, fats, proteins, vitamins, minerals), deficiency diseases, balanced diet, and communicable infections.",
        "textbook_pages": "pp. 93-110",
        "lesson_id": None,
    },
    {
        "id": "sci-term1-ch07",
        "subject_id": "science",
        "term": 1,
        "chapter_number": 7,
        "title": "Unit 7: Computer — An Introduction",
        "description": "History of computers, pioneer Charles Babbage, five generations of hardware, CPU components, and input/output devices.",
        "textbook_pages": "pp. 111-124",
        "lesson_id": None,
    },

    # Social Science (Term 1: 8 Units — 4 History, 2 Geography, 2 Civics)
    {
        "id": "soc-term1-ch01",
        "subject_id": "social_science",
        "term": 1,
        "chapter_number": 1,
        "title": "History Unit 1: What is History?",
        "description": "Definition from Historia, pre-history, archaeological and literary sources, Emperor Ashoka and the Dharma Chakra.",
        "textbook_pages": "pp. 121-134",
        "lesson_id": "social-what-is-history",
    },
    {
        "id": "soc-term1-ch02",
        "subject_id": "social_science",
        "term": 1,
        "chapter_number": 2,
        "title": "History Unit 2: Human Evolution",
        "description": "Stages of human evolution from Australopithecus to Homo sapiens, discovery of fire, invention of wheel, and cave rock art.",
        "textbook_pages": "pp. 135-146",
        "lesson_id": None,
    },
    {
        "id": "soc-term1-ch03",
        "subject_id": "social_science",
        "term": 1,
        "chapter_number": 3,
        "title": "History Unit 3: Indus Civilisation",
        "description": "Harappa and Mohenjo-daro, grid planned towns, Great Bath, granaries, drainage systems, Lothal dockyard.",
        "textbook_pages": "pp. 147-164",
        "lesson_id": "social-indus-civilisation",
    },
    {
        "id": "soc-term1-ch04",
        "subject_id": "social_science",
        "term": 1,
        "chapter_number": 4,
        "title": "History Unit 4: Ancient Cities of Tamilagam",
        "description": "Sangam port city of Poompuhar, Pandya trade capital of Madurai (Naalangadi and Allangadi), and temple learning center Kanchi.",
        "textbook_pages": "pp. 165-178",
        "lesson_id": None,
    },
    {
        "id": "soc-term1-ch05",
        "subject_id": "social_science",
        "term": 1,
        "chapter_number": 5,
        "title": "Geography Unit 1: The Universe and Solar System",
        "description": "Big Bang, Milky Way, Sun and eight planets, terrestrial vs gas giants, rotation and revolution, and four spheres of Earth.",
        "textbook_pages": "pp. 179-198",
        "lesson_id": "social-universe-solar-system",
    },
    {
        "id": "soc-term1-ch06",
        "subject_id": "social_science",
        "term": 1,
        "chapter_number": 6,
        "title": "Geography Unit 2: Land and Oceans",
        "description": "First order landforms (7 continents and 5 oceans), second order landforms (mountains, plateaus, plains), and third order landforms.",
        "textbook_pages": "pp. 199-216",
        "lesson_id": None,
    },
    {
        "id": "soc-term1-ch07",
        "subject_id": "social_science",
        "term": 1,
        "chapter_number": 7,
        "title": "Civics Unit 1: Understanding Diversity",
        "description": "Geographical, linguistic, religious, and cultural diversity in India, 8th schedule official languages, and unity in diversity.",
        "textbook_pages": "pp. 217-226",
        "lesson_id": None,
    },
    {
        "id": "soc-term1-ch08",
        "subject_id": "social_science",
        "term": 1,
        "chapter_number": 8,
        "title": "Civics Unit 2: Achieving Equality",
        "description": "Prejudices, stereotypes, constitutional guarantees (Article 14, Article 17), and contributions of Dr. B.R. Ambedkar.",
        "textbook_pages": "pp. 227-238",
        "lesson_id": "social-achieving-equality",
    },
)


CURRICULUM_CONCEPTS: tuple[ConceptSeed, ...] = (
    # English Concepts
    {
        "id": "eng-ch01-c01",
        "chapter_id": "eng-term1-ch01",
        "title": "Sea Turtles & Marine Life",
        "summary": "Seven species of sea turtles exist globally; five visit Indian waters. They return to nesting beaches through mass arribada.",
        "key_points": [
            "Seven species worldwide; five in Indian waters (Olive Ridley, Hawksbill, Green Sea Turtle, Loggerhead, Leatherback).",
            "Leatherback is the largest sea turtle, growing up to 2.2 meters and 700 kg.",
            "Females come ashore only at night to lay eggs in deep sand pits.",
            "Odisha coast is world-famous for mass nesting arribada.",
        ],
        "display_order": 1,
    },
    {
        "id": "eng-ch02-c01",
        "chapter_id": "eng-term1-ch02",
        "title": "When the Trees Walked & Forest Conservation",
        "summary": "Grandfather's passion for planting saplings transforms a rocky riverbed into a vibrant green oasis for birds and animals.",
        "key_points": [
            "Plants seek light and water, stretching their roots toward nutrients.",
            "Planting trees prevents soil erosion and creates habitats for wildlife.",
            "Ruskin Bond reflects on returning to find grandfather's saplings grown into a forest.",
        ],
        "display_order": 1,
    },
    {
        "id": "eng-ch03-c01",
        "chapter_id": "eng-term1-ch03",
        "title": "Global Spice Trade & History",
        "summary": "How ancient explorers sailed across oceans in search of Indian black pepper, cloves, and cardamom.",
        "key_points": [
            "Black pepper was valued like black gold in ancient Rome and Greece.",
            "Vasco da Gama reached Calicut (Kozhikode) in Kerala in 1498 seeking spices.",
            "Chilies, potatoes, and tomatoes were introduced to India from South America via Portuguese traders.",
        ],
        "display_order": 1,
    },

    # Mathematics Concepts
    {
        "id": "math-ch01-c01",
        "chapter_id": "math-term1-ch01",
        "title": "Large Numbers & Number Systems",
        "summary": "Comparing Indian and International place value periods, reading numbers up to crores and billions.",
        "key_points": [
            "Indian system periods: Ones, Thousands, Lakhs, Crores.",
            "International system periods: Ones, Thousands, Millions, Billions.",
            "1 Crore = 10 Million; 100 Lakhs = 1 Crore.",
        ],
        "display_order": 1,
    },
    {
        "id": "math-ch01-c02",
        "chapter_id": "math-term1-ch01",
        "title": "BIDMAS Rule & Order of Operations",
        "summary": "Mathematical expressions must be evaluated in the strict order: Brackets, Indices, Division, Multiplication, Addition, Subtraction.",
        "key_points": [
            "B: Brackets first () [] {}",
            "I: Indices or Powers",
            "D & M: Division and Multiplication from left to right",
            "A & S: Addition and Subtraction from left to right",
        ],
        "display_order": 2,
    },
    {
        "id": "math-ch02-c01",
        "chapter_id": "math-term1-ch02",
        "title": "Variables & Algebraic Expressions",
        "summary": "Using letters to represent unknown or changing values and translating word situations into algebraic statements.",
        "key_points": [
            "A variable is an unknown value denoted by letters like x, y, n.",
            "A constant has a fixed numerical value.",
            "Algebraic expressions combine variables and constants using arithmetic operations.",
        ],
        "display_order": 1,
    },
    {
        "id": "math-ch03-c01",
        "chapter_id": "math-term1-ch03",
        "title": "Ratio, Proportion & Unitary Method",
        "summary": "Comparing quantities of the same unit through division and solving real-world rates using unit cost.",
        "key_points": [
            "Ratio a:b compares two quantities of the same kind and unit; it has no unit.",
            "In proportion a:b = c:d, Product of Extremes (a * d) equals Product of Means (b * c).",
            "The unitary method finds the value of a single unit before calculating the total required.",
        ],
        "display_order": 1,
    },

    # Science Concepts
    {
        "id": "sci-ch01-c01",
        "chapter_id": "sci-term1-ch01",
        "title": "SI Units & Physical Measurements",
        "summary": "Standard international units for length (metre), mass (kilogram), time (second), and volume (litre).",
        "key_points": [
            "Length is measured in metres (m); 1 km = 1000 m, 1 m = 100 cm, 1 cm = 10 mm.",
            "Mass is measured in kilograms (kg); beam and electronic balances measure mass accurately.",
            "Parallax error is avoided by looking vertically above the scale reading line.",
        ],
        "display_order": 1,
    },
    {
        "id": "sci-ch02-c01",
        "chapter_id": "sci-term1-ch02",
        "title": "Forces & Types of Motion",
        "summary": "Forces can push or pull, alter speed or direction; motion can be linear, circular, oscillatory, or periodic.",
        "key_points": [
            "Contact forces require physical touch (muscular, frictional).",
            "Non-contact forces act at a distance (gravitational, magnetic, electrostatic).",
            "Speed = Distance / Time; measured in metres per second (m/s) or km/h.",
        ],
        "display_order": 1,
    },
    {
        "id": "sci-ch03-c01",
        "chapter_id": "sci-term1-ch03",
        "title": "Three States of Matter & Separation of Mixtures",
        "summary": "Solids, liquids, and gases differ in particle spacing and motion; mixtures can be separated by filtration, sedimentation, and evaporation.",
        "key_points": [
            "Solids have fixed shape and volume; particles are tightly packed.",
            "Liquids take the shape of their container; particles slide over each other.",
            "Gases fill all available space; particles are very far apart and move rapidly.",
            "Insoluble solids can be separated from liquids by sedimentation, decantation, and filtration.",
        ],
        "display_order": 1,
    },
    {
        "id": "sci-ch04-c01",
        "chapter_id": "sci-term1-ch04",
        "title": "Plant Structure & Functions",
        "summary": "Root systems absorb water and nutrients; shoot systems carry out photosynthesis, respiration, and transpiration.",
        "key_points": [
            "Tap root system has one main thick root with lateral branches (mustard, bean).",
            "Fibrous root system consists of a cluster of thin roots originating from stem base (grass, paddy).",
            "Leaves produce food via photosynthesis using sunlight, chlorophyll, CO2, and water.",
            "Transpiration releases excess water vapor through microscopic stomata.",
        ],
        "display_order": 1,
    },

    # Social Science Concepts
    {
        "id": "soc-ch01-c01",
        "chapter_id": "soc-term1-ch01",
        "title": "What is History & Archaeological Sources",
        "summary": "History is the systematic study of the past based on inscriptions, coins, monuments, and literary records.",
        "key_points": [
            "The term History is derived from Greek word Historia, meaning learning by inquiry.",
            "Emperor Ashoka embraced Buddhism after the Kalinga war and spread message of peace.",
            "The 24-spoke Dharma Chakra on the Indian national flag is taken from Ashoka's Sarnath pillar.",
        ],
        "display_order": 1,
    },
    {
        "id": "soc-ch03-c01",
        "chapter_id": "soc-term1-ch03",
        "title": "Indus Valley Civilisation Town Planning",
        "summary": "Advanced urban civilisation characterized by grid-pattern streets, covered drainage systems, and the Great Bath.",
        "key_points": [
            "Harappa was discovered in 1920 in Punjab; Mohenjo-daro in Sindh.",
            "Streets were laid out on a grid system with right-angle intersections.",
            "Drains were covered with stone slabs or bricks and connected to street mains.",
            "Lothal was a prominent port and dockyard city on the Sabarmati river in Gujarat.",
        ],
        "display_order": 1,
    },
    {
        "id": "soc-ch05-c01",
        "chapter_id": "soc-term1-ch05",
        "title": "The Solar System & Planetary Motions",
        "summary": "The Sun at the center with eight planets; rotation causes day and night while revolution causes seasons.",
        "key_points": [
            "The Solar System formed 4.6 billion years ago and resides in the Milky Way galaxy.",
            "Inner terrestrial planets: Mercury, Venus, Earth, Mars (rocky surfaces).",
            "Outer gas giants: Jupiter, Saturn, Uranus, Neptune.",
            "Earth's rotation on its tilted axis takes 24 hours; revolution around the Sun takes 365.25 days.",
        ],
        "display_order": 1,
    },
    {
        "id": "soc-ch08-c01",
        "chapter_id": "soc-term1-ch08",
        "title": "Equality & The Indian Constitution",
        "summary": "Constitutional provisions guarantee fundamental equality and outlaw discrimination in India.",
        "key_points": [
            "Article 14 ensures equality before the law and equal protection of laws.",
            "Article 17 completely abolishes the practice of untouchability.",
            "Dr. B.R. Ambedkar chaired the Constitution Drafting Committee and is known as the Father of Indian Constitution.",
        ],
        "display_order": 1,
    },
)
