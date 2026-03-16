"""Outbreak Report Classifier using Transformers"""
import logging
import re
from typing import List, Tuple

logger = logging.getLogger(__name__)

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available, using rule-based classifier")


# Classification labels
LABELS = ["confirmed_outbreak", "suspected_outbreak", "news_mention"]

# Keywords for rule-based fallback
CONFIRMED_KEYWORDS = [
    "confirmed", "outbreak confirmed", "cases confirmed", "laboratory confirmed",
    "officially reported", "declared outbreak", "emergency declared",
    "epidemic declared", "pandemic", "confirmed dead", "confirmed cases"
]

SUSPECTED_KEYWORDS = [
    "suspected", "under investigation", "potential outbreak",
    "preliminary reports", "unconfirmed", "possible cases",
    "monitoring", "alert issued", "surveillance alert",
    "unusual cluster", "increased cases", "being investigated"
]

NEWS_KEYWORDS = [
    "according to", "reports suggest", "news", "media reports",
    "sources say", "press release", "announcement", "update",
    "briefing", "statement", "analysis", "review", "overview"
]


class OutbreakClassifier:
    """Classify outbreak reports into confirmed/suspected/news categories."""

    def __init__(self):
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load the zero-shot classification model."""
        if TRANSFORMERS_AVAILABLE:
            try:
                self.model = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    device=-1  # CPU
                )
                logger.info("Loaded BERT/BART classifier model")
            except Exception as e:
                logger.warning(f"Failed to load transformer model: {e}")
                self.model = None

    def classify(self, text: str) -> Tuple[str, float]:
        """
        Classify a report text.
        
        Returns:
            Tuple of (label, confidence)
        """
        if not text:
            return "news_mention", 0.0

        if self.model:
            try:
                return self._transformer_classify(text)
            except Exception as e:
                logger.warning(f"Transformer classification failed: {e}")

        return self._rule_based_classify(text)

    def classify_batch(self, texts: List[str]) -> List[Tuple[str, float]]:
        """Classify multiple texts."""
        return [self.classify(text) for text in texts]

    def _transformer_classify(self, text: str) -> Tuple[str, float]:
        """Use zero-shot classification with BART."""
        candidate_labels = [
            "confirmed disease outbreak with verified cases",
            "suspected disease outbreak under investigation",
            "general health news or media report"
        ]

        result = self.model(text[:512], candidate_labels)

        label_map = {
            "confirmed disease outbreak with verified cases": "confirmed_outbreak",
            "suspected disease outbreak under investigation": "suspected_outbreak",
            "general health news or media report": "news_mention"
        }

        top_label = result["labels"][0]
        confidence = result["scores"][0]

        return label_map.get(top_label, "news_mention"), round(confidence, 3)

    def _rule_based_classify(self, text: str) -> Tuple[str, float]:
        """Rule-based fallback classifier."""
        text_lower = text.lower()

        confirmed_score = sum(1 for kw in CONFIRMED_KEYWORDS if kw in text_lower)
        suspected_score = sum(1 for kw in SUSPECTED_KEYWORDS if kw in text_lower)
        news_score = sum(1 for kw in NEWS_KEYWORDS if kw in text_lower)

        # Boost confirmed if death/case numbers mentioned
        if re.search(r'\d+\s*(deaths?|dead|killed|fatalities)', text_lower):
            confirmed_score += 2
        if re.search(r'\d+\s*(cases?|infected|positive)', text_lower):
            confirmed_score += 1

        total = confirmed_score + suspected_score + news_score + 1
        scores = {
            "confirmed_outbreak": confirmed_score / total,
            "suspected_outbreak": suspected_score / total,
            "news_mention": news_score / total
        }

        # Default to news if no strong signals
        if max(scores.values()) < 0.2:
            return "news_mention", 0.5

        best_label = max(scores, key=scores.get)
        return best_label, round(max(scores.values()), 3)


# Singleton instance
_classifier_instance = None


def get_classifier() -> OutbreakClassifier:
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = OutbreakClassifier()
    return _classifier_instance


def classify_report(text: str) -> Tuple[str, float]:
    """Convenience function for single report classification."""
    return get_classifier().classify(text)
