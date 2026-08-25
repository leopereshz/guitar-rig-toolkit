"""Verify the symptom reference against the extracted component dictionary.

Checks that every component and parameter `sintomas.json` points at actually exists in
`components.json`. A reference that does not resolve means the advice names a knob that is
not there.

Also checks the translation catalogs: every "@key" the structure references must exist in
every language file, and no language file may carry keys the structure no longer uses.

    python validate_sintomas.py
"""

from __future__ import annotations

import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
comps = json.load(open(os.path.join(HERE, "components.json"), encoding="utf-8"))["components"]
sint = json.load(open(os.path.join(HERE, "sintomas.json"), encoding="utf-8"))

by_name = {c["name"]: c for c in comps.values()}

errors: list[str] = []
warnings: list[str] = []
checked = 0


def check_action(where: str, act: dict) -> None:
    global checked
    checked += 1
    comp_name = act.get("component")
    param = act.get("param")

    # wildcard: "any amp" — alternatives are pipe-separated
    if comp_name == "*amp":
        alts = param.split("|")
        if not any(a in c["parameters"] for c in comps.values() for a in alts):
            errors.append(f"{where}: nenhum componente tem {param}")
        return

    c = by_name.get(comp_name)
    if c is None:
        errors.append(f"{where}: componente '{comp_name}' nao existe no dicionario")
        return

    if act.get("id") and act["id"] != c["id"]:
        errors.append(f"{where}: id {act['id']} != {c['id']} para '{comp_name}'")

    for pid in [param] + act.get("related_params", []):
        if pid is not None and pid not in c["parameters"]:
            errors.append(f"{where}: '{comp_name}' nao tem parametro '{pid}'")

    comp_ = act.get("compensate")
    if comp_ and comp_.get("param"):
        alts = comp_["param"].split("|")
        if comp_name != "*amp" and not any(a in c["parameters"] for a in alts):
            warnings.append(f"{where}: compensate '{comp_['param']}' nao existe em '{comp_name}'")

    if c["presets"] <= 2:
        warnings.append(f"{where}: '{comp_name}' aparece em apenas {c['presets']} preset(s) - "
                        "pode nao estar no preset em uso")


for s in sint["symptoms"]:
    sid = s["id"]
    for cause in s.get("causes", []):
        label = cause.get("cause", "?").lstrip("@").split(".")[-2:]
        for act in cause.get("actions", []):
            check_action(f"{sid}/{'.'.join(label)}", act)
        for name in cause.get("check", []):
            checked += 1
            if name not in by_name:
                errors.append(f"{sid}: componente a verificar '{name}' nao existe")
    for act in s.get("safety_net", []):
        check_action(f"{sid}/safety_net", act)

for amp_name in sint.get("amp_exceptions", {}):
    checked += 1
    if amp_name not in by_name:
        errors.append(f"amp_exceptions: '{amp_name}' nao existe no dicionario")

# cross-references between symptoms
ids = {s["id"] for s in sint["symptoms"]}
for s in sint["symptoms"]:
    for key in ("not_to_confuse_with", "check_first"):
        if s.get(key) and s[key] not in ids:
            errors.append(f"{s['id']}.{key} aponta para sintoma inexistente '{s[key]}'")

# ---- translation catalogs ----
blob = json.dumps(sint, ensure_ascii=False)
needed = {v.lstrip("@") for v in json.loads(blob).values() if isinstance(v, str) and v.startswith("@")}


def collect_refs(node, acc: set) -> None:
    if isinstance(node, dict):
        for v in node.values():
            collect_refs(v, acc)
    elif isinstance(node, list):
        for v in node:
            collect_refs(v, acc)
    elif isinstance(node, str) and node.startswith("@"):
        acc.add(node[1:])


refs: set = set()
collect_refs(sint, refs)

langs = sorted(glob.glob(os.path.join(HERE, "i18n", "*.json")))
lang_report = []
for path in langs:
    cat = json.load(open(path, encoding="utf-8"))
    # ui.* keys are consumed by build_docs.py, not referenced from the structure
    keys = {k for k in cat if not k.startswith(("_", "ui."))}
    ui_keys = {k for k in cat if k.startswith("ui.")}
    missing = refs - keys
    extra = keys - refs
    name = os.path.basename(path)
    lang_report.append((name, len(keys), len(ui_keys), len(missing), len(extra)))
    for k in sorted(missing)[:5]:
        errors.append(f"{name}: falta a chave '{k}'")
    for k in sorted(extra)[:5]:
        warnings.append(f"{name}: chave orfa '{k}'")

print(f"sintomas           : {len(sint['symptoms'])}")
print(f"referencias        : {checked}")
print(f"chaves de texto    : {len(refs)}")
print(f"idiomas            : {len(langs)}")
for name, n, nui, miss, extra in lang_report:
    status = "ok" if not miss and not extra else f"faltam {miss}, orfas {extra}"
    print(f"   {name:<14} {n:>4} texto + {nui:>3} ui   {status}")
print(f"erros              : {len(errors)}")
for e in errors:
    print("  ERRO ", e)
print(f"avisos             : {len(warnings)}")
for w in warnings:
    print("  aviso", w)

sys.exit(1 if errors else 0)
