# Training: Fine-Tuning SentenceTransformer for MTG Card Similarity

## Why Fine-Tune?

The pre-trained `all-MiniLM-L6-v2` model understands general English semantics but not MTG-specific relationships. Fine-tuning teaches it that cards sharing keywords like "Flying + Haste" are mechanically related, without losing its general language understanding.

## Loss Function Comparison

| Criteria | CosineSimilarityLoss | TripletLoss | MultipleNegativesRankingLoss |
|---|---|---|---|
| **Training data required** | Pairs + float similarity score (0.0-1.0) | (anchor, positive, negative) triplets | Only positive pairs |
| **Negative mining** | Not needed (similarity is graded) | Must explicitly define negatives | Automatic via in-batch negatives |
| **Batch size impact** | No effect on loss quality | No effect on loss quality | Larger batch = better negatives for free |
| **Best when** | You have graded similarity labels | You can reliably mine hard negatives | Negatives are hard to define explicitly |
| **Data prep effort** | High - need meaningful float scores | High - need good negative selection | Low - just positive pairs |

### Why We Chose MultipleNegativesRankingLoss (MNRL)

**The core problem:** Defining what makes two MTG cards "not similar" is surprisingly hard. A red burn spell and a blue counterspell seem different, but in a Jeskai control deck they're natural partners. Manually creating negative pairs would bake in assumptions about what "dissimilar" means.

**How MNRL solves this:** Given a batch of 64 positive pairs, each card's match is the one you provided. The other 63 cards in the batch automatically serve as negatives. This means:

- No manual negative mining needed
- Larger batch sizes naturally provide harder, more diverse negatives
- The model learns from a broad contrast signal without our bias about what "different" means

**Why not CosineSimilarityLoss?** We'd need to assign a float similarity score (e.g., 0.7) to each pair. For MTG cards, this is subjective and hard to calibrate. Is "shares 2 keywords" a 0.6 or a 0.8? MNRL avoids this entirely.

**Why not TripletLoss?** Triplet mining is expensive and brittle. You need to find negatives that are "hard enough" to be informative but not so similar they confuse the model. With 30K+ unique MTG cards, the search space for good triplets is enormous.

## Training Pipeline

```
make generate-training-data   # Query DB, build positive pairs → data/training_pairs.jsonl
make train-model              # Fine-tune all-MiniLM-L6-v2 → models/mtg-similarity-v1/
make evaluate-model           # Compare base vs fine-tuned on golden set
make train-full               # Run all steps end-to-end including embedding regeneration
```

## Training Data Sources

Positive pairs are generated from five signals in the card database, ordered by confidence:

| Source | Signal | Weight | Notes |
|---|---|---|---|
| `oracle_id` | Functional reprints | ~5% | Trivially identical — don't over-represent |
| `all_parts` | Scryfall related cards | ~15% | Meld pairs, tokens, flip sides — human-curated |
| keyword + color | Shared mechanics | ~40% | Requires 2+ keyword AND 1+ color overlap |
| tribal | Creature type overlap | ~25% | Same subtypes + CMC within +/-1 |
| CMC + color + type | Statistical bucket | ~15% | Same cost, color identity, and card supertype |

## Hyperparameters

| Parameter | Value | Rationale |
|---|---|---|
| Base model | `all-MiniLM-L6-v2` | 22M params, 384 dims — fast on CPU, small vectors |
| Loss | `MultipleNegativesRankingLoss` | Only needs positive pairs, in-batch negatives |
| Epochs | 3 | Small dataset — more risks overfitting |
| Batch size | 64 | Larger = better in-batch negatives for MNRL |
| Learning rate | 2e-5 | Standard for transformer fine-tuning |
| Warmup | 10% | Prevents catastrophic forgetting of pre-trained weights |
| Train/eval split | 90/10 | Enough eval data to track convergence |

## Integration

Set the `MTG_MODEL_PATH` environment variable to point to the fine-tuned model:

```bash
export MTG_MODEL_PATH=models/mtg-similarity-v1
make reset-embeddings
make run-embeddings
```

When unset, the system falls back to the base `all-MiniLM-L6-v2` model.
