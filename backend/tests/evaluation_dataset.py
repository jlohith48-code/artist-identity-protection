"""
evaluation_dataset.py - Benchmark dataset for lyric similarity evaluation.
"""

EVALUATION_PAIRS = [
    {
        "id": "pair_01",
        "category": "exact_duplicate",
        "language_a": "English",
        "language_b": "English",
        "expected_similarity": "duplicate",
        "text_a": "I walk beneath the starlight sky tonight looking for peace.",
        "text_b": "I walk beneath the starlight sky tonight looking for peace."
    },
    {
        "id": "pair_02",
        "category": "formatting_variation",
        "language_a": "English",
        "language_b": "English",
        "expected_similarity": "duplicate",
        "text_a": "I walk beneath the starlight sky tonight looking for peace.",
        "text_b": "I WALK BENEATH\nTHE STARLIGHT SKY TONIGHT!\nLooking for peace..."
    },
    {
        "id": "pair_03",
        "category": "minor_word_change",
        "language_a": "English",
        "language_b": "English",
        "expected_similarity": "high_similarity",
        "text_a": "I walk beneath the starlight sky tonight looking for peace.",
        "text_b": "I walk beneath the starlight sky this evening searching for peace."
    },
    {
        "id": "pair_04",
        "category": "paraphrase",
        "language_a": "English",
        "language_b": "English",
        "expected_similarity": "high_similarity",
        "text_a": "I walk beneath the starlight sky tonight looking for peace.",
        "text_b": "Tonight I wander under the shining stars in search of quietness."
    },
    {
        "id": "pair_05",
        "category": "synonym_substitution",
        "language_a": "English",
        "language_b": "English",
        "expected_similarity": "high_similarity",
        "text_a": "My heart is broken into pieces.",
        "text_b": "My heart is shattered into fragments."
    },
    {
        "id": "pair_06",
        "category": "unrelated",
        "language_a": "English",
        "language_b": "English",
        "expected_similarity": "unrelated",
        "text_a": "My heart is broken into pieces.",
        "text_b": "The express train arrived at platform number four right on schedule."
    },
    {
        "id": "pair_07",
        "category": "partial_copy",
        "language_a": "English",
        "language_b": "English",
        "expected_similarity": "moderate_similarity",
        "text_a": "First verse about sunny summer days on the beach. Chorus: My heart is broken into pieces under the heavy rain. Second verse about winter snow falling softly.",
        "text_b": "Opening about city traffic and busy streets. Chorus: My heart is broken into pieces under the heavy rain. Outro about highway miles."
    },
    {
        "id": "pair_08",
        "category": "regional_kannada",
        "language_a": "Kannada",
        "language_b": "Kannada",
        "expected_similarity": "high_similarity",
        "text_a": "ನನ್ನ ಪ್ರೀತಿಯ ಹಾಡು ಸದಾ ನನ್ನ ಮನಸ್ಸಿನಲ್ಲಿ ಉಳಿಯುತ್ತದೆ.",
        "text_b": "ನನ್ನ ಪ್ರೀತಿಯ ಗೀತೆ ಸದಾ ನನ್ನ ಹೃದಯದಲ್ಲಿ ನೆಲೆಸುತ್ತದೆ."
    },
    {
        "id": "pair_09",
        "category": "regional_hindi",
        "language_a": "Hindi",
        "language_b": "Hindi",
        "expected_similarity": "high_similarity",
        "text_a": "दिल में तेरी यादों की शमा जलती रहती है।",
        "text_b": "हृदय में तुम्हारी स्मृतियों का दीपक जलता रहता है।"
    },
    {
        "id": "pair_10",
        "category": "regional_tamil",
        "language_a": "Tamil",
        "language_b": "Tamil",
        "expected_similarity": "high_similarity",
        "text_a": "என் இதயத்தில் உன்னுடைய நினைவுகள் என்றும் வாழும்.",
        "text_b": "என்னுடைய மனதில் உனது நினைவுகள் எப்போதும் நிலைக்கும்."
    },
    {
        "id": "pair_11",
        "category": "regional_telugu",
        "language_a": "Telugu",
        "language_b": "Telugu",
        "expected_similarity": "high_similarity",
        "text_a": "నా గుండెల్లో నీ జ్ఞాపకాలు ఎప్పటికీ నిలిచిపోతాయి.",
        "text_b": "నా మనస్సులో నీ నవ్వుల వెలుగు ఎల్లప్పుడూ ఉంటుంది."
    },
    {
        "id": "pair_12",
        "category": "cross_language_english_kannada",
        "language_a": "English",
        "language_b": "Kannada",
        "expected_similarity": "high_similarity",
        "text_a": "My heart is shattered into pieces under the rain.",
        "text_b": "ಮಳೆಯ ಅಡಿಯಲ್ಲಿ ನನ್ನ ಹೃದಯವು ಚೂರಚೂರಾಗಿ ಒಡೆದು ಹೋಗಿದೆ."
    }
]
