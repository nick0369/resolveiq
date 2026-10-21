"""Train on 2015–2016, select on Q1 2017, set policy on Q2, test later dates."""

import argparse, json, platform, time, hashlib
from pathlib import Path
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from data import load_data
from features import normalize
from policy import choose_threshold
from evaluate import text_metrics
from inference import predict


def main(source=None):
    start = time.perf_counter()
    df = load_data(source)
    train = df[df.date < "2017-01-01"]
    selection = df[(df.date >= "2017-01-01") & (df.date < "2017-04-01")]
    policy = df[(df.date >= "2017-04-01") & (df.date < "2017-07-01")]
    test = df[df.date >= "2017-07-01"]
    assert min(map(len, [train, selection, policy, test])) > 100
    assert not (set(train.text_hash) & set(test.text_hash))
    candidates = []
    for C in [1.0, 4.0]:
        pipe = Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        token_pattern=r"(?u)[a-z0-9]{2,}",
                        ngram_range=(1, 2),
                        max_features=18000,
                        min_df=3,
                        sublinear_tf=True,
                        preprocessor=normalize,
                    ),
                ),
                ("classifier", LogisticRegression(C=C, max_iter=1500, random_state=42)),
            ]
        )
        pipe.fit(train.text, train.label)
        candidates.append(
            (
                f1_score(
                    selection.label, pipe.predict(selection.text), average="macro"
                ),
                C,
                pipe,
            )
        )
    score, C, pipe = max(candidates, key=lambda x: x[0])
    probs = pipe.predict_proba(policy.text)
    classes = pipe.classes_.tolist()
    correct = np.asarray(classes)[probs.argmax(axis=1)] == policy.label.to_numpy()
    threshold = choose_threshold(
        probs.max(axis=1), correct, required_precision=0.90, min_cases=100
    )
    vector = pipe["tfidf"]
    lr = pipe["classifier"]
    model = dict(
        task="text",
        version="resolveiq-v1",
        classes=classes,
        threshold=threshold,
        vocabulary={k: int(v) for k, v in vector.vocabulary_.items()},
        idf=vector.idf_.tolist(),
        coefficients=lr.coef_.tolist(),
        intercepts=lr.intercept_.tolist(),
    )
    # Only synthetic text is shipped with the public inference examples.
    synthetic = [
        "My credit card statement includes a purchase I never made and the bank will not correct it.",
        "My mortgage servicer has not applied the payment to my home loan and is threatening foreclosure.",
        "A debt collector keeps calling me about money I do not owe and refuses to validate the debt.",
        "There is an incorrect account on my credit report and the bureau has not investigated my dispute.",
        "My student loan payments increased and I cannot get help with repayment from the servicer.",
        "The bank has frozen my checking account and will not return the deposit I made last week.",
    ]
    examples = []
    for text in synthetic:
        original = float(pipe.predict_proba([text]).max())
        assert abs(original - predict({"text": text}, model)["confidence"]) < 1e-9
        examples.append({"input": {"text": text}, "expected_confidence": original})
    Path("model.json").write_text(
        json.dumps(model, separators=(",", ":")), encoding="utf-8"
    )
    Path("examples.json").write_text(json.dumps(examples, indent=2), encoding="utf-8")
    probs = pipe.predict_proba(test.text)
    metrics = text_metrics(test.label, probs, classes, threshold)
    majority = train.label.value_counts().index[0]
    metrics.update(
        n_train=len(train),
        n_selection=len(selection),
        n_policy=len(policy),
        n_test=len(test),
        train_end="2016-12-31",
        selection_end="2017-03-31",
        policy_end="2017-06-30",
        test_start="2017-07-01",
        test_end=str(test.date.max().date()),
        selected_C=C,
        selection_macro_f1=float(score),
        threshold=threshold,
        classes=classes,
        majority_macro_f1=float(
            f1_score(test.label, [majority] * len(test), average="macro")
        ),
        vocabulary_size=len(vector.vocabulary_),
        train_seconds=time.perf_counter() - start,
        python=platform.python_version(),
    )
    hashes = df[["id", "date", "text_hash"]].copy()
    hashes["split"] = np.select(
        [df.date < "2017-01-01", df.date < "2017-04-01", df.date < "2017-07-01"],
        ["train", "selection", "policy"],
        default="test",
    )
    # IDs and hashes only, never public narrative text.
    hashes.to_csv("split_manifest.csv", index=False)
    Path("metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source")
    main(parser.parse_args().source)
