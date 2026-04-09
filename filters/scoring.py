#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Rule-based scoring for paper relevance
#

import re


DEFAULT_SCORING_CONFIG = {
    "direct_exclusions": [
        "Author Correction",
        "Publisher Correction",
        "Corrigendum",
        "Erratum",
        "Retraction",
    ],
    "groups": [
        {
            "name": "photo_core",
            "weight": 3,
            "terms": ["PDT", "PACT"],
            "label_map": {"PDT": "PDT", "PACT": "PACT"},
        },
        {
            "name": "photo_support",
            "weight": 2,
            "terms": [
                "photodynamic",
                "photoactivated",
                "photosensitizer",
                "photosensitiser",
                "phototoxicity",
                "singlet oxygen",
                "ROS",
                "reactive oxygen species",
                "visible light",
                "NIR",
            ],
            "label_map": {
                "photoactivated": "photoactivated",
                "photodynamic": "photodynamic",
                "photosensitizer": "photosensitizer",
                "photosensitiser": "photosensitiser",
                "phototoxicity": "phototoxicity",
                "singlet oxygen": "singlet oxygen",
                "ROS": "ROS",
                "reactive oxygen species": "ROS",
                "visible light": "visible light",
                "NIR": "NIR",
            },
        },
        {
            "name": "therapy",
            "weight": 2,
            "terms": [
                "anticancer",
                "cancer",
                "tumor",
                "tumour",
                "cytotoxicity",
                "cytotoxic",
                "apoptosis",
            ],
            "label_map": {
                "anticancer": "anticancer",
                "cancer": "cancer",
                "tumor": "tumor",
                "tumour": "tumour",
                "cytotoxicity": "cytotoxicity",
                "cytotoxic": "cytotoxic",
                "apoptosis": "apoptosis",
            },
        },
        {
            "name": "bio_context",
            "weight": 1,
            "terms": ["cell line", "in vitro", "in vivo"],
            "label_map": {
                "cell line": "cell line",
                "in vitro": "in vitro",
                "in vivo": "in vivo",
            },
        },
        {
            "name": "chemistry",
            "weight": 1,
            "terms": [
                "coordination complex",
                "metal complex",
                "organometallic",
                "polypyridyl",
            ],
            "label_map": {
                "coordination complex": "coordination complex",
                "metal complex": "metal complex",
                "organometallic": "organometallic",
                "polypyridyl": "polypyridyl",
            },
        },
        {
            "name": "metals",
            "weight": 2,
            "terms": ["ruthenium", "iridium", "osmium", "platinum", "rhenium"],
            "label_map": {
                "ruthenium": "Ru",
                "iridium": "Ir",
                "osmium": "Os",
                "platinum": "Pt",
                "rhenium": "Re",
            },
        },
        {
            "name": "photocatalysis_negative",
            "weight": -3,
            "terms": [
                "photocatalysis",
                "photocatalyst",
                "hydrogen evolution",
                "water splitting",
                "CO2 reduction",
                "pollutant degradation",
                "environmental remediation",
                "dye degradation",
            ],
            "label_map": {
                "photocatalysis": "photocatalysis",
                "photocatalyst": "photocatalyst",
                "hydrogen evolution": "hydrogen evolution",
                "water splitting": "water splitting",
                "CO2 reduction": "CO2 reduction",
                "pollutant degradation": "pollutant degradation",
                "environmental remediation": "environmental remediation",
                "dye degradation": "dye degradation",
            },
        },
        {
            "name": "surface_negative",
            "weight": -2,
            "terms": [
                "surface",
                "surfaces",
                "surface chemistry",
                "surface modification",
                "surface functionalization",
                "interface",
                "interfacial",
                "adsorption",
                "heterogeneous",
                "substrate",
                "electrode",
                "film",
                "thin film",
            ],
            "label_map": {
                "surface": "surface",
                "surfaces": "surfaces",
                "surface chemistry": "surface chemistry",
                "surface modification": "surface modification",
                "surface functionalization": "surface functionalization",
                "interface": "interface",
                "interfacial": "interfacial",
                "adsorption": "adsorption",
                "heterogeneous": "heterogeneous",
                "substrate": "substrate",
                "electrode": "electrode",
                "film": "film",
                "thin film": "thin film",
            },
            "requires_absence_of": ["therapy_context"],
        },
        {
            "name": "weak_negative",
            "weight": -1,
            "terms": ["sensor", "detection", "imaging", "environmental"],
            "label_map": {
                "sensor": "sensor",
                "detection": "detection",
                "imaging": "imaging",
                "environmental": "environmental",
            },
            "requires_absence_of": ["therapy_context"],
        },
    ],
    "contexts": [
        {
            "name": "therapy_context",
            "terms": [
                "PDT",
                "PACT",
                "photodynamic",
                "photoactivated",
                "phototoxicity",
                "cytotoxicity",
                "cytotoxic",
                "anticancer",
                "cancer",
                "tumor",
                "tumour",
                "cell line",
                "in vitro",
                "in vivo",
                "apoptosis",
            ],
        }
    ],
}


class RuleBasedScorer:
    def __init__(self, scoring_config=None):
        self.config = scoring_config or DEFAULT_SCORING_CONFIG
        self.direct_exclusion_regexes = self._compile_direct_exclusions(
            self.config.get("direct_exclusions", [])
        )
        self.contexts = self._compile_contexts(self.config.get("contexts", []))
        self.groups = self._compile_groups(self.config.get("groups", []))

    def _compile_direct_exclusions(self, terms):
        return [self._compile_term(term) for term in terms]

    def _compile_contexts(self, contexts):
        compiled = {}
        for context in contexts:
            name = context.get("name")
            terms = context.get("terms", [])
            if not name or not terms:
                continue
            compiled[name] = {
                "name": name,
                "regexes": [self._compile_term(term) for term in terms],
            }
        return compiled

    def _compile_groups(self, groups):
        compiled = []
        for group in groups:
            terms = group.get("terms", [])
            if not terms:
                continue
            compiled.append(
                {
                    "name": group.get("name", "unnamed"),
                    "weight": group.get("weight", 0),
                    "regexes": {term: self._compile_term(term) for term in terms},
                    "label_map": group.get("label_map", {}),
                    "requires_absence_of": group.get("requires_absence_of", []),
                }
            )
        return compiled

    def _compile_term(self, term):
        escaped = re.escape(term)
        pattern = r"\b" + escaped.replace(r"\ ", r"\s+") + r"\b"
        return re.compile(pattern, re.IGNORECASE)

    def _entry_text(self, entry):
        title = getattr(entry, "title", "") or ""
        summary = entry.get("summary", "") or ""
        return f"{title} {summary}"

    def is_directly_excluded(self, entry):
        title = getattr(entry, "title", "") or ""
        return any(regex.search(title) for regex in self.direct_exclusion_regexes)

    def score_entry(self, entry):
        text = self._entry_text(entry)
        active_contexts = self._detect_contexts(text)
        reasons = []
        matched_terms = []
        score = 0

        for group in self.groups:
            if not self._group_is_applicable(group, active_contexts):
                continue

            matches = self._find_matches(group, text)
            if not matches:
                continue

            score += group["weight"] * len(matches)
            for match in matches:
                label = group["label_map"].get(match, match)
                sign = "+" if group["weight"] > 0 else "-"
                reasons.append(f"{sign}{label}")
                matched_terms.append(label)

        return {
            "score": score,
            "reasons": reasons,
            "matched_terms": matched_terms,
            "contexts": sorted(active_contexts),
            "excluded": self.is_directly_excluded(entry),
        }

    def _detect_contexts(self, text):
        active = set()
        for name, context in self.contexts.items():
            if any(regex.search(text) for regex in context["regexes"]):
                active.add(name)
        return active

    def _group_is_applicable(self, group, active_contexts):
        required_absence = group.get("requires_absence_of", [])
        return not any(context in active_contexts for context in required_absence)

    def _find_matches(self, group, text):
        matches = []
        for term, regex in group["regexes"].items():
            if regex.search(text):
                matches.append(term)
        return matches

    def sort_messages(self, messages):
        return sorted(messages, key=lambda message: message.get("score", 0), reverse=True)
