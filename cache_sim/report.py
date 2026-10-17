"""Apresenta os resultados de forma organizada no terminal."""

from .cache import Cache
from .config import (
    N_ACCESSES, WRITE_COUNT, WORD_BYTES, LINE_BYTES, CACHE_LINES,
    ASSOCIATIVITY, N_SETS, POLICY_WT, POLICY_WB,
)
from .trace import generate_trace


def _run(trace, policy):
    cache = Cache(policy)
    for operation, address, value in trace:
        cache.access(operation, address, value)
    reads, writes = cache.traffic_bytes()
    return cache, reads, writes, reads + writes


def _print_result(name, cache, reads, writes, total, trace_length):
    print(f"\n{name}")
    print(f"  Acertos / falhas : {cache.hits:>4} / {cache.misses:<4} ({cache.hits / trace_length:.1%} de acerto)")
    print(f"  Leituras         : {cache.bus_reads:>4} linhas = {reads:>7,} bytes")
    if cache.policy == POLICY_WT:
        print(f"  Escritas         : {cache.bus_word_writes:>4} palavras = {writes:>7,} bytes")
    else:
        print(f"  Write-backs      : {cache.bus_line_writes:>4} por substituição")
        print(f"  Flush final      : {cache.final_flush_lines:>4} linhas")
        print(f"  Escritas         : {writes:>7,} bytes no total")
    print(f"  TRÁFEGO TOTAL    : {total:>7,} bytes")


def show_main_comparison():
    trace = generate_trace()
    write_count = sum(op == "W" for op, _, _ in trace)
    read_count = len(trace) - write_count
    assert len(trace) == N_ACCESSES and write_count == WRITE_COUNT

    print("=" * 64)
    print("SIMULADOR DE POLÍTICAS DE ESCRITA EM CACHE")
    print("=" * 64)
    print("CONFIGURAÇÃO")
    print(f"  Acessos: {len(trace)} ({read_count} leituras, {write_count} escritas)")
    print(f"  Cache: {CACHE_LINES * LINE_BYTES} B | linha: {LINE_BYTES} B | palavra: {WORD_BYTES} B")
    print(f"  Organização: {ASSOCIATIVITY} vias | {N_SETS} conjuntos | substituição LRU")
    print("  WT: no-write-allocate | WB: write-allocate | mesmo trace")
    print("  Acertos/falhas contam todas as operações (leituras e escritas).")
    print("\nPARTE 1 — COMPARAÇÃO DE TRÁFEGO")

    results = {}
    for policy, name in (
        (POLICY_WT, "1. Write-through"),
        (POLICY_WB, "2. Write-back"),
    ):
        cache, reads, writes, total = _run(trace, policy)
        results[policy] = total
        _print_result(name, cache, reads, writes, total, len(trace))

    wt, wb = results[POLICY_WT], results[POLICY_WB]
    ratio = f"{wb / wt:.2f}x" if wt else "indefinido (WT = 0)"
    winner = "Write-through" if wt < wb else "Write-back" if wb < wt else "empate"
    print("\nRESUMO")
    print(f"  WT: {wt:,} bytes | WB: {wb:,} bytes | WB/WT: {ratio}")
    print(f"  Menor tráfego neste cenário: {winner}")
    print("  O resultado depende do padrão de acessos e das hipóteses do modelo.")


def show_sensitivity():
    print("\n" + "=" * 64)
    print("PARTE 2 — EFEITO DA LOCALIDADE DOS ACESSOS")
    print("  Cada linha usa um trace com exatamente 1.000 acessos e 300 escritas.")
    print("  A região quente e a região fria não se sobrepõem.")
    print(f"  {'Prob. quente':>14} {'Linhas quentes':>14} {'WT (bytes)':>14} {'WB (bytes)':>14} {'WB/WT':>8}")
    for fraction, hot_lines in ((0.80, 48), (0.90, 32), (0.95, 32), (0.99, 16)):
        trace = generate_trace(hot_fraction=fraction, hot_lines=hot_lines)
        wt = _run(trace, POLICY_WT)[3]
        wb = _run(trace, POLICY_WB)[3]
        ratio = wb / wt if wt else float("inf")
        print(f"{fraction:>13.0%} {hot_lines:>14} {wt:>14,} {wb:>14,} {ratio:>8.2f}")
