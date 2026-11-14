import re
from threading import Lock

from app.core.config import get_settings

EMOTION_LEXICON: dict[str, tuple[str, ...]] = {
    "joy": ("радост", "весел", "позитив", "счастлив", "празднич", "светл", "воодушев", "оптимист"),
    "sadness": ("груст", "печал", "меланхол", "тоск", "ностальг", "одиночеств", "разлук", "уныл"),
    "calm": ("спокой", "расслаб", "умиротвор", "тих", "медитатив", "безмятеж", "уют"),
    "energy": ("энерг", "динамич", "бодр", "мотивир", "ритмич", "быстр", "трениров", "танцев", "мощн"),
    "romance": ("романтич", "нежн", "чувствен", "любов", "свидан", "ласк", "интимн"),
    "anxiety": ("тревож", "напряж", "беспокой", "мрач", "страш", "опасн", "неуверен"),
}
TOKEN_RE = re.compile(r"[а-яёa-z]+", re.IGNORECASE)
NEGATIONS = {"не", "без", "никак"}
EMOTIONS = tuple(EMOTION_LEXICON)


class EmotionAnalyzer:
    """Russian multi-label emotion model with an interpretable lexicon fallback."""

    def __init__(self) -> None:
        self.model_name = get_settings().emotion_model
        self._tokenizer = None
        self._model = None
        self._torch = None
        self._load_attempted = False
        self._load_lock = Lock()
        self.mode = "lexicon"

    def _load(self) -> bool:
        with self._load_lock:
            if self._model is not None:
                return True
            if self._load_attempted:
                return False
            self._load_attempted = True
            try:
                import torch
                from transformers import AutoModelForSequenceClassification, AutoTokenizer

                self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
                self._model.eval()
                self._torch = torch
                self.mode = "rubert_multi_label"
                return True
            except Exception:
                self.mode = "lexicon"
                return False

    @staticmethod
    def _lexicon_scores(text: str) -> dict[str, float]:
        tokens = [token.lower() for token in TOKEN_RE.findall(text)]
        scores = {emotion: 0.0 for emotion in EMOTIONS}
        for index, token in enumerate(tokens):
            if index and tokens[index - 1] in NEGATIONS:
                continue
            for emotion, stems in EMOTION_LEXICON.items():
                if any(token.startswith(stem) for stem in stems):
                    scores[emotion] = max(scores[emotion], 0.85)
        return scores

    def analyze(self, text: str) -> dict[str, float]:
        scores = self._lexicon_scores(text)
        if not self._load():
            return scores

        try:
            inputs = self._tokenizer(text, return_tensors="pt", truncation=True, max_length=256)
            with self._torch.inference_mode():
                logits = self._model(**inputs).logits[0]
                probabilities = self._torch.sigmoid(logits).tolist()

            labels = self._model.config.id2label
            predicted = {str(labels[index]).lower(): float(value) for index, value in enumerate(probabilities)}
            mapped_labels = {"joy", "happiness", "sadness", "enthusiasm", "surprise", "fear"}
            if not mapped_labels.intersection(predicted):
                self.mode = "lexicon"
                return scores
            # Label names vary by model revision; only compatible labels are mapped.
            # Calm and romance stay lexicon-based because the model has no such labels.
            scores["joy"] = max(scores["joy"], predicted.get("joy", 0.0), predicted.get("happiness", 0.0))
            scores["sadness"] = max(scores["sadness"], predicted.get("sadness", 0.0))
            scores["energy"] = max(scores["energy"], predicted.get("enthusiasm", 0.0), predicted.get("surprise", 0.0))
            scores["anxiety"] = max(scores["anxiety"], predicted.get("fear", 0.0))
        except Exception:
            self.mode = "lexicon"
        return {key: max(0.0, min(value, 1.0)) for key, value in scores.items()}

    @staticmethod
    def has_signal(scores: dict[str, float]) -> bool:
        return any(value >= 0.12 for value in scores.values())
