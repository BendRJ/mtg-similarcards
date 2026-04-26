"""Generate training pairs from MTG card data for fine-tuning.

Queries the database for cards and builds positive pairs based on
mechanical similarity signals (keywords, colors, creature types,
related cards, functional reprints).

Usage:
    python -m training.generate_training_data \
        --output-path data/training_pairs.jsonl \
        --max-pairs 15000 \
        --seed 42
"""

import argparse
import json
import logging
import random
from pathlib import Path
from typing import Any

from app.config.logging_config import setup_logging
from app.services.vector_service import build_card_text
from database.db import get_cursor

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Database queries
# ---------------------------------------------------------------------------

ALL_CARDS_SQL = """
    SELECT id, oracle_id, name, type_line, oracle_text,
           keywords, colors, color_identity, cmc, all_parts
    FROM cards
    WHERE oracle_text IS NOT NULL
      AND type_line IS NOT NULL
    limit 2000
"""


def load_all_cards() -> list[dict[str, Any]]:
    """Fetch all cards with text fields from the database."""
    with get_cursor() as cur:
        cur.execute(ALL_CARDS_SQL)
        columns = [desc[0] for desc in cur.description] if cur.description else []
        return [dict(zip(columns, row)) for row in cur.fetchall()]

# ---------------------------------------------------------------------------
# Pair generation helpers
# ---------------------------------------------------------------------------

def _parse_subtypes(type_line: str) -> set[str]:
    """Extract creature subtypes from a type_line like 'Creature — Elf Warrior'."""
    if "—" in type_line:
        right = type_line.split("—", 1)[1].strip()
    elif "-" in type_line:
        right = type_line.split("-", 1)[1].strip()
    else:
        return set()
    return {s.strip() for s in right.split() if s.strip()}


def _supertype(type_line: str) -> str:
    """Extract the main card type (Creature, Instant, Sorcery, etc.)."""
    left = type_line.split("—")[0] if "—" in type_line else type_line
    left = left.split("-")[0] if "-" in left else left
    for t in ("Creature", "Instant", "Sorcery", "Enchantment", "Artifact",
              "Planeswalker", "Land", "Battle"):
        if t in left:
            return t
    return "Other"


def _card_text(card: dict[str, Any]) -> str:
    """Build the text representation used for embedding."""
    return build_card_text(card)


Pair = tuple[str, str]  # (sentence1, sentence2)


def pairs_from_oracle_id(cards: list[dict[str, Any]]) -> list[Pair]:
    """Functional reprints: cards sharing the same oracle_id."""
    by_oracle: dict[str, list[dict]] = {}
    for c in cards:
        oid = c.get("oracle_id")
        if oid:
            by_oracle.setdefault(oid, []).append(c)

    pairs: list[Pair] = []
    for group in by_oracle.values():
        if len(group) < 2:
            continue
        # Pick one representative pair per oracle_id to avoid flooding
        a, b = group[0], group[1]
        pairs.append((_card_text(a), _card_text(b)))
    return pairs


def pairs_from_all_parts(cards: list[dict[str, Any]]) -> list[Pair]:
    """Related cards from Scryfall's all_parts (meld, tokens, flip sides)."""
    card_by_id: dict[str, dict] = {c["id"]: c for c in cards}
    seen: set[tuple[str, str]] = set()
    pairs: list[Pair] = []

    for c in cards:
        parts = c.get("all_parts")
        if not parts:
            continue
        if isinstance(parts, str):
            parts = json.loads(parts)
        for part in parts:
            related_id = part.get("id")
            if related_id and related_id != c["id"] and related_id in card_by_id:
                key = tuple(sorted((c["id"], related_id)))
                if key not in seen:
                    seen.add(key)
                    pairs.append((
                        _card_text(c),
                        _card_text(card_by_id[related_id]),
                    ))
    return pairs


def pairs_from_keyword_color_overlap(cards: list[dict[str, Any]]) -> list[Pair]:
    """Cards sharing 2+ keywords AND 1+ color."""
    # Index cards by keyword for efficient lookup
    by_keyword: dict[str, list[int]] = {}
    for i, c in enumerate(cards):
        kws = c.get("keywords") or []
        if isinstance(kws, list) and len(kws) >= 2:
            for kw in kws:
                by_keyword.setdefault(kw, []).append(i)

    seen: set[tuple[int, int]] = set()
    pairs: list[Pair] = []

    for indices in by_keyword.values():
        for x in range(len(indices)):
            for y in range(x + 1, len(indices)):
                i, j = indices[x], indices[y]
                key = (min(i, j), max(i, j))
                if key in seen:
                    continue

                ca, cb = cards[i], cards[j]
                kw_a = set(ca.get("keywords") or [])
                kw_b = set(cb.get("keywords") or [])
                if len(kw_a & kw_b) < 2:
                    continue

                col_a = set(ca.get("colors") or [])
                col_b = set(cb.get("colors") or [])
                if not (col_a & col_b):
                    continue

                seen.add(key)
                pairs.append((_card_text(ca), _card_text(cb)))
    return pairs


def pairs_from_tribal_overlap(cards: list[dict[str, Any]]) -> list[Pair]:
    """Creature type overlap + similar CMC (±1)."""
    creatures = [
        c for c in cards
        if c.get("type_line") and "Creature" in c["type_line"]
    ]

    by_subtype: dict[str, list[int]] = {}
    for i, c in enumerate(creatures):
        for st in _parse_subtypes(c["type_line"]):
            by_subtype.setdefault(st, []).append(i)

    seen: set[tuple[str, str]] = set()
    pairs: list[Pair] = []

    for indices in by_subtype.values():
        for x in range(len(indices)):
            for y in range(x + 1, len(indices)):
                ca, cb = creatures[indices[x]], creatures[indices[y]]
                key = tuple(sorted((ca["id"], cb["id"])))
                if key in seen:
                    continue

                cmc_a = ca.get("cmc") or 0
                cmc_b = cb.get("cmc") or 0
                if abs(cmc_a - cmc_b) > 1:
                    continue

                seen.add(key)
                pairs.append((_card_text(ca), _card_text(cb)))
    return pairs


def pairs_from_cmc_color_type(cards: list[dict[str, Any]]) -> list[Pair]:
    """Same CMC + color identity + card supertype."""
    buckets: dict[tuple, list[int]] = {}
    for i, c in enumerate(cards):
        cmc = c.get("cmc")
        ci = tuple(sorted(c.get("color_identity") or []))
        st = _supertype(c.get("type_line", ""))
        if cmc is not None and ci and st != "Other":
            key = (int(cmc), ci, st)
            buckets.setdefault(key, []).append(i)

    pairs: list[Pair] = []
    seen: set[tuple[int, int]] = set()
    for indices in buckets.values():
        for x in range(len(indices)):
            for y in range(x + 1, len(indices)):
                key = (min(indices[x], indices[y]), max(indices[x], indices[y]))
                if key not in seen:
                    seen.add(key)
                    pairs.append((_card_text(cards[indices[x]]),
                                  _card_text(cards[indices[y]])))
    return pairs


# ---------------------------------------------------------------------------
# Main: assemble, score, and sample pairs
# ---------------------------------------------------------------------------

def score_and_sample_pairs(
    all_pair_sources: dict[str, list[Pair]],
    max_pairs: int,
    seed: int,
) -> list[Pair]:
    """Score, weight, and sample pairs from multiple sources.
    Args:
        all_pair_sources: Dict mapping source name to list of pairs.
            Keys: "oracle_id", "all_parts", "keyword_color",
                  "tribal", "cmc_color_type"
        max_pairs: Target number of pairs to produce.
        seed: Random seed for reproducibility.

    Returns:
        List of (sentence1, sentence2) pairs for training.
    """
    rng = random.Random(seed)

    # Step 1: Define weights per source (higher = more confident signal)
    weights = {
    "oracle_id": 5.0,
    "all_parts": 3.0,
    "keyword_color": 2.0,
    "tribal": 1.5,
    "cmc_color_type": 1.0,
    }

    total_weight = sum(weights.values())
    # express as percentage values
    pct = {k: v / total_weight for k, v in weights.items()}

    # Step 2: Compute allocations, capped by available pairs.
    #   Redistribute leftover slots from exhausted sources.
    allocation: dict[str, int] = {}
    remaining = max_pairs
    exhausted: set[str] = set()

    for source, frac in sorted(pct.items(), key=lambda x: x[1]):
        available = len(all_pair_sources.get(source, []))
        target = int(frac * max_pairs)
        actual = min(target, available)
        allocation[source] = actual
        remaining -= actual
        if actual < target:
            exhausted.add(source)

    # Distribute leftover slots to non-exhausted sources proportionally
    if remaining > 0:
        active = {k: pct[k] for k in weights if k not in exhausted}
        if active:
            active_total = sum(active.values())
            for source in active:
                available = len(all_pair_sources[source])
                bonus = int((active[source] / active_total) * remaining)
                allocation[source] = min(allocation[source] + bonus, available)

    # Step 3: Sample from each source
    final_pairs: list[Pair] = []
    for source, n in allocation.items():
        pairs = all_pair_sources.get(source, [])
        if n >= len(pairs):
            final_pairs.extend(pairs)
        else:
            final_pairs.extend(rng.sample(pairs, n))

    # Step 4: Shuffle and return
    rng.shuffle(final_pairs)
    return final_pairs


def generate_training_data(output_path: Path, max_pairs: int, seed: int) -> int:
    """Generate training pairs and write to JSONL file.

    Returns:
        Number of pairs written.
    """
    logger.info("Loading cards from database...")
    cards = load_all_cards()
    logger.info("Loaded %d cards.", len(cards))

    logger.info("Generating pairs from each source...")
    all_sources: dict[str, list[Pair]] = {}

    all_sources["oracle_id"] = pairs_from_oracle_id(cards)
    logger.info("  oracle_id:      %d pairs", len(all_sources["oracle_id"]))

    all_sources["all_parts"] = pairs_from_all_parts(cards)
    logger.info("  all_parts:      %d pairs", len(all_sources["all_parts"]))

    all_sources["keyword_color"] = pairs_from_keyword_color_overlap(cards)
    logger.info("  keyword_color:  %d pairs", len(all_sources["keyword_color"]))

    all_sources["tribal"] = pairs_from_tribal_overlap(cards)
    logger.info("  tribal:         %d pairs", len(all_sources["tribal"]))

    all_sources["cmc_color_type"] = pairs_from_cmc_color_type(cards)
    logger.info("  cmc_color_type: %d pairs", len(all_sources["cmc_color_type"]))

    total_raw = sum(len(v) for v in all_sources.values())
    logger.info("Total raw pairs: %d", total_raw)

    # Score and sample
    final_pairs = score_and_sample_pairs(all_sources, max_pairs, seed)
    logger.info("Sampled %d pairs for training.", len(final_pairs))

    # Write to JSONL
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        for s1, s2 in final_pairs:
            f.write(json.dumps({"sentence1": s1, "sentence2": s2}) + "\n")

    logger.info("Training pairs written to %s", output_path)
    return len(final_pairs)


def main() -> None:
    """CLI entry point."""
    setup_logging()
    parser = argparse.ArgumentParser(description="Generate MTG training pairs")
    parser.add_argument(
        "--output-path", type=Path, default=Path("data/training_pairs.jsonl"),
        help="Path for output JSONL file",
    )
    parser.add_argument(
        "--max-pairs", type=int, default=15000,
        help="Target number of training pairs",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility",
    )
    args = parser.parse_args()
    generate_training_data(args.output_path, args.max_pairs, args.seed)


if __name__ == "__main__":
    main()
