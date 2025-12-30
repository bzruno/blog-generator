from typing import List, Dict
from datetime import datetime, timedelta

def render(categories: List[str], posts: List[Dict[str, str]], content: str = "", **kwargs) -> str:
    """Gera HTML para um grid de vida, mostrando semanas vividas e futuras até 90 anos."""
    
    # Datas fornecidas
    birth_date = datetime(1997, 5, 1)
    current_date = datetime.now()
    
    # Marcos especiais - cores mais vivas e vibrantes
    marcos = [
        {"data": datetime(2015, 5, 1), "nome": "Maioridade", "cor": "#7aa2f7"},
        {"data": datetime(2019, 5, 15), "nome": "Primeiro emprego", "cor": "#9ece6a"},
        {"data": datetime(2020, 3, 11), "nome": "Início pandemia COVID", "cor": "#f7768e"}
    ]
    
    # Data exata dos 90 anos (considerando possíveis anos bissextos)
    try:
        end_date = datetime(birth_date.year + 90, birth_date.month, birth_date.day)
    except ValueError:  # Caso nasceu em 29/02 e o ano dos 90 não é bissexto
        end_date = datetime(birth_date.year + 90, birth_date.month, 28)

    # Calcular número total de semanas até 90 anos
    total_days = (end_date - birth_date).days
    total_weeks = total_days // 7  # Apenas semanas completas

    # Calcular semanas vividas até a data atual
    lived_days = (current_date - birth_date).days
    lived_weeks = lived_days // 7  # Apenas semanas completas
    
    # Validação: garantir que não exceda o total
    lived_weeks = min(lived_weeks, total_weeks)

    # Calcular semanas dos marcos especiais
    marcos_semanas = []
    for marco in marcos:
        dias_marco = (marco["data"] - birth_date).days
        semana_marco = dias_marco // 7
        if 0 <= semana_marco < total_weeks:
            marcos_semanas.append({
                "semana": semana_marco,
                "nome": marco["nome"],
                "cor": marco["cor"]
            })

    # Calcular idade atual para informações adicionais
    idade_atual = lived_days / 365.25  # Mais preciso com anos bissextos
    
    # Configurações do grid
    weeks_per_row = 52
    base_square_size = 10
    base_gap = 2
    rows = (total_weeks + weeks_per_row - 1) // weeks_per_row

    # Iniciar HTML com Canvas
    html = '<figure class="life-grid-container">\n'
    html += '  <canvas id="lifeGrid" class="life-grid"></canvas>\n'
    html += f'  <figcaption>\n'
    html += f'    <div class="info-principal">\n'
    html += f'      Idade: {idade_atual:.1f} anos | '
    html += f'      Semanas vividas: {lived_weeks:,} | '
    html += f'      Semanas restantes: {total_weeks - lived_weeks:,}<br>\n'
    html += f'      Última atualização: {current_date.strftime("%d/%m/%Y às %H:%M")}\n'
    html += f'    </div>\n'
    # APENAS legendas para marcos especiais
    html += '    <div class="legenda-container">\n'
    html += '      <div class="marcos-linha">\n'
    for i, marco in enumerate(marcos_semanas):
        html += f'        <span class="legenda-item marco-item"><span class="cor-marco" style="background-color: {marco["cor"]}"></span> {marco["nome"]}</span>\n'
    html += '      </div>\n'
    html += '    </div>\n'
    html += f'  </figcaption>\n'
    html += '</figure>\n'

    # Adicionar CSS para responsividade e transição suave
    html += '<style>\n'
    html += '.life-grid-container {\n'
    html += '  max-width: 100%;\n'
    html += '  margin: 20px auto;\n'
    html += '  text-align: center;\n'
    html += '  font-family: "Inter", system-ui, sans-serif;\n'
    html += '  color: #a9b1d6;\n'
    html += '  font-size: 14px;\n'
    html += '}\n'
    html += '.life-grid-container canvas {\n'
    html += '  max-width: 100%;\n'
    html += '  height: auto;\n'
    html += '  border-radius: 6px;\n'
    html += '  background: #16161e;\n'
    html += '}\n'
    html += '.life-grid-container figcaption {\n'
    html += '  margin-top: 15px;\n'
    html += '  font-family: "Inter", system-ui, sans-serif;\n'
    html += '  color: #a9b1d6;\n'
    html += '  font-size: 14px;\n'
    html += '  line-height: 1.6;\n'
    html += '}\n'
    html += '.info-principal {\n'
    html += '  margin-bottom: 12px;\n'
    html += '  font-family: "JetBrains Mono", monospace;\n'
    html += '  color: #c0caf5;\n'
    html += '  font-size: 13px;\n'
    html += '}\n'
    html += '.legenda-container {\n'
    html += '  display: flex;\n'
    html += '  flex-direction: column;\n'
    html += '  gap: 8px;\n'
    html += '}\n'
    html += '.marcos-linha {\n'
    html += '  display: flex;\n'
    html += '  justify-content: center;\n'
    html += '  flex-wrap: wrap;\n'
    html += '  gap: 16px;\n'
    html += '  padding-top: 8px;\n'
    html += '  border-top: 1px solid #1a1b26;\n'
    html += '}\n'
    html += '.legenda-item {\n'
    html += '  display: flex;\n'
    html += '  align-items: center;\n'
    html += '  gap: 6px;\n'
    html += '  font-family: "Inter", system-ui, sans-serif;\n'
    html += '  color: #a9b1d6;\n'
    html += '  font-size: 13px;\n'
    html += '}\n'
    html += '.marco-item {\n'
    html += '  font-family: "Inter", system-ui, sans-serif;\n'
    html += '  color: #a9b1d6;\n'
    html += '  font-size: 13px;\n'
    html += '}\n'
    html += '.cor-marco {\n'
    html += '  width: 12px;\n'
    html += '  height: 12px;\n'
    html += '  border-radius: 3px;\n'
    html += '}\n'
    html += '@media (max-width: 768px) {\n'
    html += '  .info-principal { font-size: 12px; }\n'
    html += '  .legenda-item, .marco-item { font-size: 12px; }\n'
    html += '}\n'
    html += '</style>\n'

    # Adicionar JavaScript para desenhar no Canvas responsivamente
    html += '<script>\n'
    html += 'document.addEventListener("DOMContentLoaded", function() {\n'
    html += '  const canvas = document.getElementById("lifeGrid");\n'
    html += '  const ctx = canvas.getContext("2d");\n'
    html += f'  const totalWeeks = {total_weeks};\n'
    html += f'  const livedWeeks = {lived_weeks};\n'
    html += f'  const weeksPerRow = {weeks_per_row};\n'
    html += f'  const rows = {rows};\n'
    html += f'  const baseSquareSize = {base_square_size};\n'
    html += f'  const baseGap = {base_gap};\n'
    html += '  let opacity = 1.0;\n'
    html += '  let fadingIn = true;\n'
    
    # Adicionar array de marcos especiais no JavaScript
    html += '  const marcosEspeciais = [\n'
    for i, marco in enumerate(marcos_semanas):
        html += f'    {{ semana: {marco["semana"]}, cor: "{marco["cor"]}" }}'
        if i < len(marcos_semanas) - 1:
            html += ',\n'
        else:
            html += '\n'
    html += '  ];\n'

    # Função para ajustar o tamanho do canvas
    html += '  function resizeCanvas() {\n'
    html += '    const container = canvas.parentElement;\n'
    html += '    const containerWidth = container.clientWidth;\n'
    html += '    const maxCanvasWidth = Math.min(containerWidth * 0.95, weeksPerRow * (baseSquareSize + baseGap) - baseGap);\n'
    html += '    const scale = maxCanvasWidth / (weeksPerRow * (baseSquareSize + baseGap) - baseGap);\n'
    html += '    const squareSize = Math.max(baseSquareSize * scale, 3);\n'
    html += '    const gap = Math.max(baseGap * scale, 1);\n'
    html += '    canvas.width = weeksPerRow * (squareSize + gap) - gap;\n'
    html += '    canvas.height = rows * (squareSize + gap) - gap;\n'
    html += '    return { squareSize, gap };\n'
    html += '  }\n'

    # Função para verificar se uma semana é um marco especial
    html += '  function isMarcoEspecial(week) {\n'
    html += '    return marcosEspeciais.find(marco => marco.semana === week);\n'
    html += '  }\n'

    # Função para desenhar o grid
    html += '  function drawGrid() {\n'
    html += '    const { squareSize, gap } = resizeCanvas();\n'
    html += '    ctx.clearRect(0, 0, canvas.width, canvas.height);\n'
    html += '    \n'
    html += '    for (let week = 0; week < totalWeeks; week++) {\n'
    html += '      const row = Math.floor(week / weeksPerRow);\n'
    html += '      const col = week % weeksPerRow;\n'
    html += '      const x = col * (squareSize + gap);\n'
    html += '      const y = row * (squareSize + gap);\n'
    html += '      \n'
    html += '      const marco = isMarcoEspecial(week);\n'
    html += '      \n'
    html += '      if (marco) {\n'
    html += '        ctx.fillStyle = marco.cor;\n'
    html += '        ctx.fillRect(x, y, squareSize, squareSize);\n'
    html += '      } else if (week < livedWeeks - 1) {\n'
    html += '        ctx.fillStyle = "#6c7086";\n'
    html += '        ctx.fillRect(x, y, squareSize, squareSize);\n'
    html += '      } else if (week === livedWeeks - 1 && livedWeeks > 0) {\n'
    html += '        ctx.fillStyle = `rgb(108, 112, 134, ${opacity})`;\n'
    html += '        ctx.fillRect(x, y, squareSize, squareSize);\n'
    html += '      } else {\n'
    html += '        ctx.fillStyle = "#313244";\n'
    html += '        ctx.fillRect(x, y, squareSize, squareSize);\n'
    html += '      }\n'
    html += '    }\n'
    html += '  }\n'

    # Animação para o quadrado com fade suave
    html += '  function animate() {\n'
    html += '    if (fadingIn) {\n'
    html += '      opacity += 0.003;\n'
    html += '      if (opacity >= 1.0) fadingIn = false;\n'
    html += '    } else {\n'
    html += '      opacity -= 0.012;\n'
    html += '      if (opacity <= 0.3) fadingIn = true;\n'
    html += '    }\n'
    html += '    drawGrid();\n'
    html += '    requestAnimationFrame(animate);\n'
    html += '  }\n'

    # Redesenhar ao redimensionar a janela
    html += '  window.addEventListener("resize", drawGrid);\n'

    # Iniciar o desenho e a animação
    html += '  drawGrid();\n'
    html += '  animate();\n'
    html += '});\n'
    html += '</script>\n'

    # Append any inner content
    if content:
        html += f'<div>{content}</div>\n'

    return html