"""Preview a sample of generated training pairs per source.

Usage:
    python -m scripts.preview_training_pairs [--sample 5] [--seed 42]
"""

import argparse
import random
import textwrap

from app.config.logging_config import setup_logging
from training.generate_training_data import (
    dedup_across_sources,
    load_all_cards,
    pairs_from_all_parts,
    pairs_from_cmc_color_type,
    pairs_from_keyword_color_overlap,
    pairs_from_tribal_overlap,
    score_and_sample_pairs,
)


def preview(sample_per_source: int, seed: int) -> None:
    setup_logging()
    cards = load_all_cards()
    print(f"Loaded {len(cards)} cards\n")

    rng = random.Random(seed)

    sources = {
        "all_parts": pairs_from_all_parts(cards),
        "keyword_color": pairs_from_keyword_color_overlap(cards, rng),
        "tribal": pairs_from_tribal_overlap(cards, rng),
        "cmc_color_type": pairs_from_cmc_color_type(cards, rng),
    }
    sources = dedup_across_sources(sources)

    for name, pairs in sources.items():
        print(f"{'=' * 60}")
        print(f"  {name}  ({len(pairs)} pairs)")
        print(f"{'=' * 60}")
        shown = rng.sample(pairs, min(sample_per_source, len(pairs))) if pairs else []
        for i, (s1, s2) in enumerate(shown, 1):
            print(f"\n  Pair {i}:")
            print(textwrap.indent(s1, "    A: ", lambda _: True))
            print(textwrap.indent(s2, "    B: ", lambda _: True))
        if not pairs:
            print("  (no pairs)")
        print()

    # Also show final sampled set stats
    final = score_and_sample_pairs(sources, max_pairs=100, seed=seed)
    print(f"{'=' * 60}")
    print(f"  score_and_sample_pairs → {len(final)} pairs (requested 100)")
    print(f"{'=' * 60}")
    sample = rng.sample(final, min(3, len(final))) if final else []
    for i, (s1, s2) in enumerate(sample, 1):
        print(f"\n  Final sample {i}:")
        print(textwrap.indent(s1, "    A: ", lambda _: True))
        print(textwrap.indent(s2, "    B: ", lambda _: True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preview training pairs")
    parser.add_argument("--sample", type=int, default=5, help="Pairs to show per source")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    preview(args.sample, args.seed)
