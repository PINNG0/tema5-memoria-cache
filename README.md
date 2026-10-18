# 🧠 Simulador de Políticas de Escrita em Memória Cache

<p align="center">
  <strong>Write-through × Write-back</strong><br>
  Simulação, análise de tráfego no barramento e demonstração didática de coerência de cache em SMP.
</p>

---

## 📌 Sobre o projeto

Este projeto implementa, em **Python**, um simulador didático para estudar e comparar duas políticas de escrita utilizadas em memória cache:

- **Write-through:** cada escrita atualiza a cache e é propagada à memória principal.
- **Write-back:** as alterações são mantidas inicialmente na cache e escritas na memória principal quando uma linha modificada precisa ser substituída ou no descarregamento final considerado pela simulação.

Além da comparação entre as políticas, o programa calcula o tráfego de dados, analisa como diferentes padrões de localidade influenciam os resultados e apresenta um exemplo simplificado de incoerência entre caches privadas em um sistema multiprocessado (SMP).

Projeto acadêmico da disciplina **Arquitetura de Computadores — 2026/2**, da Universidade Federal de Rondônia (UNIR).

## 🎯 Objetivos

- Comparar as políticas Write-through e Write-back.
- Simular **1.000 acessos à memória**, com **700 leituras e 300 escritas**.
- Calcular o tráfego de leitura e escrita em bytes.
- Observar o efeito de diferentes padrões de localidade.
- Demonstrar incoerência entre caches privadas e uma estratégia simplificada de invalidação por *bus snooping*.
- Organizar o código em módulos e executar autotestes.

## ⚙️ Configuração da simulação principal

| Parâmetro | Configuração |
|---|---:|
| Total de acessos | 1.000 |
| Leituras | 700 (70%) |
| Escritas | 300 (30%) |
| Capacidade da cache | 2.048 bytes (2 KiB) |
| Tamanho da linha | 32 bytes |
| Tamanho da palavra | 4 bytes |
| Palavras por linha | 8 |
| Associatividade | 4 vias |
| Número de conjuntos | 16 |
| Substituição | LRU (*Least Recently Used*) |
| Write-through | *No-write-allocate* |
| Write-back | *Write-allocate* |

> **Importante:** as duas configurações usam estratégias de alocação diferentes. Os resultados comparam essas configurações completas, e não apenas o efeito isolado da política de escrita.

## 📊 Resultados da configuração principal

Resultados da versão final do simulador:

| Métrica | Write-through | Write-back |
|---|---:|---:|
| Acertos (*hits*) | 666 | 663 |
| Falhas (*misses*) | 334 | 337 |
| Taxa de acerto | 66,6% | 66,3% |
| Linhas lidas da memória | 228 | 337 |
| Tráfego de leitura | 7.296 B | 10.784 B |
| Escritas de palavra na memória | 300 | — |
| *Write-backs* por substituição | — | 116 |
| Linhas modificadas no descarregamento final | — | 38 |
| Tráfego de escrita total | 1.200 B | 4.928 B |
| **Tráfego total** | **8.496 B** | **15.712 B** |

### Interpretação

Nesta configuração, o Write-through gera menos tráfego total. Isso não significa que seja sempre mais eficiente: o Write-through utiliza *no-write-allocate*, enquanto o Write-back utiliza *write-allocate*. Em falhas de escrita, o Write-back pode carregar linhas para a cache, aumentando as leituras contabilizadas.

No Write-back, o cálculo também considera as linhas modificadas que permanecem na cache ao final, como transferências de retorno para a memória principal.

## 🔎 Análise de localidade

O simulador executa cenários com diferentes proporções de acessos a uma região quente da memória:

| Acessos quentes | Linhas quentes | Write-through | Write-back | Relação WB/WT |
|---:|---:|---:|---:|---:|
| 80% | 48 | 8.496 B | 15.712 B | 1,85 |
| 90% | 32 | 4.592 B | 6.368 B | 1,39 |
| 95% | 32 | 3.664 B | 4.480 B | 1,22 |
| 99% | 16 | 2.032 B | 1.536 B | 0,76 |

Os resultados mostram que o padrão de acesso influencia o tráfego. Quando os acessos se concentram em uma região menor, os dados podem ser reutilizados com mais frequência enquanto permanecem na cache. No cenário de 99% de acessos quentes em 16 linhas, o Write-back apresenta tráfego total inferior ao Write-through.

**Limitação experimental:** os cenários variam tanto a proporção de acessos quentes quanto a quantidade de linhas quentes; portanto, não isolam apenas uma variável.

## 🔄 Coerência de cache em SMP

O projeto inclui um exemplo didático com dois núcleos e caches privadas que armazenam cópias do mesmo endereço. São demonstrados cenários em que um núcleo altera o valor enquanto o outro mantém uma cópia antiga, tanto com Write-through quanto com Write-back.

Em seguida, o simulador apresenta uma estratégia simplificada de *bus snooping* com invalidação: a cópia do outro núcleo é invalidada e, quando o dado é solicitado novamente, o modelo recupera o valor atualizado.

> A demonstração é didática e não implementa integralmente um protocolo comercial de coerência, como MESI.

## 🗂️ Estrutura do projeto

```text
projeto_cache/
├── main.py
├── LEIA-ME.txt
├── .gitignore
└── cache_sim/
    ├── __init__.py
    ├── cache.py
    ├── coherence.py
    ├── config.py
    ├── report.py
    ├── tests.py
    └── trace.py
```

| Arquivo | Responsabilidade |
|---|---|
| `main.py` | Ponto de entrada: executa as demonstrações e apresenta os resultados. |
| `cache_sim/cache.py` | Estruturas e operações relacionadas à cache e às políticas de escrita. |
| `cache_sim/coherence.py` | Demonstração didática de coerência entre caches em SMP. |
| `cache_sim/config.py` | Parâmetros e configurações do simulador. |
| `cache_sim/report.py` | Organização e exibição dos resultados. |
| `cache_sim/tests.py` | Autotestes do projeto. |
| `cache_sim/trace.py` | Geração da sequência de acessos dos experimentos. |
| `LEIA-ME.txt` | Instruções complementares. |

## ▶️ Como executar

### Requisitos

- Python 3 instalado.
- Terminal ou PowerShell.

O projeto utiliza a biblioteca padrão do Python; não é necessário instalar pacotes externos para a execução básica.

### 1. Clonar o repositório

```bash
git clone https://github.com/PINNG0/tema5-memoria-cache.git
cd tema5-memoria-cache
```

### 2. Executar o simulador

No Windows, pelo PowerShell:

```powershell
py main.py
```

Se o comando `py` não estiver disponível, tente:

```bash
python main.py
```

A execução apresenta as demonstrações, os resultados de tráfego, a análise de localidade e os autotestes.

## 🧪 Testes

Os autotestes fazem parte do projeto e são executados pelo fluxo principal. Para executar o programa e verificar o resultado dos testes:

```powershell
py main.py
```

Confira no terminal a indicação de sucesso dos autotestes.

## ⚠️ Limitações do modelo

O simulador tem finalidade educacional e não representa todos os detalhes de uma cache física. Os resultados dependem dos parâmetros, da sequência de acessos e das estratégias de alocação configuradas. O modelo não representa integralmente latências, filas do barramento, *prefetching* ou um protocolo comercial completo de coerência.

Os números deste README correspondem à versão final do simulador descrita no projeto. Alterações no código ou nos parâmetros podem modificar os resultados.

## 👥 Integrantes

- Ana Julia Santiago Vieira
- Andrei Rodrigues de Araújo
- Clarice Thais Reyes Ortiz Pardo
- Pedro Artur Pereira Oliveira Santos

**Instituição:** Universidade Federal de Rondônia (UNIR)  
**Departamento:** Departamento Acadêmico de Ciências da Computação  
**Disciplina:** Arquitetura de Computadores — 2026/2  
**Professor:** Marcello Batista Ribeiro

## 📚 Referências

- STALLINGS, William. *Arquitetura e organização de computadores*. 10. ed. São Paulo: Pearson Education do Brasil, 2017.
- STALLINGS, William. *Computer organization and architecture: designing for performance*. 10. ed. Harlow: Pearson Education Limited, 2016.
- PATTERSON, David A.; HENNESSY, John L. *Computer organization and design: the hardware/software interface*. 6. ed. Cambridge: Morgan Kaufmann, 2020.
- HENNESSY, John L.; PATTERSON, David A. *Computer architecture: a quantitative approach*. 6. ed. Cambridge: Morgan Kaufmann, 2017.

---

<p align="center">
  <sub>Projeto acadêmico para estudo de políticas de escrita em memória cache.</sub>
</p>
