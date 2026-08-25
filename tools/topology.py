"""How Guitar Rig racks are actually wired, learned from a preset corpus.

`components.json` says what each knob is. This says what goes *next to* what: which component
usually precedes which, where each category sits in the signal path, how long a chain tends to
be. That is convention rather than authorship — nobody invented the idea that a cabinet
follows an amp — so unlike parameter values it can be summarised and shared.

Two rules keep the summary honest:

**Deduplicate first.** Preset packs are full of near-copies, and the same file often appears
twice under different names. Counting duplicates is not statistics, it is one preset shouting.
Chains are hashed and identical ones collapse to a single observation.

**Require a minimum count.** A pattern seen once is that preset's opinion, not a convention —
and at N=1 the "statistic" is literally one file's contents. `--min-n` defaults to 5.

    python topology.py build                     # write topology.json
    python topology.py show                      # read it back
    python topology.py check "A,B,C"             # sanity-check a proposed chain
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import find_presets, preset_roots
from scan import read_rack_xml

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "topology.json")

# Signal-path order most electric guitar rigs follow. Used to describe where a category sits,
# and to explain a warning in terms a player recognises rather than as a raw statistic.
CANONICAL = ["Filters", "Dynamics", "Distortion", "Amplifiers", "Cabinets", "Legacy",
             "EQ", "Modulation", "Delay & Echo", "Reverb"]


def categories() -> dict[str, str]:
    p = os.path.join(HERE, "catalog.json")
    if not os.path.exists(p):
        return {}
    return json.load(open(p, encoding="utf-8")).get("components", {})


def chains(files: list[str]) -> tuple[list[list[str]], int, int]:
    """Component-name sequences, one per preset, with duplicates collapsed."""
    seen: set[str] = set()
    out: list[list[str]] = []
    read = 0
    for path in files:
        try:
            xml, _ = read_rack_xml(path)
            if xml is None:
                continue
            root = ET.fromstring(xml)
        except Exception:  # noqa: BLE001
            continue
        nf = root.find("gr-rack/non-fix-components")
        if nf is None:
            continue
        read += 1
        seq = [c.get("name") for c in nf if c.tag == "component" and c.get("name")]
        if not seq:
            continue
        # hash the values too: two presets with the same components but different settings
        # are genuinely different racks, and both are evidence about ordering
        sig = hashlib.sha256(
            ("|".join(seq) + "#" + "".join(
                sorted(f"{p.get('id')}={p.get('value')}" for p in root.iter("parameter"))
            )).encode("utf-8")).hexdigest()
        if sig in seen:
            continue
        seen.add(sig)
        out.append(seq)
    return out, read, len(out)


def build(files: list[str], min_n: int) -> dict:
    seqs, read, unique = chains(files)
    cats = categories()

    adjacency: Counter = Counter()
    cat_adjacency: Counter = Counter()
    position: defaultdict = defaultdict(list)      # component -> normalised positions
    cat_position: defaultdict = defaultdict(list)
    together: Counter = Counter()
    lengths: list[int] = []
    comp_count: Counter = Counter()

    for seq in seqs:
        lengths.append(len(seq))
        for name in set(seq):
            comp_count[name] += 1
        for i, name in enumerate(seq):
            pos = i / max(1, len(seq) - 1)
            position[name].append(pos)
            c = cats.get(name)
            if c:
                cat_position[c].append(pos)
        for a, b in zip(seq, seq[1:]):
            if a == b:
                continue                            # doubled cabs etc. say nothing about order
            adjacency[(a, b)] += 1
            ca, cb = cats.get(a), cats.get(b)
            if ca and cb and ca != cb:
                cat_adjacency[(ca, cb)] += 1
        uniq = sorted(set(seq))
        for i, a in enumerate(uniq):
            for b in uniq[i + 1:]:
                together[(a, b)] += 1

    def summarise(samples: list[float]) -> dict:
        return {"n": len(samples),
                "median_position": round(statistics.median(samples), 3),
                "spread": round(statistics.pstdev(samples), 3) if len(samples) > 1 else 0.0}

    return {
        "_about": ("Wiring conventions learned from a preset corpus: what follows what, where "
                   "each category sits in the signal path, how long chains run. Structure "
                   "only — no parameter values, and nothing that identifies a source preset."),
        "corpus": {"presets_read": read, "unique_chains": unique, "min_n": min_n},
        "chain_length": {
            "median": statistics.median(lengths) if lengths else 0,
            "mean": round(statistics.mean(lengths), 1) if lengths else 0,
            "min": min(lengths) if lengths else 0,
            "max": max(lengths) if lengths else 0,
        },
        "component_position": {
            name: summarise(v) for name, v in sorted(position.items())
            if len(v) >= min_n
        },
        "category_position": {
            name: summarise(v) for name, v in sorted(cat_position.items())
            if len(v) >= min_n
        },
        "adjacency": [
            {"from": a, "to": b, "n": n}
            for (a, b), n in adjacency.most_common() if n >= min_n
        ],
        "category_adjacency": [
            {"from": a, "to": b, "n": n}
            for (a, b), n in cat_adjacency.most_common() if n >= min_n
        ],
        "co_occurrence": [
            {"pair": [a, b], "n": n}
            for (a, b), n in together.most_common(120) if n >= min_n
        ],
        "canonical_order": CANONICAL,
    }


# --------------------------------------------------------------------------- commands

def cmd_build(args) -> None:
    files = find_presets(preset_roots(args.path))
    if not files:
        raise SystemExit("nenhum preset encontrado / no presets found. Rode 'python paths.py'.")
    data = build(files, args.min_n)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)

    c = data["corpus"]
    dupes = c["presets_read"] - c["unique_chains"]
    print(f"presets lidos      : {c['presets_read']}")
    print(f"cadeias unicas     : {c['unique_chains']}   ({dupes} duplicadas descartadas)")
    print(f"comprimento tipico : mediana {data['chain_length']['median']}, "
          f"faixa {data['chain_length']['min']}-{data['chain_length']['max']}")
    print(f"pares (N >= {args.min_n})    : {len(data['adjacency'])} de componente, "
          f"{len(data['category_adjacency'])} de categoria")
    print(f"posicoes           : {len(data['component_position'])} componentes, "
          f"{len(data['category_position'])} categorias")
    print(f"\nescrito / written  : {OUT}")


def load() -> dict:
    if not os.path.exists(OUT):
        raise SystemExit("topology.json ausente. Rode 'python topology.py build'.")
    return json.load(open(OUT, encoding="utf-8"))


def cmd_show(args) -> None:
    d = load()
    c = d["corpus"]
    print(f"corpus: {c['unique_chains']} cadeias unicas de {c['presets_read']} presets, "
          f"N minimo {c['min_n']}")
    print(f"comprimento: mediana {d['chain_length']['median']}, "
          f"media {d['chain_length']['mean']}, faixa {d['chain_length']['min']}-"
          f"{d['chain_length']['max']}\n")

    print("posicao tipica por categoria (0 = inicio da cadeia, 1 = fim):")
    for name, s in sorted(d["category_position"].items(), key=lambda kv: kv[1]["median_position"]):
        bar = "-" * int(s["median_position"] * 30)
        print(f"  {name:<14} {s['median_position']:>5.2f}  n={s['n']:<4} {bar}|")

    print("\ntransicoes de categoria mais comuns:")
    for e in d["category_adjacency"][:12]:
        print(f"  {e['n']:>4}x  {e['from']} -> {e['to']}")

    print("\npares de componente mais comuns:")
    for e in d["adjacency"][:12]:
        print(f"  {e['n']:>4}x  {e['from']} -> {e['to']}")


def review(chain: list[str]) -> list[str]:
    """Observations about a proposed chain, empty when it matches what the corpus shows.

    Importable so callers do not have to shell out — rackbuild.py uses this to warn before
    it writes. Returns advice, never a verdict: the corpus knows only what it has seen.
    """
    if not os.path.exists(OUT):
        return []
    d = load()
    cats = categories()
    pos = d["component_position"]
    cat_pos = d["category_position"]
    adj = {(e["from"], e["to"]): e["n"] for e in d["adjacency"]}
    cat_adj = {(e["from"], e["to"]): e["n"] for e in d["category_adjacency"]}
    notes: list[str] = []

    for i, name in enumerate(chain):
        here = i / max(1, len(chain) - 1)
        s = pos.get(name) or cat_pos.get(cats.get(name, ""), None)
        if not s:
            continue
        drift = here - s["median_position"]
        if abs(drift) > 0.35 and abs(drift) > s["spread"]:
            where = "antes" if drift < 0 else "depois"
            notes.append(f"{name}: esta {where} do usual (posicao {here:.2f}, "
                         f"tipico {s['median_position']:.2f}, n={s['n']})")

    for a, b in zip(chain, chain[1:]):
        if adj.get((a, b)):
            continue
        rev = adj.get((b, a))
        if rev:
            notes.append(f"{a} -> {b}: nunca visto, mas {b} -> {a} aparece {rev}x — "
                         "talvez invertido")
            continue
        ca, cb = cats.get(a), cats.get(b)
        if ca and cb and ca != cb and not cat_adj.get((ca, cb)):
            rev_cat = cat_adj.get((cb, ca))
            if rev_cat:
                notes.append(f"{a} -> {b}: {ca} antes de {cb} nao aparece no corpus, "
                             f"enquanto {cb} -> {ca} aparece {rev_cat}x")

    cl = d["chain_length"]
    if len(chain) < cl["min"] or len(chain) > cl["max"]:
        notes.append(f"comprimento {len(chain)} esta fora da faixa observada "
                     f"({cl['min']}-{cl['max']})")
    return notes


def cmd_check(args) -> None:
    d = load()
    cats = categories()
    chain = [c.strip() for c in args.chain.split(",") if c.strip()]
    if not chain:
        raise SystemExit("cadeia vazia / empty chain")

    pos = d["component_position"]
    cat_pos = d["category_position"]
    adj = {(e["from"], e["to"]): e["n"] for e in d["adjacency"]}
    cat_adj = {(e["from"], e["to"]): e["n"] for e in d["category_adjacency"]}

    print(f"cadeia: {' -> '.join(chain)}\n")
    notes = []

    # order against the corpus' typical position
    for i, name in enumerate(chain):
        here = i / max(1, len(chain) - 1)
        s = pos.get(name) or cat_pos.get(cats.get(name, ""), None)
        if not s:
            notes.append(f"  {name}: sem dados suficientes no corpus para opinar")
            continue
        drift = here - s["median_position"]
        where = "antes" if drift < 0 else "depois"
        if abs(drift) > 0.35 and abs(drift) > s["spread"]:
            notes.append(f"  {name}: esta {where} do usual "
                         f"(posicao {here:.2f}, tipico {s['median_position']:.2f}, "
                         f"n={s['n']}) — confira se e intencional")

    # adjacent pairs
    for a, b in zip(chain, chain[1:]):
        ca, cb = cats.get(a), cats.get(b)
        n = adj.get((a, b))
        if n:
            continue
        rev = adj.get((b, a))
        if rev:
            notes.append(f"  {a} -> {b}: nunca visto, mas {b} -> {a} aparece {rev}x — "
                         "talvez invertido")
        elif ca and cb and ca != cb and not cat_adj.get((ca, cb)):
            rev_cat = cat_adj.get((cb, ca))
            if rev_cat:
                notes.append(f"  {a} -> {b}: {ca} antes de {cb} nao aparece no corpus, "
                             f"enquanto {cb} -> {ca} aparece {rev_cat}x")

    ln = len(chain)
    cl = d["chain_length"]
    if ln < cl["min"] or ln > cl["max"]:
        notes.append(f"  comprimento {ln} esta fora da faixa observada "
                     f"({cl['min']}-{cl['max']})")

    if notes:
        print("observacoes:")
        print("\n".join(notes))
        print("\nSao convencoes, nao regras. O corpus e o que ele e, e um rack deliberadamente")
        print("incomum pode estar perfeitamente certo.")
    else:
        print("nada a observar: ordem e adjacencias batem com o que o corpus mostra")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("build")
    a.add_argument("--path", action="append", default=[])
    a.add_argument("--min-n", type=int, default=5,
                   help="minimum observations before a pattern is recorded (default 5)")
    a.set_defaults(func=cmd_build)

    a = sub.add_parser("show"); a.set_defaults(func=cmd_show)

    a = sub.add_parser("check"); a.add_argument("chain"); a.set_defaults(func=cmd_check)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
