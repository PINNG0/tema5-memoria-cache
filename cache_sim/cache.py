"""Modelo de cache set-associative com LRU e duas políticas de escrita."""

from collections import OrderedDict
from .config import (
    POLICY_WT, POLICY_WB, LINE_BYTES, WORD_BYTES, WORDS_PER_LINE,
    ASSOCIATIVITY, N_SETS,
)


class Cache:
    def __init__(self, policy):
        if policy not in (POLICY_WT, POLICY_WB):
            raise ValueError("policy deve ser 'WT' ou 'WB'")
        self.policy = policy
        # Cada conjunto mantém as linhas da menos para a mais recentemente usada.
        self.sets = [OrderedDict() for _ in range(N_SETS)]
        self.memory = {}
        self.hits = 0
        self.misses = 0
        self.bus_reads = 0
        self.bus_word_writes = 0
        self.bus_line_writes = 0
        self.final_flush_lines = 0
        self._flushed = False

    @staticmethod
    def _locate(address):
        block = address // LINE_BYTES
        return block % N_SETS, block // N_SETS, block

    @staticmethod
    def _word_offset(address):
        return (address % LINE_BYTES) // WORD_BYTES

    def _write_line_to_memory(self, block, data):
        base = block * LINE_BYTES
        for offset, value in data.items():
            self.memory[base + offset * WORD_BYTES] = value

    def _fill(self, cache_set, tag, block):
        # Se o conjunto estiver cheio, remove a linha LRU e salva dados sujos.
        if len(cache_set) >= ASSOCIATIVITY:
            _, victim = cache_set.popitem(last=False)
            if victim["dirty"]:
                self.bus_line_writes += 1
                self._write_line_to_memory(victim["block"], victim["data"])

        base = block * LINE_BYTES
        data = {
            offset: self.memory.get(base + offset * WORD_BYTES, 0)
            for offset in range(WORDS_PER_LINE)
        }
        cache_set[tag] = {"data": data, "dirty": False, "block": block}
        self.bus_reads += 1

    def access(self, operation, address, value=None):
        if operation not in ("R", "W"):
            raise ValueError("operation deve ser R ou W")
        if (not isinstance(address, int) or isinstance(address, bool)
                or address < 0 or address % WORD_BYTES):
            raise ValueError("endereço deve ser um inteiro não negativo e alinhado a palavra")
        if operation == "W" and not isinstance(value, int):
            raise ValueError("escrita precisa informar um valor inteiro")
        if self._flushed:
            raise RuntimeError("não é possível acessar a cache depois do flush final")

        index, tag, block = self._locate(address)
        offset = self._word_offset(address)
        cache_set = self.sets[index]
        line = cache_set.get(tag)
        hit = line is not None

        if hit:
            self.hits += 1
            cache_set.move_to_end(tag)
        else:
            self.misses += 1

        if operation == "R":
            if not hit:
                self._fill(cache_set, tag, block)
                line = cache_set[tag]
            return line["data"][offset]

        if self.policy == POLICY_WT:
            # Write-through grava na memória; no-write-allocate não carrega miss.
            self.memory[address] = value
            self.bus_word_writes += 1
            if hit:
                line["data"][offset] = value
        else:
            # Write-back carrega em miss e adia a gravação da linha modificada.
            if not hit:
                self._fill(cache_set, tag, block)
                line = cache_set[tag]
            line["data"][offset] = value
            line["dirty"] = True
        return None

    def flush(self):
        """Grava uma única vez as linhas sujas que ainda estão na cache."""
        if self._flushed:
            return 0
        count = 0
        if self.policy == POLICY_WB:
            for cache_set in self.sets:
                for line in cache_set.values():
                    if line["dirty"]:
                        self._write_line_to_memory(line["block"], line["data"])
                        line["dirty"] = False
                        count += 1
            self.final_flush_lines += count
        self._flushed = True
        return count

    def traffic_bytes(self):
        """Retorna (bytes de leitura, bytes de escrita), incluindo flush final."""
        self.flush()
        read_bytes = self.bus_reads * LINE_BYTES
        write_bytes = (self.bus_word_writes * WORD_BYTES
                       + self.bus_line_writes * LINE_BYTES
                       + self.final_flush_lines * LINE_BYTES)
        return read_bytes, write_bytes
