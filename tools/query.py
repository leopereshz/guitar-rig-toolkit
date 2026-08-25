"""Point queries against the component dictionary and catalog.

`components.json` is hundreds of kilobytes and `COMPONENTS.md` is not much smaller. Neither
belongs in an LLM's context window, and neither is pleasant to grep by hand. This is the
lookup layer: ask a narrow question, get a short answer.

    python query.py categories                     # catalog, one line per category
    python query.py category Amplifiers            # what is in a category
    python query.py component "Lead 800"           # its parameters, ranges, observed values
    python query.py search reverb                  # name/category substring match
    python query.py param "Lead 800" V1            # one parameter
    python query.py preset "<file.ngrr>"           # what a preset actually contains
    python query.py missing                        # catalogued but no parameter data yet
    python query.py docs "midi mapping"            # which manual page answers this

Every command takes `--json` for machine-readable output.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
DICT_PATH = os.path.join(HERE, "components.json")
CATALOG_PATH = os.path.join(HERE, "catalog.json")


def load(path: str, what: str) -> dict:
    if not os.path.exists(path):
        raise SystemExit(f"{os.path.basename(path)} nao existe. Rode 'python {what}'.\n"
                         f"{os.path.basename(path)} missing. Run 'python {what}'.")
    return json.load(open(path, encoding="utf-8"))


def dictionary() -> dict:
    return load(DICT_PATH, "scan.py").get("components", {})


def catalog() -> dict:
    return load(CATALOG_PATH, "catalog.py")


def find(comps: dict, name: str) -> dict | None:
    low = name.lower()
    for c in comps.values():
        if c["name"].lower() == low or any(a.lower() == low for a in c.get("aliases", [])):
            return c
    return None


def fmt_param(p: dict) -> str:
    obs = (f"{p['observed_min']:g}–{p['observed_max']:g}"
           if p.get("observed_min") is not None else "—")
    rng = f"{p.get('min', '—')}..{p.get('max', '—')}"
    return f"  {p['id']:<8} {(p.get('name') or ''):<22} range {rng:<8} visto {obs}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("categories")
    a = sub.add_parser("category"); a.add_argument("name")
    a = sub.add_parser("component"); a.add_argument("name")
    a = sub.add_parser("search"); a.add_argument("term")
    a = sub.add_parser("param"); a.add_argument("component"); a.add_argument("param")
    a = sub.add_parser("preset"); a.add_argument("file")
    sub.add_parser("missing")
    a = sub.add_parser("docs"); a.add_argument("topic", nargs="?", default="")

    args = ap.parse_args()
    out: object = None

    if args.cmd == "categories":
        cat = catalog()
        comps = dictionary()
        known = {n for c in comps.values() for n in {c["name"], *c.get("aliases", [])}}
        out = {k: {"total": len(v), "com_parametros": sum(1 for i in v if i in known)}
               for k, v in cat["categories"].items()}
        if not args.json:
            for k, v in sorted(out.items(), key=lambda kv: -kv[1]["total"]):
                print(f"  {k:<16} {v['total']:>3} componentes, "
                      f"{v['com_parametros']:>3} com parametros")

    elif args.cmd == "category":
        cat = catalog()
        items = next((v for k, v in cat["categories"].items()
                      if k.lower() == args.name.lower()), None)
        if items is None:
            raise SystemExit(f"categoria desconhecida / unknown category: {args.name}. "
                             f"Opcoes: {', '.join(sorted(cat['categories']))}")
        comps = dictionary()
        out = [{"nome": i, "parametros": len(find(comps, i)["parameters"]) if find(comps, i) else 0,
                "presets": find(comps, i)["presets"] if find(comps, i) else 0} for i in items]
        if not args.json:
            for e in out:
                mark = "" if e["parametros"] else "   (sem dados / no data)"
                print(f"  {e['nome']:<24} {e['parametros']:>3} parametros{mark}")

    elif args.cmd == "component":
        comps = dictionary()
        c = find(comps, args.name)
        if c is None:
            raise SystemExit(f"sem dados para / no data for: {args.name}. "
                             f"Tente 'python query.py search {args.name.split()[0]}'.")
        cat = catalog()["components"].get(c["name"], "?")
        out = c
        if not args.json:
            print(f"{c['name']}  id={c['id']}  categoria={cat}  "
                  f"{'slot fixo' if c['fixed'] else 'cadeia'}  visto em {c['presets']} presets")
            for p in c["parameters"].values():
                print(fmt_param(p))

    elif args.cmd == "search":
        comps = dictionary()
        cat = catalog()
        term = args.term.lower()
        hits = []
        for name, category in cat["components"].items():
            if term in name.lower() or term in category.lower():
                c = find(comps, name)
                hits.append({"nome": name, "categoria": category,
                             "parametros": len(c["parameters"]) if c else 0})
        out = hits
        if not args.json:
            for h in hits:
                mark = "" if h["parametros"] else "   (sem dados / no data)"
                print(f"  {h['nome']:<24} {h['categoria']:<14} "
                      f"{h['parametros']:>3} parametros{mark}")
            if not hits:
                print("  (nada encontrado / nothing found)")

    elif args.cmd == "param":
        c = find(dictionary(), args.component)
        if c is None:
            raise SystemExit(f"sem dados para / no data for: {args.component}")
        p = c["parameters"].get(args.param)
        if p is None:
            raise SystemExit(f"{c['name']} nao tem '{args.param}'. Tem: "
                             + ", ".join(c["parameters"]))
        out = p
        if not args.json:
            print(f"{c['name']}.{p['id']}  ({p.get('name')})")
            print(fmt_param(p))
            if p.get("examples"):
                print("  exemplos:", ", ".join(p["examples"]))

    elif args.cmd == "preset":
        from grpreset import Preset, components as preset_components
        pr = Preset(args.file)
        chain = [(cid, cn, len(ps)) for cid, cn, fx, ps in preset_components(pr.rack) if not fx]
        out = {"container": pr.flavour, "cadeia": [{"id": c, "nome": n, "parametros": k}
                                                   for c, n, k in chain]}
        if not args.json:
            print(f"{os.path.basename(args.file)}  container={pr.flavour}  "
                  f"{len(chain)} componentes na cadeia")
            for cid, cn, k in chain:
                print(f"  id={cid:<8} {cn:<24} {k:>3} parametros")

    elif args.cmd == "missing":
        comps = dictionary()
        cat = catalog()
        known = {n for c in comps.values() for n in {c["name"], *c.get("aliases", [])}}
        out = {n: c for n, c in cat["components"].items() if n not in known}
        if not args.json:
            print(f"{len(out)} de {len(cat['components'])} componentes sem dados de parametro:")
            for n, c in sorted(out.items(), key=lambda kv: (kv[1], kv[0])):
                print(f"  {c:<14} {n}")

    elif args.cmd == "docs":
        idx = load(os.path.join(HERE, "docs-index.json"), "docs-index.json (shipped)")
        base = idx["_base_url"]
        term = args.topic.lower()
        if not term:
            out = [{"titulo": s["title"], "url": base + s["slug"]} for s in idx["sections"]]
            if not args.json:
                print(f"Manual oficial / official manual: {base}\n")
                for s in idx["sections"]:
                    print(f"  {s['title']:<30} {base + s['slug']}")
                print("\nDicas de busca / lookup hints:")
                for k, v in idx["lookup_hints"].items():
                    print(f"  {k:<30} -> {v}")
        else:
            hits = []
            for s in idx["sections"]:
                hay = " ".join([s["title"], *s.get("covers", []), *s.get("answers", []),
                                *s.get("keywords", [])]).lower()
                if term in hay:
                    hits.append(s)
            out = [{"titulo": s["title"], "url": base + s["slug"],
                    "cobre": s.get("covers", [])} for s in hits]
            if not args.json:
                if not hits:
                    print(f"nada para '{args.topic}'. Rode 'python query.py docs' para a lista.")
                for s in hits:
                    print(f"{s['title']}\n  {base + s['slug']}")
                    print("  cobre: " + ", ".join(s.get("covers", [])))
                    if s.get("relevant_to_this_project"):
                        print(f"  nota: {s['relevant_to_this_project']}")
                    print()

    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
