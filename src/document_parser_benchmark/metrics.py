"""Field-level precision, recall, and F1.

A field counts as a true positive only when its extracted value matches
ground truth exactly. A wrong value counts as both a false positive and a
false negative: the parser claimed something and still missed the truth.
"""


def score(result, ground_truth):
    extracted = result.field_map()
    tp = fp = fn = 0
    for name, truth in ground_truth.items():
        if extracted.get(name) == truth:
            tp += 1
        else:
            fn += 1
    for name, value in extracted.items():
        if name not in ground_truth or ground_truth[name] != value:
            fp += 1
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def aggregate(results_with_truth):
    """Aggregate per-parser totals across documents, then recompute P/R/F1."""
    tp = fp = fn = 0
    for result, truth in results_with_truth:
        s = score(result, truth)
        tp += s["tp"]
        fp += s["fp"]
        fn += s["fn"]
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}
