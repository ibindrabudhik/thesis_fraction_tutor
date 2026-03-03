"""
Quiz Questions Data for Fractions Quiz

This module contains hardcoded multiple choice questions for all quiz sections.
Each question has an ID, question text, options, correct answer, and knowledge areas.

Use MathJax/LaTeX notation ($$...$$) for mathematical expressions.
"""

QUIZ_QUESTIONS = {
    # "pre_test": [
    #     {
    #         "id": "pre_1",
    #         "question": "Bentuk paling sederhana dari pecahan $$\\frac{12}{18}$$ adalah...",
    #         "options": [
    #             "A. $$\\frac{2}{3}$$",
    #             "B. $$\\frac{3}{4}$$",
    #             "C. $$\\frac{4}{6}$$",
    #             "D. $$\\frac{6}{9}$$"
    #         ],
    #         "correct_answer": "A",
    #         "knowledge_areas": ["simplifying"]
    #     },
    #     {
    #         "id": "pre_2",
    #         "question": "Hasil dari $$\\frac{1}{4} + \\frac{2}{4}$$ adalah...",
    #         "options": [
    #             "A. $$\\frac{3}{8}$$",
    #             "B. $$\\frac{3}{4}$$",
    #             "C. $$\\frac{1}{2}$$",
    #             "D. $$\\frac{2}{4}$$"
    #         ],
    #         "correct_answer": "B",
    #         "knowledge_areas": ["addition"]
    #     },
    #     {
    #         "id": "pre_3",
    #         "question": "Hasil dari $$\\frac{4}{5} - \\frac{2}{5}$$ adalah...",
    #         "options": [
    #             "A. $$\\frac{6}{5}$$",
    #             "B. $$\\frac{2}{10}$$",
    #             "C. $$\\frac{1}{5}$$",
    #             "D. $$\\frac{2}{5}$$"
    #         ],
    #         "correct_answer": "D",
    #         "knowledge_areas": ["subtraction"]
    #     },
    #     {
    #         "id": "pre_4",
    #         "question": "Hasil dari $$\\frac{1}{2} \\times \\frac{3}{5}$$ adalah...",
    #         "options": [
    #             "A. $$\\frac{4}{7}$$",
    #             "B. $$\\frac{3}{10}$$",
    #             "C. $$\\frac{2}{10}$$",
    #             "D. $$\\frac{3}{7}$$"
    #         ],
    #         "correct_answer": "B",
    #         "knowledge_areas": ["multiplication"]
    #     },
    #     {
    #         "id": "pre_5",
    #         "question": "Hasil dari $$\\frac{1}{3} \\div \\frac{1}{2}$$ adalah...",
    #         "options": [
    #             "A. $$\\frac{2}{3}$$",
    #             "B. $$\\frac{1}{6}$$",
    #             "C. $$\\frac{3}{2}$$",
    #             "D. $$\\frac{1}{5}$$"
    #         ],
    #         "correct_answer": "A",
    #         "knowledge_areas": ["division"]
    #     },
    # ],
    
    "ordering_fractions": [
        {
            "id": "ord_2",
            "question": "Urutan pecahan $$\\frac{1}{2}, \\frac{1}{3}, \\frac{1}{4}$$ dari yang terkecil adalah...",
            "options": [
                "A. $$\\frac{1}{2}, \\frac{1}{3}, \\frac{1}{4}$$",
                "B. $$\\frac{1}{3}, \\frac{1}{2}, \\frac{1}{4}$$",
                "C. $$\\frac{1}{4}, \\frac{1}{3}, \\frac{1}{2}$$",
                "D. $$\\frac{1}{4}, \\frac{1}{2}, \\frac{1}{3}$$"
            ],
            "correct_answer": "C",
            "knowledge_areas": ["ordering"]
        },
        {
            "id": "ord_3",
            "question": "Tanda pembanding yang tepat untuk $$\\frac{3}{5} ... \\frac{4}{7}$$ adalah...",
            "options": [
                "A. <",
                "B. >",
                "C. =",
                "D. \\leq"
            ],
            "correct_answer": "B",
            "knowledge_areas": ["ordering"]
        },
        {
            "id": "ord_4",
            "question": "Pecahan yang terletak di antara $$\\frac{1}{5}$$ dan $$\\frac{3}{5}$$ adalah...",
            "options": [
                "A. $$\\frac{2}{5}$$",
                "B. $$\\frac{4}{5}$$",
                "C. $$\\frac{1}{2}$$",
                "D. $$\\frac{3}{10}$$"
            ],
            "correct_answer": "A",
            "knowledge_areas": ["ordering"]
        },
    ],
    
    "fraction_addition": [
        {
            "id": "add_2",
            "question": "Hasil dari $$\\frac{2}{5} + \\frac{1}{2}$$ adalah...",
            "options": [
                "A. $$\\frac{3}{7}$$",
                "B. $$\\frac{3}{10}$$",
                "C. $$\\frac{9}{10}$$",
                "D. $$\\frac{4}{5}$$"
            ],
            "correct_answer": "C",
            "knowledge_areas": ["addition"]
        },
        {
            "id": "add_3",
            "question": "Hasil dari $$1 \\frac{1}{2} + \\frac{1}{4}$$ adalah...",
            "options": [
                "A. $$1 \\frac{2}{4}$$",
                "B. $$1 \\frac{3}{4}$$",
                "C. $$\\frac{3}{4}$$",
                "D. $$2$$"
            ],
            "correct_answer": "B",
            "knowledge_areas": ["addition"]
        },
        {
            "id": "add_4",
            "question": "Ibu membeli $$\\frac{3}{4}$$ kg telur dan $$\\frac{1}{2}$$ kg tepung. Total berat belanjaan Ibu adalah...",
            "options": [
                "A. $$1 \\frac{1}{4}$$ kg",
                "B. $$1 \\frac{1}{2}$$ kg",
                "C. $$\\frac{4}{6}$$ kg",
                "D. $$1 \\frac{3}{4}$$ kg"
            ],
            "correct_answer": "A",
            "knowledge_areas": ["addition"]
        },
    ],
    
    "fraction_subtraction": [
        {
            "id": "sub_2",
            "question": "Hasil dari $$\\frac{3}{4} - \\frac{1}{3}$$ adalah...",
            "options": [
                "A. $$\\frac{2}{1}$$",
                "B. $$\\frac{5}{12}$$",
                "C. $$\\frac{2}{12}$$",
                "D. $$\\frac{1}{12}$$"
            ],
            "correct_answer": "B",
            "knowledge_areas": ["subtraction"]
        },
        {
            "id": "sub_3",
            "question": "Hasil dari $$2 - \\frac{3}{4}$$ adalah...",
            "options": [
                "A. $$\\frac{1}{4}$$",
                "B. $$1 \\frac{1}{4}$$",
                "C. $$\\frac{5}{4}$$",
                "D. $$1 \\frac{3}{4}$$"
            ],
            "correct_answer": "B",
            "knowledge_areas": ["subtraction"]
        },
        {
            "id": "sub_4",
            "question": "Sebuah botol berisi $$\\frac{7}{8}$$ liter air. Jika diminum $$\\frac{1}{4}$$ liter, sisa air adalah...",
            "options": [
                "A. $$\\frac{6}{4}$$ liter",
                "B. $$\\frac{5}{8}$$ liter",
                "C. $$\\frac{3}{4}$$ liter",
                "D. $$\\frac{1}{2}$$ liter"
            ],
            "correct_answer": "B",
            "knowledge_areas": ["subtraction"]
        },
        # {
        #     "id": "sub_5",
        #     "question": "Hasil dari $$\\frac{4}{5} - \\frac{1}{10}$$ adalah...",
        #     "options": [
        #         "A. $$\\frac{7}{10}$$",
        #         "B. $$\\frac{3}{5}$$",
        #         "C. $$\\frac{3}{10}$$",
        #         "D. $$\\frac{5}{10}$$"
        #     ],
        #     "correct_answer": "A",
        #     "knowledge_areas": ["subtraction"]
        # },
    ],
    
    "fraction_multiplication": [
        # {
        #     "id": "mul_1",
        #     "question": "Hasil dari $$\\frac{2}{5} \\times \\frac{5}{6}$$ adalah...",
        #     "options": [
        #         "A. $$\\frac{1}{3}$$",
        #         "B. $$\\frac{7}{11}$$",
        #         "C. $$\\frac{10}{11}$$",
        #         "D. $$\\frac{2}{6}$$"
        #     ],
        #     "correct_answer": "A",
        #     "knowledge_areas": ["multiplication"]
        # },
        {
            "id": "mul_2",
            "question": "Hasil dari $$\\frac{3}{4}$$ dari $$20$$ adalah...",
            "options": [
                "A. $$5$$",
                "B. $$10$$",
                "C. $$15$$",
                "D. $$12$$"
            ],
            "correct_answer": "C",
            "knowledge_areas": ["multiplication"]
        },
        {
            "id": "mul_3",
            "question": "Hasil dari $$\\frac{1}{2} \\times \\frac{4}{7}$$ adalah...",
            "options": [
                "A. $$\\frac{5}{9}$$",
                "B. $$\\frac{2}{7}$$",
                "C. $$\\frac{4}{14}$$",
                "D. $$\\frac{1}{7}$$"
            ],
            "correct_answer": "B",
            "knowledge_areas": ["multiplication"]
        },
        {
            "id": "mul_4",
            "question": "Hasil dari $$2 \\frac{1}{2} \\times \\frac{1}{2}$$ adalah...",
            "options": [
                "A. $$1$$",
                "B. $$1 \\frac{1}{4}$$",
                "C. $$2 \\frac{1}{4}$$",
                "D. $$\\frac{5}{2}$$"
            ],
            "correct_answer": "B",
            "knowledge_areas": ["multiplication"]
        },
        # {
        #     "id": "mul_5",
        #     "question": "Hasil perkalian $$\\frac{3}{8}$$ dengan $$\\frac{2}{3}$$ adalah...",
        #     "options": [
        #         "A. $$\\frac{1}{4}$$",
        #         "B. $$\\frac{5}{11}$$",
        #         "C. $$\\frac{6}{24}$$",
        #         "D. $$\\frac{1}{8}$$"
        #     ],
        #     "correct_answer": "A",
        #     "knowledge_areas": ["multiplication"]
        # },
    ],
    
    "fraction_division": [
        {
            "id": "div_1",
            "question": "Hasil dari $$\\frac{3}{4} \\div \\frac{1}{2}$$ adalah...",
            "options": [
                "A. $$\\frac{3}{8}$$",
                "B. $$1 \\frac{1}{2}$$",
                "C. $$\\frac{2}{3}$$",
                "D. $$2$$"
            ],
            "correct_answer": "B",
            "knowledge_areas": ["division"]
        },
        {
            "id": "div_2",
            "question": "Hasil dari $$4 \\div \\frac{1}{2}$$ adalah...",
            "options": [
                "A. $$2$$",
                "B. $$4$$",
                "C. $$6$$",
                "D. $$8$$"
            ],
            "correct_answer": "D",
            "knowledge_areas": ["division"]
        },
        {
            "id": "div_3",
            "question": "Hasil dari $$\\frac{2}{3} \\div \\frac{4}{9}$$ adalah...",
            "options": [
                "A. $$1 \\frac{1}{2}$$",
                "B. $$\\frac{8}{27}$$",
                "C. $$\\frac{2}{3}$$",
                "D. $$1 \\frac{1}{4}$$"
            ],
            "correct_answer": "A",
            "knowledge_areas": ["division"]
        },
        {
            "id": "div_4",
            "question": "Ibu memiliki $$\\frac{3}{4}$$ liter santan yang akan dibagikan ke dalam wadah berukuran $$\\frac{1}{8}$$ liter. Banyak wadah yang diperlukan adalah...",
            "options": [
                "A. $$4$$ buah",
                "B. $$5$$ buah",
                "C. $$6$$ buah",
                "D. $$8$$ buah"
            ],
            "correct_answer": "C",
            "knowledge_areas": ["division"]
        },
        {
            "id": "div_5",
            "question": "Hasil dari $$\\frac{5}{6} \\div 5$$ adalah...",
            "options": [
                "A. $$\\frac{1}{6}$$",
                "B. $$\\frac{25}{6}$$",
                "C. $$1$$",
                "D. $$\\frac{5}{30}$$"
            ],
            "correct_answer": "A",
            "knowledge_areas": ["division"]
        },
    ],
    
    # "post_test": [
    #     {
    #         "id": "post_1",
    #         "question": "Manakah pernyataan yang benar?",
    #         "options": [
    #             "A. $$\\frac{1}{3} > \\frac{1}{2}$$",
    #             "B. $$\\frac{2}{5} < \\frac{1}{4}$$",
    #             "C. $$\\frac{3}{4} > \\frac{2}{3}$$",
    #             "D. $$\\frac{1}{2} = \\frac{2}{5}$$"
    #         ],
    #         "correct_answer": "C",
    #         "knowledge_areas": ["ordering"]
    #     },
    #     {
    #         "id": "post_2",
    #         "question": "Hasil dari $$\\frac{2}{3} + \\frac{1}{4}$$ adalah...",
    #         "options": [
    #             "A. $$\\frac{3}{7}$$",
    #             "B. $$\\frac{11}{12}$$",
    #             "C. $$\\frac{3}{12}$$",
    #             "D. $$\\frac{9}{12}$$"
    #         ],
    #         "correct_answer": "B",
    #         "knowledge_areas": ["addition"]
    #     },
    #     {
    #         "id": "post_3",
    #         "question": "Hasil dari $$\\frac{7}{9} - \\frac{1}{3}$$ adalah...",
    #         "options": [
    #             "A. $$\\frac{6}{6}$$",
    #             "B. $$\\frac{4}{9}$$",
    #             "C. $$\\frac{2}{3}$$",
    #             "D. $$\\frac{5}{9}$$"
    #         ],
    #         "correct_answer": "B",
    #         "knowledge_areas": ["subtraction"]
    #     },
    #     {
    #         "id": "post_4",
    #         "question": "Hasil dari $$\\frac{4}{5} \\times \\frac{15}{16}$$ adalah...",
    #         "options": [
    #             "A. $$\\frac{3}{4}$$",
    #             "B. $$\\frac{60}{80}$$",
    #             "C. $$\\frac{1}{2}$$",
    #             "D. $$\\frac{19}{21}$$"
    #         ],
    #         "correct_answer": "A",
    #         "knowledge_areas": ["multiplication"]
    #     },
    #     {
    #         "id": "post_5",
    #         "question": "Hasil dari $$\\frac{6}{7} \\div 3$$ adalah...",
    #         "options": [
    #             "A. $$\\frac{2}{7}$$",
    #             "B. $$\\frac{18}{7}$$",
    #             "C. $$\\frac{2}{21}$$",
    #             "D. $$\\frac{3}{7}$$"
    #         ],
    #         "correct_answer": "A",
    #         "knowledge_areas": ["division"]
    #     },
    # ]
}


def get_questions_by_section(section_key: str) -> list:
    """
    Get all questions for a specific section.
    
    Args:
        section_key: One of the keys in QUIZ_QUESTIONS dict
        
    Returns:
        List of question dicts
    """
    return QUIZ_QUESTIONS.get(section_key, [])


def get_question_by_id(question_id: str) -> dict:
    """
    Find a specific question by its ID across all sections.
    
    Args:
        question_id: The unique question ID
        
    Returns:
        Question dict or None if not found
    """
    for section_questions in QUIZ_QUESTIONS.values():
        for question in section_questions:
            if question["id"] == question_id:
                return question
    return None
