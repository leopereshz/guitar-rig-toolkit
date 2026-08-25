"""Render the symptom reference from sintomas.json + a language catalog.

`sintomas.json` holds the structure; `i18n/<lang>.json` holds every string. This joins them
into one Markdown document per language, so a correction to the decision tree lands in all
languages at once and translations can never drift out of structural sync.

    python build_docs.py              # every language found in i18n/
                                      # writes into ../skills/guitar-rig/references/
    python build_docs.py --lang en    # just one
    python build_docs.py --check      # render nothing, only report unresolved keys
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
I18N = os.path.join(HERE, "i18n")
# The rendered references live inside the skill, because that is what reads them.
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "skills", "guitar-rig", "references"))

# output filename per language
FILENAME = {"pt-BR": "SINTOMAS.md", "en": "SYMPTOMS.md",
            "es": "SINTOMAS.es.md", "fr": "SYMPTOMES.fr.md"}


class Catalog:
    def __init__(self, path: str):
        self.data = json.load(open(path, encoding="utf-8"))
        self.lang = self.data.get("_lang", os.path.basename(path).replace(".json", ""))
        self.name = self.data.get("_name", self.lang)
        self.unresolved: set[str] = set()

    def t(self, value, default=""):
        """Resolve an '@key' reference; pass anything else through unchanged."""
        if isinstance(value, str) and value.startswith("@"):
            key = value[1:]
            if key not in self.data:
                self.unresolved.add(key)
                return default or f"«{key}»"
            return self.data[key]
        return value if value is not None else default

    def ui(self, key: str, default: str = "") -> str:
        full = f"ui.{key}"
        if full not in self.data:
            self.unresolved.add(full)
            return default or f"«{full}»"
        return self.data[full]


def fmt_delta(d) -> str:
    return f"{d:+.2f}".replace("+0.", "+0.").replace("-0.", "−0.")


def action_line(cat: Catalog, a: dict) -> str:
    comp = a.get("component", "")
    param = a.get("param", "")
    ref = f"`{comp}.{param}`" if comp != "*amp" else f"`{param}` ({cat.ui('any_amp')})"
    bits = []
    if a.get("delta") is not None:
        bits.append(f"**{fmt_delta(a['delta'])}**")
    if a.get("value") is not None:
        bits.append(f"**= {a['value']}**")
    if a.get("toggle"):
        bits.append(cat.ui("toggle"))
    if a.get("target_hz"):
        bits.append(f"@ {a['target_hz']} Hz")
    if a.get("sweep_hz"):
        lo, hi = a["sweep_hz"]
        bits.append(f"({cat.ui('sweep')} {lo}–{hi} Hz)")
    if a.get("q"):
        bits.append(f"Q {cat.ui('q_' + a['q'], a['q'])}")
    line = f"{ref} {' '.join(bits)}".rstrip()
    if a.get("if"):
        line += f" — *{cat.ui('when')} {cat.t(a['if'])}*"
    if a.get("repeat_until"):
        line += f" — *{cat.ui('repeat_until')} {cat.t(a['repeat_until'])}*"
    if a.get("compensate"):
        c = a["compensate"]
        line += f" — {cat.ui('compensate')} `{c['param']}` {fmt_delta(c['delta'])}"
    if a.get("note"):
        line += f"\n    {cat.t(a['note'])}"
    return line


def render(data: dict, cat: Catalog) -> str:
    L: list[str] = []
    add = L.append

    add(f"# {cat.ui('title')}")
    add("")
    add(cat.t(data["description"]))
    add("")
    corpus = data.get("corpus", {})
    if corpus:
        add(f"*{cat.ui('corpus')}: {corpus['presets']} presets, "
            f"{corpus['componentes']} {cat.ui('components')}, "
            f"{corpus['parametros']} {cat.ui('parameters')}.*")
        add("")

    add(f"## {cat.ui('order_title')}")
    add("")
    add("```")
    for i, fam in enumerate(data["diagnostic_order"], 1):
        add(f"{i}. {cat.ui('family_' + fam).upper():<12} {cat.ui('family_hint_' + fam)}")
    add("```")
    add("")
    add(cat.ui("order_rationale"))
    add("")

    add(f"## {cat.ui('bands_title')}")
    add("")
    add(f"| {cat.ui('band')} | Hz | {cat.ui('band_meaning')} |")
    add("|---|---|---|")
    for band, (lo, hi) in data["bands_hz"].items():
        add(f"| {cat.ui('band_' + band)} | {lo}–{hi} | {cat.ui('band_desc_' + band)} |")
    add("")

    by_family: dict[str, list] = {}
    for s in data["symptoms"]:
        by_family.setdefault(s["family"], []).append(s)

    for fam in data["diagnostic_order"]:
        add(f"## {cat.ui('family_' + fam)}")
        add("")
        for s in by_family.get(fam, []):
            complaints = cat.t(s.get("complaints"), [])
            add(f"### {cat.ui('sym_' + s['id'])}")
            add("")
            if complaints:
                add(f"**{cat.ui('complaints')}:** " + ", ".join(f'"{c}"' for c in complaints))
                add("")
            m = s.get("measurement")
            if m:
                add(f"**{cat.ui('measure')}:** `{cat.t(m.get('metric'))}` "
                    f"{cat.t(m.get('condition'))} — {cat.ui('conf_' + m.get('confidence', 'medium'))}")
                add("")
            if s.get("ear_test"):
                add(f"**{cat.ui('ear_test')}:** {cat.t(s['ear_test'])}")
                add("")
            if s.get("context"):
                add(f"> {cat.t(s['context'])}")
                add("")
            if s.get("not_to_confuse_with"):
                add(f"**{cat.ui('not_confuse')}** → *{cat.ui('sym_' + s['not_to_confuse_with'])}*")
                add("")
            if s.get("check_first"):
                add(f"**{cat.ui('check_first')}** → *{cat.ui('sym_' + s['check_first'])}*")
                add("")
            for other, why in (cat.t(s.get("distinguish_from"), {}) or {}).items():
                add(f"**{cat.ui('distinguish')} *{cat.ui('sym_' + other, other)}*:** {why}")
                add("")
            for fc in cat.t(s.get("false_causes"), []) or []:
                add(f"- {cat.ui('rule_out')}: {fc}")
            if s.get("false_causes"):
                add("")
            for cause in s.get("causes", []):
                add(f"**{cat.t(cause['cause'])}**")
                if cause.get("outside_guitar_rig"):
                    add(f"> {cat.ui('outside')} — {cat.t(cause.get('user_action'))}")
                if cause.get("order"):
                    add(f"> {cat.t(cause['order'])}")
                if cause.get("check"):
                    add(f"> {cat.ui('verify_present')}: " + ", ".join(f"`{c}`" for c in cause["check"]))
                add("")
                for a in cause.get("actions", []):
                    add(f"- {action_line(cat, a)}")
                if cause.get("actions"):
                    add("")
            if s.get("safety_net"):
                add(f"**{cat.ui('safety_net')}**")
                add("")
                for a in s["safety_net"]:
                    add(f"- {action_line(cat, a)}")
                add("")
            for p in cat.t(s.get("pitfalls"), []) or []:
                add(f"⚠️ {p}")
                add("")

    add(f"## {cat.ui('outside_title')}")
    add("")
    add(f"| {cat.ui('symptom')} | {cat.ui('cause')} | {cat.ui('where')} |")
    add("|---|---|---|")
    for e in data.get("outside_guitar_rig", []):
        add(f"| {cat.t(e['symptom'])} | {cat.t(e['cause'])} | {cat.t(e['where'])} |")
    add("")

    add(f"## {cat.ui('amp_title')}")
    add("")
    add("```")
    for k, v in data.get("common_amp_params", {}).items():
        add(f"{k:<12} {cat.t(v)}")
    add("```")
    add("")
    add(f"**{cat.ui('amp_exceptions')}**")
    add("")
    for amp, note in data.get("amp_exceptions", {}).items():
        add(f"- **{amp}** — {cat.t(note)}")
    add("")
    add("---")
    add("")
    add(cat.ui("footer"))
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lang", action="append", default=[])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    data = json.load(open(os.path.join(HERE, "sintomas.json"), encoding="utf-8"))
    paths = sorted(glob.glob(os.path.join(I18N, "*.json")))
    if args.lang:
        paths = [p for p in paths if os.path.basename(p).replace(".json", "") in args.lang]
    if not paths:
        raise SystemExit("nenhum catalogo em i18n/ / no catalog in i18n/")

    failed = False
    for path in paths:
        cat = Catalog(path)
        text = render(data, cat)
        out = os.path.join(OUT_DIR, FILENAME.get(cat.lang, f"SYMPTOMS.{cat.lang}.md"))
        status = f"{len(text):>7} chars"
        if cat.unresolved:
            failed = True
            status += f"   {len(cat.unresolved)} chaves nao resolvidas"
        if not args.check:
            open(out, "w", encoding="utf-8").write(text)
        print(f"  {cat.lang:<6} {cat.name:<22} -> {os.path.basename(out):<20} {status}")
        for k in sorted(cat.unresolved)[:10]:
            print(f"      ! {k}")

    sys.exit(1 if (failed and args.check) else 0)


if __name__ == "__main__":
    main()
