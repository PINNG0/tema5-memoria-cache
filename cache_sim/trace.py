"""Gera a mesma sequência de acessos para comparar as políticas."""

import math
import random
from .config import N_ACCESSES, WRITE_COUNT, SEED, WORD_BYTES, WORDS_PER_LINE


def generate_trace(n=N_ACCESSES, write_count=WRITE_COUNT, seed=SEED,
                   hot_fraction=0.80, hot_lines=48):
    """Cria acessos reproduzíveis, com quantidade exata de escritas."""
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError("n deve ser um inteiro maior que zero")
    if not isinstance(write_count, int) or isinstance(write_count, bool):
        raise ValueError("write_count deve ser um inteiro")
    if not 0 <= write_count <= n:
        raise ValueError("write_count deve estar entre 0 e n")
    if (not isinstance(hot_fraction, (int, float))
            or not math.isfinite(hot_fraction)
            or not 0 <= hot_fraction <= 1):
        raise ValueError("hot_fraction deve ser um número entre 0 e 1")
    if not isinstance(hot_lines, int) or isinstance(hot_lines, bool) or hot_lines < 1:
        raise ValueError("hot_lines deve ser um inteiro maior que zero")

    rng = random.Random(seed)
    hot_words = hot_lines * WORDS_PER_LINE
    cold_words = 512 * WORDS_PER_LINE
    operations = ["W"] * write_count + ["R"] * (n - write_count)
    rng.shuffle(operations)

    trace = []
    for operation in operations:
        # hot_fraction controla a chance de acessar a região mais usada.
        # A região fria começa após a quente para não haver sobreposição.
        word = (rng.randrange(hot_words) if rng.random() < hot_fraction
                else hot_words + rng.randrange(cold_words))
        address = word * WORD_BYTES
        value = rng.randrange(1, 1_000_001) if operation == "W" else None
        trace.append((operation, address, value))
    return trace
