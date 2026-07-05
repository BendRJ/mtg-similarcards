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
from utils.vector_helper import build_card_text
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
    ORDER BY id
"""


def load_all_cards(max_cards: int | None = None) -> list[dict[str, Any]]:
    """Fetch cards with text fields from the database.

    Args:
        max_cards: Optional cap on the number of cards loaded. Combined with the
            deterministic ``ORDER BY id`` this keeps the loaded universe stable
            across runs (required for reproducible sampling). ``None`` loads all.
    Returns:
        List of dict, e.g.
        [
          {"col1":"row1", "col2":"row2"} -> card1
        , {"col1":"row1", "col2":"row2"} -> card2
        ]
        """
    sql = ALL_CARDS_SQL
    params: tuple = ()
    if max_cards is not None:
        sql += "\n    LIMIT %s"
        params = (max_cards,)
    with get_cursor() as cur:
        cur.execute(sql, params)
        columns = [desc[0] for desc in cur.description] if cur.description else []
        return [dict(zip(columns, row)) for row in cur.fetchall()]

# ---------------------------------------------------------------------------
# Pair generation helpers
# ---------------------------------------------------------------------------

def _parse_subtypes(type_line: str) -> set[str]:
    """Extract subtypes from a type_line (text after the em dash or hyphen).
    Args:
        type_line: MTG card type line (e.g., 'Creature — Elf Warrior')
    Returns:
        Set of individual subtype tokens.
    Examples:
        'Creature — Elf Warrior' → {'Elf', 'Warrior'}
        'Enchantment — Aura' → {'Aura'}
        'Artifact Creature - Golem' → {'Golem'}  (hyphen fallback)
        'Instant' → set()  (no subtypes)
    """
    if "—" in type_line: #em dash (Unicode U+2014) used heavily in mtg cards
        right = type_line.split("—", 1)[1].strip()
    elif "-" in type_line: #regular hyphen
        right = type_line.split("-", 1)[1].strip()
    else:
        return set()
    return {s.strip() for s in right.split() if s.strip()}


def _supertype(type_line: str) -> str:
    """Extract the main card type from a type_line (text before the separator).
    Args:
        type_line: MTG card type line (e.g., 'Creature — Elf Warrior')
    Returns:
        The primary card type category (first match from the type list).
    Examples:
        'Creature — Elf Warrior' → 'Creature'
        'Legendary Creature — Human Wizard' → 'Creature'
        'Instant' → 'Instant'
        'Artifact Creature - Golem' → 'Creature'  (Creature found first)
        'Artifact — Equipment' → 'Artifact'
        'Enchantment — Aura' → 'Enchantment'
        'Unknown Type — Something' → 'Other'
    """
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

# Similarity-signal confidence per source (higher = more trusted positive).
# Ordered by how strongly the signal implies mechanical similarity, not by how
# many pairs the source can produce.
SOURCE_WEIGHTS = {
    "all_parts": 3.0,
    "keyword_color": 3.0,
    "tribal": 2.0,
    "cmc_color_type": 1.0,
}

# Cap on how many bucket members are sampled before pairing, to avoid
# materializing every combination in dense buckets. A cap of k yields at most
# k*(k-1)//2 pairs per bucket (10 -> 45).
MAX_MEMBERS_PER_BUCKET = 10


def _sample_index_pairs(
    indices: list[int], rng: random.Random
) -> list[tuple[int, int]]:
    """Choose which index pairs to emit for one similarity bucket.

    ``indices`` are the member positions of a single bucket (e.g. all cards
    sharing a creature subtype). A full pairing is ``len * (len - 1) / 2`` pairs,
    which explodes for dense buckets. To bound both work and output, at most
    ``MAX_MEMBERS_PER_BUCKET`` members are randomly sampled and then fully paired
    (yielding up to ``k*(k-1)//2`` unordered ``(i, j)`` pairs, ``i != j``);
    callers still apply their own predicate/dedup afterwards.

    Determinism: use only ``rng`` for any randomness so runs stay reproducible.
    """
    cap = MAX_MEMBERS_PER_BUCKET
    indices_samples = rng.sample(indices, min(cap, len(indices)))
    result = []
    for x in range(len(indices_samples)):
        for y in range(x + 1, len(indices_samples)):
            result.append((indices_samples[x], indices_samples[y]))

    return result




def pairs_from_all_parts(cards: list[dict[str, Any]]) -> list[Pair]:
    """Pair cards linked by Scryfall's ``all_parts`` (meld, flip sides, combos).

    Signal (weight 3.0): ``all_parts`` is an editorially curated list of cards
    Scryfall considers related to a given card — meld halves, transform faces,
    tokens created, and named combo pieces. Curated relationships are the most
    trustworthy positive signal, so this source carries a high weight.

    Algorithm: build a Scryfall-id lookup, then for each card walk its parts and
    emit a pair for every related card that is (a) not itself and (b) also in the
    loaded set. Tokens usually aren't stored as cards, so they drop out via (b).
    Pairs are deduplicated by sorted id so A→B and B→A count once.

    Args:
        cards: Card dicts; ``id`` is the Scryfall UUID that ``all_parts`` refers
            to, and ``all_parts`` is JSONB (may arrive as a JSON string).

    Returns:
        List of (sentence1, sentence2) card-text pairs.
    """
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


def pairs_from_keyword_color_overlap(
    cards: list[dict[str, Any]], rng: random.Random
) -> list[Pair]:
    """Pair cards sharing 2+ keywords AND 1+ color.

    Signal (weight 3.0): cards with several mechanics in common (e.g. both
    Flying + Vigilance) that also overlap in color tend to fill the same role.
    Requiring two shared keywords and a shared color makes this a strong signal.

    Algorithm ("index wide, verify narrow"): bucket cards by each keyword — but
    only cards with >=2 keywords, since they're the only ones that *can* share
    two. Within a bucket, candidate pairs are proposed by ``_sample_index_pairs``
    (capping dense buckets); each candidate is then verified for >=2 shared
    keywords and >=1 shared color. ``seen`` dedups pairs that appear in several
    keyword buckets.

    Args:
        cards: Card dicts with ``keywords`` and ``colors`` list fields.
        rng: Seeded RNG, forwarded to ``_sample_index_pairs`` for reproducibility.

    Returns:
        List of (sentence1, sentence2) card-text pairs.
    """
    # Index cards by keyword for efficient lookup
    by_keyword: dict[str, list[int]] = {}
    for i, c in enumerate(cards):
        kws = c.get("keywords") or []
        if isinstance(kws, list) and len(kws) >= 2:
            for kw in kws:
                if kw not in by_keyword:
                    by_keyword[kw] = []
                by_keyword[kw].append(i)

    seen: set[tuple[int, int]] = set()
    pairs: list[Pair] = []

    for indices in by_keyword.values():
        for i, j in _sample_index_pairs(indices, rng):
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


def pairs_from_tribal_overlap(
    cards: list[dict[str, Any]], rng: random.Random
) -> list[Pair]:
    """Pair creatures sharing a subtype with similar mana value (CMC ±1).

    Signal (weight 2.0): creatures of the same tribe (Elf, Goblin, ...) at a
    comparable cost occupy a similar deck slot. Tribe alone is loose, so the
    CMC-within-1 constraint tightens it. Medium weight — weaker than shared
    mechanics but stronger than pure statistical bucketing.

    Algorithm: restrict to creatures, bucket by subtype (from ``_parse_subtypes``
    on the type line), propose candidate pairs per bucket via
    ``_sample_index_pairs``, then keep only those with ``abs(cmc_a - cmc_b) <= 1``.
    Dedup is keyed on card ids because a creature belongs to multiple subtype
    buckets (e.g. "Elf Warrior").

    Args:
        cards: Card dicts with ``type_line`` and ``cmc`` fields.
        rng: Seeded RNG, forwarded to ``_sample_index_pairs`` for reproducibility.

    Returns:
        List of (sentence1, sentence2) card-text pairs.
    """
    creatures = [
        c for c in cards
        if c.get("type_line") and "Creature" in c["type_line"]
    ]

    by_subtype: dict[str, list[int]] = {}
    # {
    # "Elf": [0, 15, 42, ...],      # indices of all Elf cards
    # "Warrior": [0, 23, 58, ...],   # indices of all Warrior cards
    # "Golem": [10, 31, ...],        # indices of all Golem cards
    # }
    # sorted(): _parse_subtypes returns a set, whose iteration order is
    # randomized per process (PYTHONHASHSEED). Sorting fixes bucket insertion
    # order so the shared rng is consumed identically across runs.
    for i, c in enumerate(creatures):
        for st in sorted(_parse_subtypes(c["type_line"])):
            if st not in by_subtype:
                by_subtype[st] = []
            by_subtype[st].append(i)

    seen: set[tuple[str, str]] = set()
    pairs: list[Pair] = []

    for indices in by_subtype.values():
        for i, j in _sample_index_pairs(indices, rng):
            ca, cb = creatures[i], creatures[j]
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


def pairs_from_cmc_color_type(
    cards: list[dict[str, Any]], rng: random.Random
) -> list[Pair]:
    """Pair cards with identical (CMC, color identity, supertype).

    Signal (weight 1.0, weakest): two cards that cost the same, share a color
    identity, and are the same broad type (Creature, Instant, ...) are
    *structurally* alike but may play very differently (a lifegain 3-drop vs. an
    aggressive one). Low weight, and this is the noisiest, highest-volume source
    — it exists mainly to broaden coverage, not to teach fine distinctions.

    Algorithm: bucket by the exact ``(int(cmc), sorted color_identity,
    supertype)`` key, skipping cards with no color identity or an "Other"
    supertype, then pair within each bucket via ``_sample_index_pairs``. No
    extra predicate — bucket membership is the whole signal.

    Args:
        cards: Card dicts with ``cmc``, ``color_identity``, and ``type_line``.
        rng: Seeded RNG, forwarded to ``_sample_index_pairs`` for reproducibility.

    Returns:
        List of (sentence1, sentence2) card-text pairs.
    """
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
        for i, j in _sample_index_pairs(indices, rng):
            key = (min(i, j), max(i, j))
            if key not in seen:
                seen.add(key)
                pairs.append((_card_text(cards[i]), _card_text(cards[j])))
    return pairs


# ---------------------------------------------------------------------------
# Main: assemble, score, and sample pairs
# ---------------------------------------------------------------------------

def dedup_across_sources(
    all_pair_sources: dict[str, list[Pair]],
) -> dict[str, list[Pair]]:
    """Drop degenerate and cross-source-duplicate pairs.

    Two cleanups, both keyed on the pair's two card texts:

    - **Self-identical pairs** (``sentence1 == sentence2``) are dropped. Distinct
      printings of the same card (same ``oracle_id``, different ``id``) share
      type/CMC/color/keywords, so they re-collide inside the mechanical sources
      and produce identical text — which teaches nothing under MNRL.
    - **Duplicates across sources** (a pair qualifying under both e.g. tribal and
      cmc_color_type) are kept only once, assigned to the highest-weight source
      that produced it. Repeated positives become false negatives under MNRL.

    Args:
        all_pair_sources: Dict mapping source name to its list of pairs.

    Returns:
        A new dict with the same keys, each surviving pair in exactly one source.
    """
    seen: set[frozenset[str]] = set()
    deduped: dict[str, list[Pair]] = {name: [] for name in all_pair_sources}

    # Highest-weight sources claim pairs first.
    ordered = sorted(
        all_pair_sources,
        key=lambda name: SOURCE_WEIGHTS.get(name, 0.0),
        reverse=True,
    )
    for name in ordered:
        for s1, s2 in all_pair_sources[name]:
            key = frozenset((s1, s2))
            # A 1-element frozenset means s1 == s2 (identical card text).
            if len(key) < 2 or key in seen:
                continue
            seen.add(key)
            deduped[name].append((s1, s2))
    return deduped


def score_and_sample_pairs(
    all_pair_sources: dict[str, list[Pair]],
    max_pairs: int,
    seed: int,
) -> list[Pair]:
    """Score, weight, and sample pairs from multiple sources.
    Args:
        all_pair_sources: Dict mapping source name to list of pairs.
            Keys: "all_parts", "keyword_color", "tribal", "cmc_color_type"
        max_pairs: Target number of pairs to produce.
        seed: Random seed for reproducibility.

    Returns:
        List of (sentence1, sentence2) pairs for training.
    """
    rng = random.Random(seed)

    # Step 1: Define weights per source (higher = more confident signal).
    # Ordered by similarity-signal quality rather than raw pair volume.
    weights = SOURCE_WEIGHTS

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


def generate_training_data(
    output_path: Path, max_pairs: int, seed: int, max_cards: int | None = None
) -> int:
    """Generate training pairs and write to JSONL file.

    Returns:
        Number of pairs written.
    """
    rng = random.Random(seed)

    logger.info("Loading cards from database...")
    cards = load_all_cards(max_cards)
    logger.info("Loaded %d cards.", len(cards))

    logger.info("Generating pairs from each source...")
    all_sources: dict[str, list[Pair]] = {}

    all_sources["all_parts"] = pairs_from_all_parts(cards)
    logger.info("  all_parts:      %d pairs", len(all_sources["all_parts"]))

    all_sources["keyword_color"] = pairs_from_keyword_color_overlap(cards, rng)
    logger.info("  keyword_color:  %d pairs", len(all_sources["keyword_color"]))

    all_sources["tribal"] = pairs_from_tribal_overlap(cards, rng)
    logger.info("  tribal:         %d pairs", len(all_sources["tribal"]))

    all_sources["cmc_color_type"] = pairs_from_cmc_color_type(cards, rng)
    logger.info("  cmc_color_type: %d pairs", len(all_sources["cmc_color_type"]))

    total_raw = sum(len(v) for v in all_sources.values())
    logger.info("Total raw pairs: %d", total_raw)

    # Drop pairs that appear in more than one source, keeping the highest-weight
    # assignment. Duplicate positives become false negatives under MNRL.
    all_sources = dedup_across_sources(all_sources)
    total_dedup = sum(len(v) for v in all_sources.values())
    logger.info("Total pairs after cross-source dedup: %d", total_dedup)

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
    parser.add_argument(
        "--max-cards", type=int, default=None,
        help="Cap on cards loaded from the DB (default: all). Loaded in id order.",
    )
    args = parser.parse_args()
    generate_training_data(
        args.output_path, args.max_pairs, args.seed, args.max_cards
    )


if __name__ == "__main__":
    main()
