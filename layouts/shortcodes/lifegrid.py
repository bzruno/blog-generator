from typing import List, Dict
from datetime import datetime
import json

def render(categories: List[str], posts: List[Dict[str, str]], content: str = "", **kwargs) -> str:
    """Gera HTML para um grid de vida, mostrando semanas vividas e futuras até 90 anos."""
    
    birth_date = datetime(1997, 5, 1)
    current_date = datetime.now()
    
    marcos = [
        {"data": datetime(2015, 5, 1), "nome": "Maioridade", "cor": "#7aa2f7"},
        {"data": datetime(2019, 5, 15), "nome": "Primeiro emprego", "cor": "#9ece6a"},
        {"data": datetime(2020, 3, 11), "nome": "Início pandemia COVID", "cor": "#f7768e"}
    ]
    
    try:
        end_date = datetime(birth_date.year + 90, birth_date.month, birth_date.day)
    except ValueError:
        end_date = datetime(birth_date.year + 90, birth_date.month, 28)

    total_days = (end_date - birth_date).days
    total_weeks = total_days // 7
    lived_days = (current_date - birth_date).days
    lived_weeks = min(lived_days // 7, total_weeks)
    
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

    # HTML limpo sem JavaScript inline
    html = '<div class="lifegrid-container">\n'
    html += '  <canvas id="lifeGrid"></canvas>\n'
    html += '  <div class="lifegrid-caption">\n'
    html += '    <div class="lifegrid-stats">\n'
    html += f'      Idade: {idade_atual:.1f} anos | '
    html += f'Semanas vividas: {lived_weeks:,} | '
    html += f'Semanas restantes: {total_weeks - lived_weeks:,}<br>\n'
    html += f'      Última atualização: {current_date.strftime("%d/%m/%Y às %H:%M")}\n'
    html += '    </div>\n'
    html += '    <div class="lifegrid-legends">\n'
    
    for marco in marcos_semanas:
        html += f'      <span class="legend-item">'
        html += f'<span class="legend-color" style="background-color:{marco["cor"]};"></span> '
        html += f'{marco["nome"]}</span>\n'
    
    html += '    </div>\n'
    html += '  </div>\n'
    html += '</div>\n'

    # Configuração em JSON para o JavaScript externo
    config = {
        "totalWeeks": total_weeks,
        "livedWeeks": lived_weeks,
        "weeksPerRow": weeks_per_row,
        "rows": rows,
        "marcosEspeciais": [{"semana": m["semana"], "cor": m["cor"]} for m in marcos_semanas]
    }
    
    html += f'<script src="/static/js/lifegrid.js"></script>\n'
    html += f'<script>initLifeGrid({json.dumps(config)});</script>\n'

    return html