"""Demonstração didática de incoerência e invalidação simplificada."""


class Memory:
    def __init__(self):
        self.data = {}

    def read(self, address):
        return self.data.get(address, 0)

    def write(self, address, value):
        self.data[address] = value


class Bus:
    def __init__(self):
        self.cores = []

    def attach(self, core):
        self.cores.append(core)

    def invalidate_others(self, writer, address):
        # Invalida cópias dos outros núcleos antes de concluir a escrita.
        for other in self.cores:
            if other is writer or address not in other.lines:
                continue
            value, dirty = other.lines[address]
            if dirty:
                writer.memory.write(address, value)
            del other.lines[address]
            print(f"    snoop: {other.name} invalida a cópia de X")


class Core:
    def __init__(self, name, memory, policy, bus=None):
        self.name = name
        self.memory = memory
        self.policy = policy
        self.bus = bus
        self.lines = {}  # endereço -> [valor, dirty]
        if bus:
            bus.attach(self)

    def read(self, address):
        if address in self.lines:
            value = self.lines[address][0]
            print(f"    {self.name}: lê X={value} (hit)")
            return value

        value = self.memory.read(address)
        # Um núcleo com linha suja pode fornecer o valor mais recente.
        if self.bus:
            for other in self.bus.cores:
                if other is not self and address in other.lines and other.lines[address][1]:
                    value = other.lines[address][0]
                    other.lines[address][1] = False
                    other.memory.write(address, value)
                    print(f"    snoop: {other.name} fornece X={value}")
                    break
        self.lines[address] = [value, False]
        print(f"    {self.name}: lê X={value} (miss)")
        return value

    def write(self, address, value):
        if self.bus:
            self.bus.invalidate_others(self, address)
        if self.policy == "WT":
            self.lines[address] = [value, False]
            self.memory.write(address, value)
            print(f"    {self.name}: escreve X={value} (cache + memória)")
        else:
            self.lines[address] = [value, True]
            print(f"    {self.name}: escreve X={value} (linha suja na cache)")


def run_scenario(title, policy, use_snoop):
    print(f"\n  {title}")
    memory = Memory()
    memory.write("X", 0)
    bus = Bus() if use_snoop else None
    core0 = Core("Core0", memory, policy, bus)
    core1 = Core("Core1", memory, policy, bus)
    core0.read("X")
    core1.read("X")
    core0.write("X", 1)
    value = core1.read("X")
    status = "COERENTE" if value == 1 else "INCOERENTE: valor obsoleto"
    print(f"    memória X={memory.read('X')} | leitura de Core1={value} -> {status}")


def show_coherence_demo():
    print("\n" + "=" * 64)
    print("PARTE 3 — COERÊNCIA ENTRE CACHES (SMP)")
    run_scenario("A) Write-through sem coerência", "WT", False)
    run_scenario("B) Write-back sem coerência", "WB", False)
    run_scenario("C) Write-back com snooping simplificado", "WB", True)
    print("\n  Nota: exemplo didático; não implementa um protocolo MESI completo.")
