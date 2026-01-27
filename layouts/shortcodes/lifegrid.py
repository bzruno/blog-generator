from typing import List, Dict
from datetime import datetime

def render(categories: List[str], posts: List[Dict[str, str]], content: str = "", **kwargs) -> str:
    """Gera HTML para um grid de vida, mostrando semanas vividas e futuras até 90 anos."""
    
    # Datas fornecidas
    birth_date = datetime(1997, 5, 1)
    current_date = datetime.now()
    
    # Marcos especiais
    marcos = [
        {"data": datetime(2015, 5, 1), "nome": "Maioridade", "cor": "#7aa2f7"},
        {"data": datetime(2019, 5, 15), "nome": "Primeiro emprego", "cor": "#9ece6a"},
        {"data": datetime(2020, 3, 11), "nome": "Início pandemia COVID", "cor": "#f7768e"}
    ]
    
    # Data exata dos 90 anos
    try:
        end_date = datetime(birth_date.year + 90, birth_date.month, birth_date.day)
    except ValueError:
        end_date = datetime(birth_date.year + 90, birth_date.month, 28)

    # Calcular semanas
    total_days = (end_date - birth_date).days
    total_weeks = total_days // 7
    lived_days = (current_date - birth_date).days
    lived_weeks = min(lived_days // 7, total_weeks)
    
    # Calcular semanas dos marcos
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

    idade_atual = lived_days / 365.25
    weeks_per_row = 52
    rows = (total_weeks + weeks_per_row - 1) // weeks_per_row

    # HTML com estilos inline e classe especial para não conflitar com CSS global
    html = '<div class="lifegrid-container" style="max-width:100%;margin:20px auto;text-align:center;font-family:Inter,system-ui,sans-serif;color:#a9b1d6;font-size:14px;">\n'
    html += '  <canvas id="lifeGrid" style="max-width:100%;height:auto;border-radius:6px;background:#16161e;"></canvas>\n'
    html += '  <div class="lifegrid-caption" style="margin-top:15px;font-family:Inter,system-ui,sans-serif;color:#a9b1d6;font-size:14px;line-height:1.6;">\n'
    html += '    <div style="margin-bottom:12px;font-family:JetBrains,monospace;color:#c0caf5;font-size:13px;">\n'
    html += f'      Idade: {idade_atual:.1f} anos | '
    html += f'Semanas vividas: {lived_weeks:,} | '
    html += f'Semanas restantes: {total_weeks - lived_weeks:,}<br>\n'
    html += f'      Última atualização: {current_date.strftime("%d/%m/%Y às %H:%M")}\n'
    html += '    </div>\n'
    html += '    <div style="display:flex;flex-direction:column;gap:8px;">\n'
    html += '      <div style="display:flex;justify-content:center;flex-wrap:wrap;gap:16px;padding-top:8px;border-top:1px solid #1a1b26;">\n'
    
    for marco in marcos_semanas:
        html += f'        <span style="display:flex;align-items:center;gap:6px;font-family:Inter,system-ui,sans-serif;color:#a9b1d6;font-size:13px;">'
        html += f'<span style="width:12px;height:12px;border-radius:3px;background-color:{marco["cor"]};"></span> {marco["nome"]}</span>\n'
    
    html += '      </div>\n'
    html += '    </div>\n'
    html += '  </div>\n'
    html += '</div>\n'

    # JavaScript para desenhar no Canvas
    html += '<script>\n'
    html += '(function() {\n'
    html += '  const canvas = document.getElementById("lifeGrid");\n'
    html += '  if (!canvas) return;\n'
    html += '  const ctx = canvas.getContext("2d");\n'
    html += f'  const totalWeeks = {total_weeks};\n'
    html += f'  const livedWeeks = {lived_weeks};\n'
    html += f'  const weeksPerRow = {weeks_per_row};\n'
    html += f'  const rows = {rows};\n'
    html += '  const baseSquareSize = 10;\n'
    html += '  const baseGap = 2;\n'
    html += '  let opacity = 1.0;\n'
    html += '  let fadingIn = true;\n'
    
    html += '  const marcosEspeciais = [\n'
    for i, marco in enumerate(marcos_semanas):
        html += f'    {{semana: {marco["semana"]}, cor: "{marco["cor"]}"}}'
        html += ',\n' if i < len(marcos_semanas) - 1 else '\n'
    html += '  ];\n'

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

    html += '  function isMarcoEspecial(week) {\n'
    html += '    return marcosEspeciais.find(marco => marco.semana === week);\n'
    html += '  }\n'

    html += '  function drawGrid() {\n'
    html += '    const { squareSize, gap } = resizeCanvas();\n'
    html += '    ctx.clearRect(0, 0, canvas.width, canvas.height);\n'
    html += '    for (let week = 0; week < totalWeeks; week++) {\n'
    html += '      const row = Math.floor(week / weeksPerRow);\n'
    html += '      const col = week % weeksPerRow;\n'
    html += '      const x = col * (squareSize + gap);\n'
    html += '      const y = row * (squareSize + gap);\n'
    html += '      const marco = isMarcoEspecial(week);\n'
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

    html += '  window.addEventListener("resize", drawGrid);\n'
    html += '  drawGrid();\n'
    html += '  animate();\n'
    html += '})();\n'
    html += '</script>\n'

    if content:
        html += f'<div>{content}</div>\n'

    return html