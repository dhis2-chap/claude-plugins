"""Duplicate candidates by text similarity. Writes dup_candidates.json.

Run with: uv run --with scikit-learn python dups.py
Compares every in-scope issue against the whole project (jira_other_summaries.jsonl).
Keeps pairs where at least one side is in scope and at least one is open.
"""
import json
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

cfg = json.load(open("config.json"))
DONE = set(cfg["done_statuses"])
TFIDF_MIN, JACCARD_MIN, MAX_PAIRS = 0.22, 0.34, 150
STOP = {"the", "and", "for", "with", "from", "add", "support", "when", "that", "this", "should", "not", cfg["project"].lower()}

issues = json.load(open("jira.json"))
corpus = [{"key": d["key"], "summary": d["summary"], "status": d["status"], "in_scope": d["in_scope"], "type": d["type"],
           "parent": d["parent"], "text": d["summary"] + " " + d["desc"][:500]} for d in issues.values()]
for line in open("jira_other_summaries.jsonl"):
    d = json.loads(line)
    if d["key"] not in issues:
        corpus.append({"key": d["key"], "summary": d["summary"], "status": d["status"], "in_scope": False, "type": d["type"], "parent": None, "text": d["summary"]})

X = TfidfVectorizer(stop_words="english", sublinear_tf=True).fit_transform([c["text"] for c in corpus])
sim = cosine_similarity(X)
toks = [set(re.findall(r"[a-z0-9]{3,}", c["summary"].lower())) - STOP for c in corpus]

pairs = []
for i in range(len(corpus)):
    for j in range(i + 1, len(corpus)):
        a, b = corpus[i], corpus[j]
        if not (a["in_scope"] or b["in_scope"]) or (a["status"] in DONE and b["status"] in DONE) or "Epic" in (a["type"], b["type"]):
            continue
        jac = len(toks[i] & toks[j]) / len(toks[i] | toks[j]) if toks[i] | toks[j] else 0
        if sim[i, j] >= TFIDF_MIN or jac >= JACCARD_MIN:
            pairs.append({"a": a["key"], "a_summary": a["summary"], "a_status": a["status"], "b": b["key"], "b_summary": b["summary"], "b_status": b["status"],
                          "tfidf": round(float(sim[i, j]), 3), "jaccard": round(jac, 3), "same_epic": a["parent"] is not None and a["parent"] == b["parent"]})

pairs.sort(key=lambda p: -(p["tfidf"] + p["jaccard"]))
print(f"{len(pairs)} candidate pairs, keeping {min(len(pairs), MAX_PAIRS)}")
json.dump(pairs[:MAX_PAIRS], open("dup_candidates.json", "w"), indent=1)
