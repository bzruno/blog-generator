---
title: Guia Completo de GitHub Flavored Markdown
subtitle: Todos os elementos de sintaxe GFM em um único documento
date: 2026-01-03
category: Documentação, Tutorial
---

# Guia Completo de GitHub Flavored Markdown

<mark>ste documento demonstra **todos** os elementos suportados pelo GitHub Flavored Markdown (GFM).</mark>

## Ênfase e Formatação de Texto

**Texto em negrito** ou **também negrito**

*Texto em itálico* ou *também itálico*

***Negrito e itálico combinados***

~~Texto riscado (strikethrough)~~

## Parágrafos e Quebras de Linha

Este é um parágrafo normal. Basta deixar uma linha em branco para criar um novo parágrafo.

Para forçar uma quebra de linha sem novo parágrafo,  
adicione dois espaços no final da linha.

## Links

[Link simples](https://exemplo.com)

[Link com título](https://exemplo.com "Passe o mouse aqui")

<https://exemplo-autolink.com>

[Link de referência][1]

[1]: https://exemplo.com "Referência no rodapé"

## Imagens

![Estou assim](/images/corrida_ratos.gif)

## Listas

### Lista não ordenada

- Item 1
- Item 2
- Item 3
  - Subitem 3.1
  - Subitem 3.2
    - Subitem 3.2.1
- Item 4

- Asterisco também funciona
- Outro item

- Sinal de mais também
- Mais um item

### Lista ordenada

1. Primeiro item
2. Segundo item
3. Terceiro item
   1. Subitem 3.1
   2. Subitem 3.2
4. Quarto item

### Lista de tarefas (Task List)

- [x] Tarefa completa
- [x] Outra tarefa feita
- [ ] Tarefa pendente
- [ ] Mais uma pendente

## Código

### Código inline

Use `const x = 10;` para código inline.

Variáveis como `variavel` ou funções `funcao()` ficam destacadas.

### Blocos de código

```javascript
function exemplo() {
  const mensagem = "Hello, World!";
  console.log(mensagem);
  return true;
}
```

```python
def exemplo():
    mensagem = "Hello, World!"
    print(mensagem)
    return True
```

```bash
#!/bin/bash
echo "Hello, World!"
ls -la
```

Bloco sem syntax highlighting:

```
Texto sem formatação especial
Apenas monospace
```

## Citações (Blockquotes)

> Esta é uma citação simples.
> Pode ter múltiplas linhas.

> Citações podem conter **formatação** e *ênfase*.
>
> E até múltiplos parágrafos.

> Citações aninhadas:
>
> > Segunda citação dentro da primeira
> >
> > > E uma terceira!

## Linhas Horizontais

---

***

___

## Tabelas

| Coluna 1 | Coluna 2 | Coluna 3 |
|----------|----------|----------|
| Linha 1  | Dado A   | Dado X   |
| Linha 2  | Dado B   | Dado Y   |
| Linha 3  | Dado C   | Dado Z   |

### Tabela com alinhamento

| Esquerda | Centro | Direita |
|:---------|:------:|--------:|
| A1       | B1     | C1      |
| A2       | B2     | C2      |
| A3       | B3     | C3      |

### Tabela complexa

| Nome | Idade | Profissão | Cidade |
|------|-------|-----------|--------|
| João | 25 | Desenvolvedor | São Paulo |
| Maria | 30 | Designer | Rio de Janeiro |
| Pedro | 28 | Analista | Belo Horizonte |

## Links de Notas de Rodapé

Aqui está uma frase com uma nota de rodapé[^1].

Outra frase com nota de rodapé[^2].

[^1]: Esta é a primeira nota de rodapé.
[^2]: Esta é a segunda nota de rodapé com mais detalhes.

## HTML Embutido (se suportado)

<div align="center">
  <strong>Texto centralizado com HTML</strong>
</div>

<details>
<summary>Clique para expandir</summary>

Conteúdo escondido que aparece ao clicar.

</details>

## Escaping de Caracteres

Use backslash para escapar:

\*Não é itálico\*

\# Não é título

\[Não é link\](url)

## Emojis (GitHub style)

:smile: :heart: :+1: :rocket: :fire: :tada:

## Menções e Referências

@usuario - mencionar usuário

# 123 - referência a issue

GH-123 - referência a issue do GitHub

## Listas de Definição (se suportado)

Term 1
:   Definition 1

Term 2
:   Definition 2

## Combinações Avançadas

### Lista com código e citações

1. Primeiro item com código:

   ```js
   const x = 10;
   ```

2. Segundo item com citação:
   > Uma citação dentro de lista

3. Terceiro item com sublista:
   - Subitem A
   - Subitem B

### Tabela com formatação

| **Negrito** | *Itálico* | ~~Riscado~~ | `Código` |
|-------------|-----------|-------------|----------|
| **Dado 1**  | *Dado 2*  | ~~Dado 3~~  | `Dado 4` |
| Texto       | Texto     | Texto       | Texto    |

## Comentários HTML (invisíveis)

<!-- Este é um comentário que não aparece no HTML renderizado -->

## Caracteres Especiais

&copy; &reg; &trade; &euro; &pound; &yen;

## Quebra de Página

---

## Conclusão

Este documento contém **todos** os elementos principais do GitHub Flavored Markdown:

- ✅ Títulos (H1-H6)
- ✅ Ênfase (negrito, itálico, riscado)
- ✅ Links e imagens
- ✅ Listas (ordenadas, não ordenadas, tarefas)
- ✅ Código (inline e blocos)
- ✅ Citações
- ✅ Tabelas com alinhamento
- ✅ Linhas horizontais
- ✅ HTML embutido
- ✅ Notas de rodapé
- ✅ Escaping de caracteres
- ✅ Emojis

**Pronto para usar no seu blog!**
