"""Testes rápidos das políticas, substituição e tráfego."""

from contextlib import redirect_stdout
from io import StringIO

from .cache import Cache
from .coherence import Bus, Core, Memory
from .config import (
    LINE_BYTES, N_ACCESSES, WORD_BYTES, WRITE_COUNT,
    POLICY_WT, POLICY_WB,
)
from .trace import generate_trace


def _line_is_cached(cache, address):
    index, tag, _ = cache._locate(address)
    return tag in cache.sets[index]


def run_tests():
    # A sequência principal deve ter a quantidade de acessos especificada.
    trace = generate_trace()
    assert len(trace) == N_ACCESSES
    assert sum(op == "W" for op, _, _ in trace) == WRITE_COUNT
    assert sum(op == "R" for op, _, _ in trace) == N_ACCESSES - WRITE_COUNT
    assert trace == generate_trace()  # A mesma seed produz o mesmo trace.

    # Entradas inválidas devem falhar com uma mensagem clara.
    for kwargs in ({"n": 0}, {"n": 10, "write_count": 11},
                   {"hot_fraction": float("nan")}, {"hot_lines": 0}):
        try:
            generate_trace(**kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"generate_trace aceitou parâmetros inválidos: {kwargs}")

    # As regiões quente e fria não podem se sobrepor.
    from .config import WORDS_PER_LINE
    hot_words = 8 * WORDS_PER_LINE
    all_hot = generate_trace(hot_fraction=1.0, hot_lines=8)
    all_cold = generate_trace(hot_fraction=0.0, hot_lines=8)
    assert all(address // WORD_BYTES < hot_words for _, address, _ in all_hot)
    assert all(address // WORD_BYTES >= hot_words for _, address, _ in all_cold)

    # WT: escrita em miss vai direto à memória e não aloca uma linha.
    wt = Cache(POLICY_WT)
    wt.access("W", 0, 10)
    assert wt.memory[0] == 10
    assert not _line_is_cached(wt, 0)
    assert wt.access("R", 0) == 10
    wt.access("W", 0, 123)  # Atualiza a memória e a cópia que já está na cache.
    assert wt.access("R", 0) == 123
    assert wt.memory[0] == 123
    assert (wt.hits, wt.misses) == (2, 2)
    wt_read, wt_write = wt.traffic_bytes()
    assert wt_read == LINE_BYTES
    assert wt_write == 2 * WORD_BYTES
    assert wt_read + wt_write == LINE_BYTES + 2 * WORD_BYTES

    # WB: escrita em miss aloca a linha e deixa a memória para depois.
    wb = Cache(POLICY_WB)
    wb.access("W", 0, 456)
    assert _line_is_cached(wb, 0)
    assert wb.memory.get(0, 0) == 0  # A memória ainda tem o valor antigo.
    assert wb.access("R", 0) == 456
    assert wb.hits == 1 and wb.misses == 1
    wb_read, wb_write = wb.traffic_bytes()
    assert wb_read == LINE_BYTES
    assert wb_write == LINE_BYTES  # Flush grava a linha suja uma única vez.
    assert wb.memory[0] == 456
    assert wb.traffic_bytes() == (wb_read, wb_write)  # Sem contar o flush duas vezes.

    # Cinco linhas no mesmo conjunto forçam uma substituição numa cache 4-way.
    eviction = Cache(POLICY_WB)
    same_set_addresses = [block * LINE_BYTES for block in (0, 16, 32, 48, 64)]
    for number, address in enumerate(same_set_addresses, start=1):
        eviction.access("W", address, number * 100)
    assert eviction.bus_line_writes == 1
    assert eviction.memory[same_set_addresses[0]] == 100
    eviction.flush()
    assert eviction.final_flush_lines == 4
    assert eviction.memory[same_set_addresses[-1]] == 500
    read_bytes, write_bytes = eviction.traffic_bytes()
    assert read_bytes == 5 * LINE_BYTES
    assert write_bytes == 5 * LINE_BYTES

    # Operações inválidas não devem alterar silenciosamente o modelo.
    invalid_cache = Cache(POLICY_WT)
    for operation, address, value in (("X", 0, None), ("R", -4, None),
                                      ("R", 2, None), ("W", 0, None)):
        try:
            invalid_cache.access(operation, address, value)
        except ValueError:
            pass
        else:
            raise AssertionError("Cache.access aceitou uma operação/endereço inválido")
    assert invalid_cache.hits == 0 and invalid_cache.misses == 0

    # As duas políticas processam o mesmo trace, mas podem ter tráfego diferente.
    wt_check, wb_check = Cache(POLICY_WT), Cache(POLICY_WB)
    for operation, address, value in trace[:100]:
        wt_check.access(operation, address, value)
        wb_check.access(operation, address, value)
    wt_bytes = sum(wt_check.traffic_bytes())
    wb_bytes = sum(wb_check.traffic_bytes())
    assert wt_bytes >= 0 and wb_bytes >= 0

    # A invalidação impede Core1 de reutilizar a cópia antiga de X.
    memory = Memory()
    memory.write("X", 0)
    bus = Bus()
    core0 = Core("Core0", memory, POLICY_WB, bus)
    core1 = Core("Core1", memory, POLICY_WB, bus)
    with redirect_stdout(StringIO()):  # Mantém os testes fora da saída principal.
        assert core0.read("X") == 0
        assert core1.read("X") == 0
        core0.write("X", 1)
        assert "X" not in core1.lines
        assert core1.read("X") == 1
    assert memory.read("X") == 1
