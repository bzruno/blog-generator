---
title: "Teste Completo de Markdown - Todos os Plugins"
subtitle: "Demonstração de todos os recursos disponíveis no blog"
date: 2026-02-07
category: Tecnologia, Internet
---

${toc}

Este artigo exercita **todos** os plugins do seu pipeline de Markdown. Use-o para validar o tema e o comportamento após mudanças. :rocket:

---

## 1. Título com âncoras (anchor)

Os headings geram links permanentes (símbolo # ao passar o mouse). Este é o **h2**.

### 1.1. Subseção (h3)

Conteúdo aqui.

#### 1.1.1. Sub-subseção (h4)

Nível mínimo que entra no sumário.

---

## 2. Ênfase e formatação inline

- **Negrito** e *itálico*
- ==Texto destacado (mark)==
- ~subscript~ e ^superscript^
- ++Texto inserido (ins)++
- ~~Riscado~~ e <ins>HTML permitido</ins>
- Abreviação: a *[GFM](https://daringfireball.net/projects/markdown/)* é usada aqui. (GFM = GitHub Flavored Markdown)
- Atalhos de teclado: [[Ctrl]]+[[C]], [[Enter]], [[Alt]]+[[F4]]

---

## 3. Emojis

:smile: :heart: :fire: :books: :computer: :warning: :white_check_mark: :x:

---

## 4. Lista de tarefas (task lists)

- [ ] Item pendente
- [x] Item concluído
- [ ] Outro pendente com **formatação**
- [x] Concluído com :tada:

---

## 5. Lista de definição (deflist)

Termo 1
: Definição do primeiro termo. Pode ter múltiplos parágrafos.

Termo 2
: Segunda definição.

Termo 3
: Terceira definição, também em uma linha.

---

## 6. Citações (blockquote)

> Citação simples com **ênfase** e [link](https://example.com).

> Citação com múltiplos
> parágrafos.
>
> E um terceiro parágrafo.

---

## 7. Código

Inline: use `print("Hello")` no texto.

Bloco com syntax highlight (JavaScript):

```javascript
function greet(name) {
  console.log("Olá, " + name + "!");
}
greet("Blog");
```

Bloco sem linguagem:

```
texto puro
sem highlight
```

Python:

```python
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)
```

Dentro de código, spoilers **não** devem ativar: !!isto continua literal!!.

---

## 8. Spoilers (custom)

No texto normal, !!este trecho é spoiler!! e fica oculto até passar o mouse.

Outro exemplo: a resposta é !!42!!.

---

## 9. Tabelas (multimd-table)

Tabela básica:

| Coluna A | Coluna B | Coluna C |
| -------- | -------- | -------- |
| a1       | b1       | c1       |
| a2       | b2       | c2       |

Tabela com alinhamento:

| Esquerda | Centro | Direita |
| :------- | :----: | ------: |
| left     | center | right   |

---

## 10. Imagens e figuras (implicit-figures + imsize)

Imagem com legenda (alt vira figcaption):

![Legenda da figura: logo ou ícone](https://via.placeholder.com/200x100?text=Figura+1)

Imagem com tamanho (imsize), se suportado: `![Alt](url){width=300}` ou sintaxe do plugin.

---

## 11. Vídeos (markdown-it-video)

YouTube (ID do vídeo):

@[youtube](dQw4w9WgXcQ)

Vimeo (ID):

@[vimeo](148751763)

---

## 12. Fórmulas matemáticas (KaTeX)

O blog usa **KaTeX 0.16** no build (Node). Sintaxe: `$...$` para inline e `$$...$$` para bloco. O CSS está em `layouts/base.html`.

### Inline

$E = mc^2$, $\frac{a}{b}$, $\alpha + \beta = \gamma$, $x^2 + y^2 = z^2$, $\sqrt{2} \approx 1{,}414$.

### Bloco (display)

Integral gaussiana:

$$
\int_{-\infty}^{\infty} e^{-x^2} \, dx = \sqrt{\pi}
$$

Série de Basel:

$$
\sum_{n=1}^{\infty} \frac{1}{n^2} = \frac{\pi^2}{6}
$$

### Frações e binomiais

$$
\frac{1}{1 + \frac{1}{2}} = \frac{2}{3}, \qquad \binom{n}{k} = \frac{n!}{k!(n-k)!}
$$

### Limites e derivadas

$$
\lim_{x \to 0} \frac{\sin x}{x} = 1, \qquad \frac{\partial f}{\partial x}, \qquad f'(x) = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h}
$$

### Letras gregas e conjuntos

$$
\alpha, \beta, \gamma, \Omega, \pi, \theta, \lambda, \mu
$$

$$
x \in \mathbb{R}, \quad A \subset \mathbb{N}, \quad \mathcal{L}\{f\} = F(s)
$$

### Matrizes

$$
\begin{matrix} a & b \\ c & d \end{matrix}
\qquad
\begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix}
\qquad
\begin{bmatrix} x \\ y \end{bmatrix}
$$

### Equações alinhadas

$$
\begin{aligned}
(a+b)^2 &= a^2 + 2ab + b^2 \\
(a-b)^2 &= a^2 - 2ab + b^2
\end{aligned}
$$

### Setas e relações

$$
A \Rightarrow B, \quad x \leftarrow y, \quad a \geq b, \quad c \neq 0
$$

### Overline, underline e acentos

$$
\overline{AB}, \quad \underline{x}, \quad \hat{x}, \quad \vec{v}
$$

### Funções e operadores

$$
\sin x, \quad \cos \theta, \quad \log n, \quad \ln x, \quad \max_i a_i
$$

### Texto em matemática

Use `\text{...}`. Para acentos use comandos LaTeX: `\'a` = á, `\'\i` = í.

$$
\text{\'area} = \pi r^2, \qquad \text{nota: } x > 0
$$

Inline: $\text{Obs: } n \in \mathbb{N}$.

### Fórmula de Bhaskara

$$
x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
$$

---

## 13. Links (linkify + linkAttrs)

Links externos abrem em nova aba com `rel="noopener noreferrer"`:

- https://example.com
- [Texto do link](https://github.com)
- <https://cursor.com>

---

## 14. Atributos (attrs)

Parágrafo com classe à direita: {.text-right} (se o tema suportar).

---

## 15. Notas de rodapé (footnote)

Texto com referência à nota[^1] e outra[^2].

[^1]: Conteúdo da primeira nota de rodapé.
[^2]: Segunda nota. Pode ter *formatação* e [links](https://example.com).

---

## 16. HTML bruto (html: true)

<div style="padding: 8px; background: var(--bg-elevated); border-radius: 4px; margin: 1em 0;">
  Bloco HTML customizado (se <code>html: true</code> estiver ativo).
</div>

---

## 17. Detalhes / resumo (HTML nativo)

<details>
<summary>Clique para expandir</summary>

Conteúdo oculto até abrir. Pode ter **markdown** e listas:

- item 1
- item 2
</details>

---

## 18. Resumo dos plugins testados

| Plugin / recurso | Seção |
| ----------------- | ----- |
| TOC (sumário) | Topo |
| Anchor (âncoras em headings) | 1 |
| Ênfase (mark, sub, sup, ins) | 2 |
| Emoji | 3 |
| Task lists | 4 |
| Deflist | 5 |
| Blockquote (classe .blockquote) | 6 |
| Código + highlight.js | 7 |
| Spoilers !!...!! | 8 |
| Tabelas (multimd-table + .table-wrapper) | 9 |
| Imagens / figuras | 10 |
| Vídeo (YouTube / Vimeo) | 11 |
| KaTeX | 12 |
| Linkify + linkAttrs | 13 |
| Attrs | 14 |
| Footnotes | 15 |
| HTML bruto | 16 |
| Details/summary | 17 |

Se tudo renderizar como esperado, seu pipeline está completo. :white_check_mark:
