import requests
import json

API_URL = "https://api.weatherstack.com/current?access_key=9c629f7cd976d6a3c526bc1eaa5b6b75&query=-10.1840,-48.3336"

try:
    response = requests.get(API_URL)
    response.raise_for_status()
    data = response.json()

    # Extract key info based on weatherstack structure and example D.JSON fields
    location = data.get('location', {})
    current = data.get('current', {})
    astro = current.get('astro', {}) if 'astro' in current else data.get('astro', {})
    air_quality = current.get('air_quality', {})

    loc_name = location.get('name', 'N/A')
    country = location.get('country', 'N/A')
    region = location.get('region', 'N/A')
    temp = current.get('temperature', 0)
    weather_desc = current.get('weather_descriptions', ['N/A'])[0] if current.get('weather_descriptions') else 'N/A'
    weather_icon = current.get('weather_icons', [''])[0] if current.get('weather_icons') else ''
    weather_icon = weather_icon.replace('\\/', '/')
    print(weather_icon)
    feelslike = current.get('feelslike', 0)
    wind_speed = current.get('wind_speed', 0)
    wind_dir = current.get('wind_dir', 'N/A')
    pressure = current.get('pressure', 0)
    precip = current.get('precip', 0)
    humidity = current.get('humidity', 0)
    cloudcover = current.get('cloudcover', 0)
    uv_index = current.get('uv_index', 0)
    visibility = current.get('visibility', 0)
    sunrise = astro.get('sunrise', 'N/A')
    sunset = astro.get('sunset', 'N/A')
    air_index = air_quality.get('us-epa-index', air_quality.get('gb-defra-index', 'N/A'))

    # Beautiful dark minimalist HTML with rounded corners, shadows, diamond charcoal theme, hover effects
    html_content = f'''<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório do Clima</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0f0f0f;
            --bg-gradient: linear-gradient(135deg, #0f0f0f 0%, #1a1a2e 40%, #16213e 100%);
            --card-bg: #1e1e2e;
            --accent: #2d1b69;
            --accent-glow: rgba(45, 27, 105, 0.6);
            --text-primary: #e0e0e0;
            --text-secondary: #a0a0a0;
            --shadow: 0 20px 40px rgba(0,0,0,0.6);
            --shadow-hover: 0 25px 50px var(--accent-glow);
        }}
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-gradient);
            min-height: 100vh;
            color: var(--text-primary);
            padding: 2rem 1rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            line-height: 1.6;
        }}
        .container {{
            max-width: 900px;
            width: 100%;
        }}
        .header {{
            background: linear-gradient(135deg, var(--accent), var(--card-bg));
            border-radius: 24px;
            padding: 3rem 2.5rem;
            text-align: center;
            box-shadow: var(--shadow);
            margin-bottom: 2.5rem;
            transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.05);
        }}
        .header:hover {{
            transform: translateY(-8px) scale(1.02);
            box-shadow: var(--shadow-hover);
        }}
        .location {{
            font-size: 1.4rem;
            font-weight: 500;
            opacity: 0.95;
            margin-bottom: 1rem;
            color: #fff;
        }}
        .temp {{
            font-size: 5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #fff, #f0f0f0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 1.5rem;
            letter-spacing: -2px;
        }}
        .weather-info {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1.5rem;
            font-size: 1.3rem;
            font-weight: 600;
            color: var(--text-primary);
        }}
        .weather-icon {{
            width: 90px;
            height: 90px;
            border-radius: 16px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.4);
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2.5rem;
        }}
        .stat-card {{
            background: var(--card-bg);
            border-radius: 20px;
            padding: 1.8rem 1.5rem;
            text-align: center;
            box-shadow: 0 12px 32px rgba(0,0,0,0.5);
            transition: all 0.3s ease;
            border: 1px solid rgba(255,255,255,0.08);
            cursor: pointer;
        }}
        .stat-card:hover {{
            transform: translateY(-10px) scale(1.03);
            box-shadow: 0 20px 45px var(--accent-glow);
            border-color: var(--accent);
        }}
        .stat-value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 0.5rem;
        }}
        .stat-label {{
            font-size: 0.95rem;
            color: var(--text-secondary);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .astro {{
            background: linear-gradient(135deg, var(--card-bg), var(--accent));
            border-radius: 20px;
            padding: 2rem;
            display: flex;
            justify-content: space-evenly;
            align-items: center;
            box-shadow: 0 12px 32px rgba(0,0,0,0.5);
            margin-bottom: 2rem;
            transition: all 0.3s ease;
            border: 1px solid rgba(255,255,255,0.08);
        }}
        .astro:hover {{
            transform: scale(1.015);
            box-shadow: 0 20px 45px var(--accent-glow);
        }}
        .astro-item {{
            text-align: center;
            flex: 1;
        }}
        .astro-value {{
            font-size: 1.6rem;
            font-weight: 700;
            color: #fff;
            margin-bottom: 0.3rem;
        }}
        .astro-label {{
            font-size: 0.9rem;
            color: var(--text-secondary);
            font-weight: 500;
        }}
        .air-quality {{
            background: var(--card-bg);
            border-radius: 20px;
            padding: 2.5rem;
            text-align: center;
            box-shadow: 0 12px 32px rgba(0,0,0,0.5);
            transition: all 0.3s ease;
            border: 1px solid rgba(255,255,255,0.08);
        }}
        .air-quality:hover {{
            transform: translateY(-10px);
            box-shadow: 0 20px 45px var(--accent-glow);
            border-color: var(--accent);
        }}
        .air-index {{
            font-size: 3rem;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 0.8rem;
        }}
        .air-label {{
            font-size: 1.1rem;
            color: var(--text-secondary);
            font-weight: 500;
        }}
        @media (max-width: 768px) {{
            body {{ padding: 1rem; }}
            .temp {{ font-size: 3.5rem; }}
            .stats-grid {{ grid-template-columns: 1fr 1fr; }}
            .astro {{ flex-direction: column; gap: 1.5rem; }}
            .header {{ padding: 2rem 1.5rem; }}
        }}
        @media (max-width: 480px) {{
            .stats-grid {{ grid-template-columns: 1fr; }}
            .weather-info {{ flex-direction: column; gap: 1rem; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="location">{loc_name}, {region}, {country}</div>
            <div class="temp">{temp}&deg;C</div>
            <div class="weather-info">
                {f"<img src='{weather_icon}' alt='{weather_desc}' class='weather-icon'>" if weather_icon else ''}
                <span>{weather_desc}</span>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{feelslike}&deg;C</div>
                <div class="stat-label">Feels Like</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{wind_speed} km/h<br><small style="font-size:0.7em">{wind_dir}</small></div>
                <div class="stat-label">Vento</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{humidity}%</div>
                <div class="stat-label">Umidade</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{pressure} hPa</div>
                <div class="stat-label">Pressão</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{precip} mm</div>
                <div class="stat-label">Precipitação</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{cloudcover}%</div>
                <div class="stat-label">Nuvens</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{uv_index}</div>
                <div class="stat-label">UV Index</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{visibility} km</div>
                <div class="stat-label">Visibilidade</div>
            </div>
        </div>

        <div class="astro">
            <div class="astro-item">
                <div class="astro-value">{sunrise}</div>
                <div class="astro-label">Nascer do Sol</div>
            </div>
            <div class="astro-item">
                <div class="astro-value">{sunset}</div>
                <div class="astro-label">Pôr do Sol</div>
            </div>
        </div>

        <div class="air-quality">
            <div class="air-index">{air_index}</div>
            <div class="air-label">Qualidade do Ar (EPA Index)</div>
        </div>
    </div>
</body>
</html>'''

    with open('report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("✓ Relatório de clima gerado com sucesso: report.html")
    print("Abra no seu navegador!")

except requests.RequestException as e:
    print(f"Erro na requisição API: {e}")
    with open('report.html', 'w', encoding='utf-8') as f:
        f.write('''<!DOCTYPE html><html><body style="background: #0f0f0f; color: white; font-family: Inter, sans-serif; padding: 4rem; text-align: center; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.8);"><h1 style="font-size: 2.5rem; color: #2d1b69;">Erro ao Carregar Dados</h1><p>Tente novamente mais tarde.</p></body></html>''')
except Exception as e:
    print(f"Erro inesperado: {e}")
