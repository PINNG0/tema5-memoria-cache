"""Ponto de entrada: coordena testes e relatórios."""

from cache_sim.tests import run_tests
from cache_sim.report import show_main_comparison, show_sensitivity
from cache_sim.coherence import show_coherence_demo


def main():
    run_tests()
    print("Verificação automática: OK\n")
    show_main_comparison()
    show_sensitivity()
    show_coherence_demo()
    print("\nExecução concluída.")


if __name__ == "__main__":
    main()
