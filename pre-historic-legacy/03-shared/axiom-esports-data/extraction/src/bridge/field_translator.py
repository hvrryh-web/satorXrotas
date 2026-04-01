"""
Field Translator — Source-agnostic field name normalisation.

Problem
-------
Every data source uses its own field names for the same metric:

    VLR.gg:     "kast"       → KCRITR: "kast_pct"
    Liquipedia: "kast_percentage"
    HLTV:       "kast"         (same accident, different scale)
    GRID:       "kastPercent"

    VLR.gg:     "hs_pct"     → KCRITR: "headshot_pct"
    Liquipedia: "headshot_percentage"
    HLTV:       "hs_percent"
    GRID:       "headshotPercent"

Without a translation layer every consumer must know every source schema.
A schema change in one source breaks all consumers.

Solution
--------
``FieldTranslator`` maintains a two-level lookup:

    source_name  →  source_field_name  →  canonical_kcritr_name

Callers pass a ``source`` identifier and a raw field dict; they receive a
new dict keyed by KCRITR canonical names.  Unmapped fields are collected
into ``unmapped`` for schema-drift detection.

The translation table is loaded from
``config/datapoint_naming.json → field_translation_table.source_mappings``.
New sources are registered there without touching Python code.

Conflict detection
------------------
When a translated dict already contains a canonical key and a second source
provides a different value for it, ``FieldTranslator`` records a
``FieldConflict`` and applies the priority order from the config
(vlr_gg > grid > liquipedia > hltv).
"""
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_NAMING_PATH = (
    Path(__file__).parent.parent.parent.parent / "config" / "datapoint_naming.json"
)


def _load_naming() -> dict:
    if _NAMING_PATH.exists():
        return json.loads(_NAMING_PATH.read_text())
    logger.warning("datapoint_naming.json not found — FieldTranslator using empty maps")
    return {}


_NAMING = _load_naming()
_FTT = _NAMING.get("field_translation_table", {})

# Source priority (index 0 = highest priority)
_SOURCE_PRIORITY: list[str] = (
    _FTT.get("conflict_resolution", {}).get("primary_source_priority", [])
    or ["vlr_gg", "grid", "liquipedia", "hltv"]
)


@dataclass
class FieldConflict:
    """
    Recorded when two sources provide different values for the same canonical field.

    Attributes
    ----------
    canonical_field:   The KCRITR field where the conflict occurred (e.g. "acs")
    source_winner:     Which source's value was kept (higher priority)
    value_winner:      The value that was kept
    source_loser:      Which source's value was discarded
    value_loser:       The discarded value
    """
    canonical_field: str
    source_winner: str
    value_winner: Any
    source_loser: str
    value_loser: Any


class FieldTranslator:
    """
    Translates a raw dict from any known source into canonical KCRITR field names.

    Usage
    -----
    translator = FieldTranslator()

    # Translate a VLR.gg row
    canonical, unmapped = translator.translate("vlr_gg", {"player": "TenZ", "kast": "75%"})
    # canonical == {"name": "TenZ", "kast_pct": "75%"}

    # Translate and merge a second source into the same record
    canonical2, conflicts = translator.translate_and_merge(
        existing=canonical,
        existing_source="vlr_gg",
        incoming={"player_name": "TenZ", "kast_percentage": "74%"},
        incoming_source="liquipedia",
    )
    # conflicts == [FieldConflict(canonical_field="kast_pct", ...)]
    """

    def __init__(self) -> None:
        # Load all source maps from config
        self._source_maps: dict[str, dict[str, Optional[str]]] = {
            src: mapping
            for src, mapping in _FTT.get("source_mappings", {}).items()
            if not src.startswith("_")
        }
        self._canonical_fields: set[str] = set(
            _FTT.get("canonical_fields", {}).keys()
        )

    # ------------------------------------------------------------------
    # Primary translation interface
    # ------------------------------------------------------------------

    def translate(
        self, source: str, raw: dict[str, Any]
    ) -> tuple[dict[str, Any], list[str]]:
        """
        Translate a raw dict from ``source`` into canonical KCRITR field names.

        Returns
        -------
        (canonical_dict, unmapped_fields)
            canonical_dict:   Keys are KCRITR canonical field names.
            unmapped_fields:  Source field names that had no translation entry.
                              Non-empty means possible schema drift — log and alert.
        """
        mapping = self._source_maps.get(source, {})
        if not mapping:
            logger.warning(
                "No field mapping registered for source '%s'. "
                "Register it in config/datapoint_naming.json "
                "→ field_translation_table.source_mappings",
                source,
            )

        canonical: dict[str, Any] = {}
        unmapped: list[str] = []

        for raw_key, raw_value in raw.items():
            if raw_key.startswith("_"):
                continue  # Skip comment keys
            if raw_key not in mapping:
                unmapped.append(raw_key)
                continue
            canonical_key = mapping[raw_key]
            if canonical_key is None:
                # Explicitly mapped to null — field has no canonical equivalent
                continue
            canonical[canonical_key] = raw_value

        if unmapped:
            logger.warning(
                "Source '%s' has %d unmapped field(s) — possible schema drift: %s",
                source, len(unmapped), unmapped,
            )

        return canonical, unmapped

    def translate_and_merge(
        self,
        existing: dict[str, Any],
        existing_source: str,
        incoming: dict[str, Any],
        incoming_source: str,
    ) -> tuple[dict[str, Any], list[FieldConflict]]:
        """
        Translate ``incoming`` from ``incoming_source`` and merge into ``existing``.

        When a canonical field already has a value in ``existing`` and
        ``incoming`` provides a different value for the same field, the
        higher-priority source wins (per ``primary_source_priority``).

        Returns
        -------
        (merged_dict, conflicts)
        """
        incoming_canonical, _unmapped = self.translate(incoming_source, incoming)
        conflicts: list[FieldConflict] = []
        merged = dict(existing)

        winner = self._higher_priority(existing_source, incoming_source)

        for key, inc_val in incoming_canonical.items():
            if key not in merged:
                merged[key] = inc_val
                continue

            existing_val = merged[key]
            if existing_val == inc_val or inc_val is None:
                continue  # No conflict or incoming is empty

            # Values differ — apply priority rule
            if winner == existing_source:
                conflicts.append(FieldConflict(
                    canonical_field=key,
                    source_winner=existing_source,
                    value_winner=existing_val,
                    source_loser=incoming_source,
                    value_loser=inc_val,
                ))
                # Keep existing value (already in merged)
            else:
                conflicts.append(FieldConflict(
                    canonical_field=key,
                    source_winner=incoming_source,
                    value_winner=inc_val,
                    source_loser=existing_source,
                    value_loser=existing_val,
                ))
                merged[key] = inc_val  # Replace with higher-priority value

        for conflict in conflicts:
            logger.info(
                "Field conflict on '%s': %s=%r kept over %s=%r",
                conflict.canonical_field,
                conflict.source_winner, conflict.value_winner,
                conflict.source_loser, conflict.value_loser,
            )

        return merged, conflicts

    # ------------------------------------------------------------------
    # Reverse lookup — canonical → source field name
    # ------------------------------------------------------------------

    def canonical_to_source(self, source: str, canonical_key: str) -> Optional[str]:
        """
        Return the source-specific field name for a canonical key.
        Useful for generating source-targeted queries.
        """
        mapping = self._source_maps.get(source, {})
        for src_key, canon in mapping.items():
            if canon == canonical_key:
                return src_key
        return None

    def known_sources(self) -> list[str]:
        """All registered source identifiers."""
        return list(self._source_maps.keys())

    def known_canonical_fields(self) -> list[str]:
        """All KCRITR canonical field names from the config."""
        return sorted(self._canonical_fields)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _higher_priority(self, source_a: str, source_b: str) -> str:
        """Return whichever source has higher priority in the config."""
        try:
            idx_a = _SOURCE_PRIORITY.index(source_a)
        except ValueError:
            idx_a = 999
        try:
            idx_b = _SOURCE_PRIORITY.index(source_b)
        except ValueError:
            idx_b = 999
        return source_a if idx_a <= idx_b else source_b
