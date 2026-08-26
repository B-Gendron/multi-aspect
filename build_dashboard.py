import json

# 1. Load raw experiment data
with open("experiments.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

# 2. Filter out non-EVALUATED entries
evaluated_data = [d for d in raw_data if d.get("Status") == "EVALUATED"]

# 3. Define the HTML dashboard template
html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>LLM Multi-Aspect Experiment Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 20px; background-color: #f8f9fa; color: #212529; }}
        h1 {{ margin-bottom: 4px; font-size: 22px; color: #1a252f; }}
        .subtitle {{ margin-bottom: 18px; color: #6c757d; font-size: 13px; }}
        
        .controls {{ display: flex; flex-wrap: wrap; gap: 15px; background: white; padding: 16px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.06); margin-bottom: 20px; align-items: flex-start; }}
        .control-group {{ display: flex; flex-direction: column; font-size: 12px; font-weight: 700; color: #34495e; text-transform: uppercase; letter-spacing: 0.5px; }}
        .checkbox-panel {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 6px; font-weight: normal; text-transform: none; }}
        .checkbox-panel label {{ display: flex; align-items: center; gap: 4px; background: #f1f3f5; padding: 4px 8px; border-radius: 4px; font-size: 12px; cursor: pointer; user-select: none; }}
        .checkbox-panel label:hover {{ background: #e9ecef; }}
        
        .metric-switch {{ background: #ebf5fb; border: 1px solid #aed6f1; padding: 8px 12px; border-radius: 6px; }}
        .metric-switch select {{ margin-top: 4px; padding: 5px 8px; border-radius: 4px; border: 1px solid #3498db; font-weight: 600; font-size: 13px; background: #fff; cursor: pointer; }}
        
        .stats-badge {{ margin-left: auto; background: #2c3e50; color: white; padding: 8px 14px; border-radius: 6px; font-size: 13px; font-weight: 600; align-self: center; }}
        
        #chart-container {{ background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.06); margin-bottom: 25px; }}
        #table-container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.06); overflow-x: auto; }}
        
        table {{ width: 100%; border-collapse: collapse; font-size: 12px; text-align: left; }}
        th {{ background-color: #2c3e50; color: white; padding: 9px; font-weight: 600; }}
        td {{ padding: 7px 9px; border-bottom: 1px solid #dee2e6; }}
        tr:nth-child(even) {{ background-color: #f8f9fa; }}
        tr:hover {{ background-color: #e8f4f8; }}
        
        .tag-blue {{ color: #2980b9; font-weight: bold; }}
        .tag-red {{ color: #c0392b; font-weight: bold; }}
    </style>
</head>
<body>

    <h1>LLM Multi-Aspect Fine-Tuning Dashboard</h1>
    <div class="subtitle">Evaluated runs only. Config counterparts (Frozen vs. Defrozen Adapters) are placed side-by-side for direct visual comparison.</div>

    <div class="controls">
        <div class="control-group metric-switch">
            <label style="color:#1b4f72;">📊 Metric Suite</label>
            <select id="metric-mode" onchange="updateDashboard()">
                <option value="wF1">Weighted F1 (CEFR / Polarity / Load)</option>
                <option value="ALT">CEFR (MAE) / Polarity (MCC) / Load (MAE)</option>
            </select>
        </div>

        <div class="control-group">
            <label>Embedding Init</label>
            <div class="checkbox-panel">
                <label><input type="checkbox" class="filter-emb" value="Sem" checked onchange="updateDashboard()"> Sem</label>
                <label><input type="checkbox" class="filter-emb" value="CLM" checked onchange="updateDashboard()"> CLM</label>
                <label><input type="checkbox" class="filter-emb" value="Rand" checked onchange="updateDashboard()"> Rand</label>
                <label><input type="checkbox" class="filter-emb" value="NoEmb" checked onchange="updateDashboard()"> NoEmb</label>
            </div>
        </div>

        <div class="control-group">
            <label>Adapter Init</label>
            <div class="checkbox-panel">
                <label><input type="checkbox" class="filter-adapter" value="Scratch" checked onchange="updateDashboard()"> Scratch</label>
                <label><input type="checkbox" class="filter-adapter" value="Pretrained" checked onchange="updateDashboard()"> Pretrained</label>
            </div>
        </div>

        <div class="control-group">
            <label>E.tr (Emb Trainable)</label>
            <div class="checkbox-panel">
                <label><input type="checkbox" class="filter-etr" value="true" checked onchange="updateDashboard()"> E.tr</label>
                <label><input type="checkbox" class="filter-etr" value="false" checked onchange="updateDashboard()"> E.frz</label>
            </div>
        </div>

        <div class="control-group">
            <label>A.tr (Adapter State)</label>
            <div class="checkbox-panel">
                <label><input type="checkbox" class="filter-atr" value="false" checked onchange="updateDashboard()"> <span class="tag-blue">A.frz (Blue)</span></label>
                <label><input type="checkbox" class="filter-atr" value="true" checked onchange="updateDashboard()"> <span class="tag-red">A.tr (Red)</span></label>
            </div>
        </div>

        <div class="stats-badge" id="stats-badge">Showing 0 / 0 Runs</div>
    </div>

    <div id="chart-container">
        <div id="plotly-div" style="width:100%; height:950px;"></div>
    </div>

    <div id="table-container">
        <h3 style="margin-top:0; font-size:15px; color:#2c3e50;">Evaluated Experiments Data Table</h3>
        <table>
            <thead>
                <tr>
                    <th>Config #</th>
                    <th>Emb Init</th>
                    <th>E.tr</th>
                    <th>Adapter Init</th>
                    <th>A.tr</th>
                    <th>CEFR wF1 ↑</th>
                    <th>CEFR MAE ↓</th>
                    <th>Polarity wF1 ↑</th>
                    <th>Polarity MCC ↑</th>
                    <th>Load wF1 ↑</th>
                    <th> Load MCC ↑</th>
                </tr>
            </thead>
            <tbody id="table-body"></tbody>
        </table>
    </div>

    <script>
        const rawData = {json.dumps(evaluated_data)};

        function getCheckedValues(className) {{
            return Array.from(document.querySelectorAll('.' + className + ':checked')).map(cb => cb.value);
        }}

        function formatAdapterInit(val) {{
            if (val === 'Scratch') return 'scr';
            if (val === 'Pretrained') return 'pre';
            return val;
        }}

        function updateDashboard() {{
            const mode = document.getElementById('metric-mode').value;
            const selectedEmbs = getCheckedValues('filter-emb');
            const selectedAdapters = getCheckedValues('filter-adapter');
            const selectedEtr = getCheckedValues('filter-etr');
            const selectedAtr = getCheckedValues('filter-atr');

            const filtered = rawData.filter(d => {{
                if (!selectedEmbs.includes(d.Emb_Init)) return false;
                if (!selectedAdapters.includes(d.Adapter_Init)) return false;
                if (!selectedEtr.includes(String(d.E_tr))) return false;
                if (!selectedAtr.includes(String(d.A_tr))) return false;
                return true;
            }});

            document.getElementById('stats-badge').innerText = `Showing ${{filtered.length}} / ${{rawData.length}} Evaluated Runs`;

            const tbody = document.getElementById('table-body');
            tbody.innerHTML = '';
            filtered.forEach(r => {{
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>#${{r.Config}}</strong></td>
                    <td>${{r.Emb_Init}}</td>
                    <td><span class="${{r.E_tr ? 'tag-red' : 'tag-blue'}}">${{r.E_tr ? '✓' : ''}}</span></td>
                    <td>${{r.Adapter_Init}}</td>
                    <td><span class="${{r.A_tr ? 'tag-red' : 'tag-blue'}}">${{r.A_tr ? '✓' : ''}}</span></td>
                    <td>${{r.CEFR_wF1 !== undefined ? r.CEFR_wF1.toFixed(2) : '-'}}</td>
                    <td>${{r.CEFR_MAE !== undefined ? r.CEFR_MAE.toFixed(2) : '-'}}</td>
                    <td>${{r.Polarity_wF1 !== undefined ? r.Polarity_wF1.toFixed(2) : '-'}}</td>
                    <td>${{r.Polarity_MCC !== undefined ? r.Polarity_MCC.toFixed(2) : '-'}}</td>
                    <td>${{r.Load_wF1 !== undefined ? r.Load_wF1.toFixed(2) : '-'}}</td>
                    <td>${{r.Load_MAE !== undefined ? r.Load_MAE.toFixed(2) : '-'}}</td>
                `;
                tbody.appendChild(tr);
            }});

            const metrics = mode === 'wF1' ? [
                {{ key: 'CEFR_wF1', title: 'CEFR Level (wF1 ↑)', axis: 'y' }},
                {{ key: 'Polarity_wF1', title: 'Emotion Polarity (wF1 ↑)', axis: 'y2' }},
                {{ key: 'Load_wF1', title: 'Emotion Load (wF1 ↑)', axis: 'y3' }}
            ] : [
                {{ key: 'CEFR_MAE', title: 'CEFR Level (MAE ↓)', axis: 'y' }},
                {{ key: 'Polarity_MCC', title: 'Emotion Polarity (MCC ↑)', axis: 'y2' }},
                {{ key: 'Load_MAE', title: 'Emotion Load (MAE ↓)', axis: 'y3' }}
            ];

            const groupKeys = Array.from(new Set(filtered.map(r => `${{r.Emb_Init}} | ${{r.E_tr ? 'E.tr' : 'E.frz'}} | ${{formatAdapterInit(r.Adapter_Init)}}`)));

            const traces = [];
            const states = [
                {{ isAtr: false, name: 'Adapter Frozen (A.frz)', color: '#2b5c8f' }},
                {{ isAtr: true, name: 'Adapter Trainable (A.tr)', color: '#c0392b' }}
            ];

            states.forEach(state => {{
                metrics.forEach((m, mIdx) => {{
                    const xVals = [];
                    const yVals = [];
                    const hoverTexts = [];

                    groupKeys.forEach(gKey => {{
                        const match = filtered.find(r => `${{r.Emb_Init}} | ${{r.E_tr ? 'E.tr' : 'E.frz'}} | ${{formatAdapterInit(r.Adapter_Init)}}` === gKey && r.A_tr === state.isAtr);
                        if (match) {{
                            xVals.push(gKey);
                            yVals.push(match[m.key]);
                            hoverTexts.push(`<b>Config #${{match.Config}}</b><br>${{gKey}}<br>${{state.name}}<br>${{m.title}}: ${{match[m.key].toFixed(2)}}`);
                        }}
                    }});

                    if (xVals.length > 0) {{
                        traces.push({{
                            x: xVals,
                            y: yVals,
                            text: yVals.map(v => v.toFixed(2)),
                            textposition: 'outside',
                            textfont: {{ size: 10, color: '#333' }},
                            cliponaxis: false,
                            name: state.name,
                            legendgroup: state.name,
                            showlegend: (mIdx === 0),
                            type: 'bar',
                            xaxis: mIdx === 0 ? 'x' : (mIdx === 1 ? 'x2' : 'x3'),
                            yaxis: m.axis,
                            marker: {{ color: state.color }},
                            hoverinfo: 'text',
                            hovertext: hoverTexts
                        }});
                    }}
                }});
            }});

            const layout = {{
                grid: {{ rows: 3, columns: 1, pattern: 'independent', roworder: 'top to bottom' }},
                margin: {{ t: 40, b: 80, l: 60, r: 40 }},
                showlegend: true,
                legend: {{ orientation: 'h', x: 0, y: 1.05 }},
                barmode: 'group',
                template: 'plotly_white',
                yaxis: {{ title: metrics[0].title }},
                yaxis2: {{ title: metrics[1].title }},
                yaxis3: {{ title: metrics[2].title }},
                xaxis: {{ showticklabels: true, tickangle: 0 }},
                xaxis2: {{ showticklabels: true, tickangle: 0 }},
                xaxis3: {{ showticklabels: true, tickangle: 0 }}
            }};

            Plotly.react('plotly-div', traces, layout);
        }}

        updateDashboard();
    </script>
</body>
</html>
"""

# 4. Save to dashboard.html
with open("dashboard.html", "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"Successfully generated dashboard.html with {len(evaluated_data)} evaluated runs.")