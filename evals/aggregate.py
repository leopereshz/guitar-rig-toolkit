"""Aggregate the independent trigger judgements into a score per query.

Three judges see the same skill list and the same 20 queries, without being told which
answer is expected. Agreement between them is the signal: a query all three agree on is a
clear case, one they split on marks a boundary the description does not yet draw sharply.
"""

from __future__ import annotations

import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

import sys

ROUND = sys.argv[1] if len(sys.argv) > 1 else "easy"
EVAL_FILE = "trigger-eval.json" if ROUND == "easy" else "trigger-eval-hard.json"
JUDGE_GLOB = "judge-*.json" if ROUND == "easy" else "hard-judge-*.json"
PREFIX = "judge-" if ROUND == "easy" else "hard-judge-"

print(f"rodada / round: {ROUND}\n")
evals = {e["id"]: e for e in json.load(open(os.path.join(HERE, EVAL_FILE), encoding="utf-8"))}
judges = {}
for path in sorted(glob.glob(os.path.join(HERE, JUDGE_GLOB))):
    name = os.path.basename(path).replace(PREFIX, "").replace(".json", "")
    judges[name] = {v["id"]: v for v in json.load(open(path, encoding="utf-8"))}

if not judges:
    raise SystemExit("nenhum judge-*.json ainda / no judge files yet")

print(f"juizes / judges: {', '.join(sorted(judges))}\n")

rows, wrong, split = [], [], []
for eid, e in sorted(evals.items()):
    votes = [judges[j][eid]["trigger"] for j in sorted(judges) if eid in judges[j]]
    if not votes:
        continue
    yes = sum(votes)
    rate = yes / len(votes)
    majority = rate > 0.5
    ok = majority == e["should_trigger"]
    unanimous = yes in (0, len(votes))
    rows.append((eid, e, votes, rate, ok, unanimous))
    if not ok:
        wrong.append((eid, e, rate))
    elif not unanimous:
        split.append((eid, e, rate))

print(f"{'id':>3} {'lang':<5} {'esperado':<9} {'votos':<9} {'taxa':>5}  {'':2} consulta")
print("-" * 100)
for eid, e, votes, rate, ok, unan in rows:
    mark = "OK " if ok and unan else ("~  " if ok else "X  ")
    v = "".join("Y" if x else "n" for x in votes)
    exp = "disparar" if e["should_trigger"] else "ignorar"
    print(f"{eid:>3} {e['lang']:<5} {exp:<9} {v:<9} {rate:>4.0%}  {mark} {e['query'][:58]}...")

total = len(rows)
correct = sum(1 for r in rows if r[4])
unanimous_correct = sum(1 for r in rows if r[4] and r[5])
pos = [r for r in rows if r[1]["should_trigger"]]
neg = [r for r in rows if not r[1]["should_trigger"]]

print()
print(f"acerto por maioria     : {correct}/{total}  ({correct/total:.0%})")
print(f"acerto unanime         : {unanimous_correct}/{total}  ({unanimous_correct/total:.0%})")
print(f"  deve disparar        : {sum(1 for r in pos if r[4])}/{len(pos)}   (recall)")
print(f"  deve ignorar         : {sum(1 for r in neg if r[4])}/{len(neg)}   (precisao)")

if wrong:
    print(f"\nERROS ({len(wrong)}) — a descricao precisa mudar:")
    for eid, e, rate in wrong:
        want = "deveria disparar" if e["should_trigger"] else "NAO deveria disparar"
        print(f"  [{eid}] {want}, taxa {rate:.0%}\n      {e['query'][:90]}")

if split:
    print(f"\nDIVERGENCIA ({len(split)}) — acertou por maioria, mas a fronteira nao esta nitida:")
    for eid, e, rate in split:
        print(f"  [{eid}] taxa {rate:.0%}\n      {e['query'][:90]}")

if not wrong and not split:
    print("\nUnanimidade em todas as consultas.")
