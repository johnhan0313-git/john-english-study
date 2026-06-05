from __future__ import annotations

SCENARIO_SCHEMA = """
{
  "title": "string",
  "theme": "string",
  "passage": "string (150-450 words, must use ALL target words naturally)",
  "dialogue": [{"speaker": "string", "text": "string"}],
  "word_usage": [{"word": "string", "sentence": "string", "meaning_zh": "string"}],
  "summary_zh": "string",
  "fun_fact": "string (interesting fact related to theme or vocabulary)"
}
"""


def build_scenario_prompt(
    words: list[dict],
    level: str,
    theme: str,
    scenario_type: str,
) -> list[dict[str, str]]:
    word_list = ", ".join(w["lemma"] for w in words)
    word_details = "\n".join(
        f"- {w['lemma']} ({w.get('pos', 'n.')}) {', '.join(w.get('definitions', []))}" for w in words
    )
    length = "150-300 words" if level == "cet4" else "250-450 words"
    type_instruction = (
        "Write as a natural dialogue between 2-3 characters with at least 6 lines."
        if scenario_type == "dialogue"
        else "Write as a cohesive narrative passage."
    )
    return [
        {
            "role": "user",
            "content": (
                f"Create an English learning scenario for CET-{level[-1]} level.\n"
                f"Theme: {theme}\n"
                f"Type: {scenario_type}. {type_instruction}\n"
                f"Target words (each MUST appear at least once): {word_list}\n"
                f"Word details:\n{word_details}\n"
                f"Length: {length}. Keep vocabulary at CET-{level[-1]} level.\n"
                f"Tone: professional yet engaging for adult learners.\n"
                f"Return JSON matching the schema."
            ),
        }
    ]


EXERCISE_SCHEMA = """
{
  "exercises": [
    {
      "type": "single_choice",
      "question": "string",
      "options": [{"label": "A|B|C|D", "text": "string"}],
      "correct_label": "A|B|C|D",
      "explanation": "string"
    },
    {
      "type": "fill_blank",
      "passage_with_blanks": "string with ___ for blanks",
      "blanks": [{"index": 0, "hint": "v.", "answer": "word", "accept": ["word", "words"]}],
      "explanation": "string"
    }
  ]
}
"""


def build_exercise_prompt(scenario_title: str, passage: str, target_words: list[str]) -> list[dict[str, str]]:
    words = ", ".join(target_words)
    return [
        {
            "role": "user",
            "content": (
                f"Based on this English learning scenario titled '{scenario_title}':\n\n"
                f"{passage}\n\n"
                f"Generate exactly 5 single_choice questions and 3 fill_blank questions.\n"
                f"Focus on vocabulary: {words} and reading comprehension.\n"
                f"For fill_blank, blank out target vocabulary words.\n"
                f"Each single_choice must have exactly 4 options (A-D).\n"
                f"Return JSON with 'exercises' array."
            ),
        }
    ]


WRITING_EVAL_PROMPT = """
Evaluate the student's writing. Return JSON:
{
  "score": 0-100,
  "grammar_feedback": "string",
  "vocabulary_feedback": "string",
  "used_target_words": ["word"],
  "missing_target_words": ["word"],
  "suggestions": ["string"]
}
"""
