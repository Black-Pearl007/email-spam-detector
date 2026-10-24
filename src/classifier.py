import re


def clean(text: str) -> str:
    """Must match the cleaning used in the Colab training notebook."""
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"http\S+", " URL ", text)
    return re.sub(r"\s+", " ", text).strip()


class SpamClassifier:
    def __init__(self, model_dir, threshold=0.5):
        from transformers import pipeline  # imported here so the dashboard can start without a model

        self.threshold = threshold
        self.pipe = pipeline(
            "text-classification", model=str(model_dir), top_k=None, truncation=True, max_length=256
        )

    def predict(self, subject: str, body: str) -> dict:
        text = clean(f"{subject}. {body}")
        scores = {d["label"]: d["score"] for d in self.pipe(text)[0]}
        prob = float(scores["spam"])
        return {"spam_prob": prob, "label": "spam" if prob >= self.threshold else "ham"}
