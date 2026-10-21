"""Portable TF-IDF logistic inference without pickle or arbitrary deserialization."""

import math
from collections import Counter
from features import tokens


def validate_artifact(model):
    if (
        not {
            "task",
            "version",
            "classes",
            "vocabulary",
            "idf",
            "coefficients",
            "intercepts",
            "threshold",
        }
        <= model.keys()
    ):
        raise ValueError("Invalid text model artifact")
    if model["task"] != "text" or len(model["idf"]) != len(model["vocabulary"]):
        raise ValueError("Invalid vocabulary contract")


def predict(payload, model):
    text = payload["text"]
    if not 20 <= len(text.strip()) <= 20000:
        raise ValueError("Text must contain 20–20000 characters")
    words = tokens(text)
    terms = words + [" ".join(pair) for pair in zip(words, words[1:])]
    counts = Counter(terms)
    values = {}
    for term, count in counts.items():
        index = model["vocabulary"].get(term)
        if index is not None:
            values[index] = (1 + math.log(count)) * model["idf"][index]
    norm = math.sqrt(sum(x * x for x in values.values())) or 1
    scores = [
        intercept + sum(coef[i] * value / norm for i, value in values.items())
        for intercept, coef in zip(model["intercepts"], model["coefficients"])
    ]
    peak = max(scores)
    exps = [math.exp(x - peak) for x in scores]
    total = sum(exps)
    probabilities = [x / total for x in exps]
    index = max(range(len(scores)), key=scores.__getitem__)
    confidence = probabilities[index]
    # Unknown vocabulary must never auto-route based only on intercept priors.
    review = confidence < model["threshold"] or not values
    return dict(
        route=model["classes"][index],
        confidence=confidence,
        needs_review=review,
        probabilities=dict(zip(model["classes"], probabilities)),
        known_terms=len(values),
    )
