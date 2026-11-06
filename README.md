# Mini Paint 2D: Motor de Rasterização em Python

Este projeto é uma implementação de baixo nível de um aplicativo de desenho e rasterização

O objetivo principal é demonstrar a manipulação direta de memória de vídeo através de matrizes bidimensionais, criando primitivas gráficas do zero sem o uso de motores gráficos.

## Tecnologias Principais
* **NumPy:** O *Framebuffer* é representado por uma matriz contígua tridimensional de 8-bits, garantindo acesso e manipulação de píxeis em tempo O(1).
* **GLFW & PyOpenGL:** Gerenciamento do ciclo de vida da janela, *Polling* de eventos assíncronos, *Double Buffering* e transferência direta da matriz para a VRAM.

## Algoritmos Implementados
* **Reta de Bresenham:** Desenho de linhas exatas utilizando apenas aritmética inteira e acumuladores de erro, eliminando o custo de operações de ponto flutuante.
* **Círculo do Ponto Médio:** Renderização simétrica baseada em octantes, garantindo fechamento perfeito sem buracos.
* **Lápis (Traço Livre):** Encadeamento contínuo de micro-retas de Bresenham guiado pela atualização de âncoras no *Polling Rate* do hardware.
* **Flood Fill (Balde de Tinta):** Algoritmo de preenchimento utilizando uma estrutura de dados **Pilha (Stack)**.
* **Máquina de Estados & Clipping:** Uso de *Deep Copy* da matriz para efeito elástico (*Rubber-Banding*) e propagação de estado paramétrico acoplado a *NumPy Slicing* para isolar a Área de Desenho da Interface de Utilizador.

## Como Executar
1. Instale as dependências necessárias:
```bash
pip install glfw PyOpenGL numpy Pillow
```
2. Execute o arquivo principal
```bash
python main.py
```

## Comandos e Ferramentas
**Espessura do Traço:**
* **`1`**: Espessura fina
* **`2`**: Espessura média
* **`3`**: Espessura grossa

**Ferramentas:**
* **`L`**: Lápis
* **`A`**: Borracha
* **`4`**: Linha
* **`5` / `6`**: Retângulo vazado / Preenchido
* **`7` / `8`**: Círculo vazado / Preenchido
* **`9`**: Balde

**Ações:**
* **`N`**: Limpar a tela
* **`S`**: Salvar desenho
