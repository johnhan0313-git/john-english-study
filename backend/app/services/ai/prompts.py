from __future__ import annotations

SCENARIO_SCHEMA = """
{
  "title": "string",
  "theme": "string",
  "passage": "string (150-450 words, must use ALL target words naturally)",
  "dialogue": [{"speaker": "string", "text": "string"}],
  "word_usage": [{"word": "string", "sentence": "string", "meaning_zh": "string"}],
  "summary_zh": "string",
  "passage_zh": "string (natural Simplified Chinese translation of passage)",
  "fun_fact": "string (interesting fact related to theme or vocabulary)"
}
"""

SCENARIO_SYSTEM = """You are an English reading scenario writer for CET-4/CET-6 learners.
Your job is STEP 1 ONLY: write a reading scenario (story or dialogue context).
Return ONLY one JSON object with these keys: title, theme, passage, dialogue, word_usage, summary_zh, passage_zh, fun_fact.
CRITICAL: Include a non-empty "passage" field with the main English text (150+ words).
Include "passage_zh": a faithful Simplified Chinese translation of the full passage.
Do NOT return exercises, questions, quiz, or an "exercises" key."""

EXERCISE_SYSTEM = """You are an English quiz generator.
Your job is STEP 2 ONLY: create practice questions based on a given passage.
Return ONLY one JSON object with key "exercises" (array of question objects).
Do NOT return passage, title, or scenario fields."""

TRANSLATION_SCHEMA = """
{
  "passage_zh": "string (faithful Simplified Chinese translation of the passage)",
  "dialogue_zh": [{"speaker": "string", "text": "string"}]
}
"""

TRANSLATION_SYSTEM = """You translate English learning materials into natural Simplified Chinese.
Return ONLY valid JSON with keys passage_zh and dialogue_zh (empty array if no dialogue).
Keep proper nouns when appropriate; translate the full passage faithfully."""


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
                f"Tone: professional yet engaging for adult learners.\n\n"
                f"IMPORTANT: This is STEP 1 — generate a READING SCENARIO only.\n"
                f"Do NOT generate exercises or questions. Do NOT use key 'exercises'.\n"
                f"Required JSON keys: title, theme, passage, dialogue, word_usage, summary_zh, passage_zh, fun_fact.\n"
                f"The 'passage' field must be a long English text using all target words."
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
                f"IMPORTANT: This is STEP 2 — generate EXERCISES only.\n"
                f"Return JSON with single key 'exercises' (array). Do NOT return passage or title."
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

WRITING_SAMPLE_SCHEMA = """
{
  "sample_en": "string (about 80 words, natural paragraph using ALL target words)",
  "sample_zh": "string (faithful Simplified Chinese translation of sample_en)"
}
"""

WRITING_SAMPLE_SYSTEM = """You write model paragraphs for English learners (CET-4/CET-6).
Return ONLY valid JSON with keys sample_en and sample_zh.
The English paragraph should be ~80 words, cohesive, and use every target word naturally.
The Chinese translation should faithfully match sample_en."""
