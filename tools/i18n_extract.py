"""One-time normalisation of sintomas.json into a language-neutral structure + text catalog.

The reference started life as a single Portuguese document. For a repository that expects
contributions in several languages that is a dead end: field names, enum values and prose
were all mixed together.

This splits it in two and normalises what stays:

    sintomas.json     structure only — English field names, English enum values, component
                      and parameter references, deltas, frequencies. No prose.
    i18n/pt-BR.json   every human-readable string, under a stable dotted key.

Text values in the structure become "@key" references that `build_docs.py` resolves against
whichever language file is requested.

Run once against the original Portuguese file:

    python i18n_extract.py --from sintomas.json.orig
"""

from __future__ import annotations

import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
I18N_DIR = os.path.join(HERE, "i18n")
OUT = os.path.join(HERE, "sintomas.json")

FIELDS = {
    "versao": "version", "descricao": "description", "ordem_diagnostico": "diagnostic_order",
    "bandas_hz": "bands_hz", "sintomas": "symptoms", "familia": "family",
    "prioridade": "priority", "queixas": "complaints", "medicao": "measurement",
    "metrica": "metric", "condicao": "condition", "confianca": "confidence",
    "ignorar_se": "ignore_if", "teste_ouvido": "ear_test", "causas": "causes",
    "causa": "cause", "acoes": "actions", "ordem": "order", "verificar": "check",
    "fora_do_guitar_rig": "outside_guitar_rig", "acao_humana": "user_action",
    "armadilhas": "pitfalls", "causas_falsas": "false_causes",
    "nao_confundir_com": "not_to_confuse_with", "checar_antes": "check_first",
    "distinguir_de": "distinguish_from", "contexto": "context",
    "rede_seguranca": "safety_net", "componente": "component", "valor": "value",
    "nota": "note", "se": "if", "compensar": "compensate", "alvo_hz": "target_hz",
    "varrer_hz": "sweep_hz", "params_relacionados": "related_params",
    "alternar": "toggle", "repetir_ate": "repeat_until",
    "amp_params_comuns": "common_amp_params", "excecoes_amp": "amp_exceptions",
    "sintoma": "symptom", "onde": "where",
}

FAMILY = {"nivel": "level", "ruido": "noise", "tom": "tone",
          "dinamica": "dynamics", "espaco": "space"}
CONFIDENCE = {"alta": "high", "media": "medium", "baixa": "low"}
Q = {"alto": "narrow", "estreito": "narrow", "medio": "medium",
     "medio-estreito": "medium-narrow", "largo": "wide"}
BANDS = {"subgrave": "sub", "peso": "weight", "corpo": "body", "lama": "mud",
         "caixa": "box", "definicao": "definition", "presenca": "presence",
         "ataque": "attack", "brilho": "brightness", "ar": "air"}

TEXT = {"description", "ear_test", "context", "cause", "user_action", "order", "note",
        "if", "symptom", "where", "condition", "metric", "repeat_until"}
TEXT_LIST = {"complaints", "pitfalls", "false_causes"}


def norm(node, path: str, strings: dict):
    if isinstance(node, dict):
        out = {}
        for raw_k, v in node.items():
            k = FIELDS.get(raw_k, raw_k)
            p = f"{path}.{k}" if path else k
            if k in TEXT and isinstance(v, str):
                strings[p] = v
                out[k] = f"@{p}"
            elif k in TEXT_LIST and isinstance(v, list):
                strings[p] = v
                out[k] = f"@{p}"
            elif k == "distinguish_from" and isinstance(v, dict):
                strings[p] = v
                out[k] = f"@{p}"
            elif k == "family":
                out[k] = FAMILY.get(v, v)
            elif k == "confidence":
                out[k] = CONFIDENCE.get(v, v)
            elif k == "q":
                out[k] = Q.get(v, v)
            elif k == "check" and isinstance(v, list):
                out[k] = v                      # component names, not prose
            else:
                out[k] = norm(v, p, strings)
        return out
    if isinstance(node, list):
        return [norm(v, f"{path}.{i}", strings) for i, v in enumerate(node)]
    return node


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", default=os.path.join(HERE, "sintomas.json.orig"))
    args = ap.parse_args()

    data = json.load(open(args.src, encoding="utf-8"))
    strings: dict = {}
    out: dict = {}

    for raw_k, v in data.items():
        k = FIELDS.get(raw_k, raw_k)
        if k == "description":
            strings["description"] = v
            out[k] = "@description"
        elif k == "diagnostic_order":
            out[k] = [FAMILY.get(x, x) for x in v]
        elif k == "bands_hz":
            out[k] = {BANDS.get(bk, bk): bv for bk, bv in v.items()}
        elif k == "symptoms":
            # key each symptom by its id so keys survive reordering
            out[k] = []
            for s in v:
                sid = s["id"]
                normed = norm(s, f"symptoms.{sid}", strings)
                out[k].append(normed)
        else:
            out[k] = norm(v, k, strings)

    os.makedirs(I18N_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    with open(os.path.join(I18N_DIR, "pt-BR.json"), "w", encoding="utf-8") as fh:
        json.dump({"_lang": "pt-BR", "_name": "Português (Brasil)", **strings},
                  fh, indent=2, ensure_ascii=False)

    print(f"estrutura : sintomas.json  ({len(out['symptoms'])} sintomas)")
    print(f"textos    : {len(strings)} chaves -> i18n/pt-BR.json")
    leftover = [k for k in json.dumps(out, ensure_ascii=False).split('"')
                if any(ch in k for ch in "áàâãéêíóôõúçÁÂÃÉÊÍÓÔÕÚÇ")]
    print(f"acentos remanescentes na estrutura: {sorted(set(leftover)) or 'nenhum'}")


if __name__ == "__main__":
    main()
