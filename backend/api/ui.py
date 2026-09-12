"""
Interactive Browser UI for TruthTrace Forensic Investigation Engine.
"""

def get_html_ui() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TruthTrace | Forensic Intelligence Engine</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0b0f19;
      --card-bg: #111827;
      --border: #1f2937;
      --text: #f3f4f6;
      --muted: #9ca3af;
      --accent: #3b82f6;
      --accent-hover: #2563eb;
      --false: #ef4444;
      --true: #10b981;
      --misleading: #f59e0b;
      --unverified: #6b7280;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 30px 20px;
    }
    .container {
      max-width: 1000px;
      margin: 0 auto;
    }
    header {
      text-align: center;
      margin-bottom: 35px;
    }
    .badge-logo {
      display: inline-block;
      background: rgba(59, 130, 246, 0.15);
      color: #60a5fa;
      padding: 6px 14px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 600;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      margin-bottom: 12px;
      border: 1px solid rgba(59, 130, 246, 0.3);
    }
    h1 {
      font-size: 32px;
      font-weight: 800;
      letter-spacing: -0.5px;
      margin-bottom: 8px;
      background: linear-gradient(135deg, #ffffff 0%, #94a3b8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    header p {
      color: var(--muted);
      font-size: 15px;
    }
    .search-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
      margin-bottom: 25px;
    }
    .input-wrapper {
      display: flex;
      gap: 12px;
    }
    input[type="text"] {
      flex: 1;
      background: #0d1322;
      border: 1px solid #2d3748;
      border-radius: 10px;
      padding: 14px 18px;
      font-size: 16px;
      color: #ffffff;
      outline: none;
      transition: all 0.2s ease;
    }
    input[type="text"]:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
    }
    button.btn-primary {
      background: var(--accent);
      color: white;
      border: none;
      padding: 14px 28px;
      border-radius: 10px;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s ease;
      white-space: nowrap;
    }
    button.btn-primary:hover {
      background: var(--accent-hover);
    }
    .sample-queries {
      margin-top: 14px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
    }
    .sample-label {
      font-size: 12px;
      color: var(--muted);
      font-weight: 500;
      margin-right: 4px;
    }
    .chip {
      background: #1e293b;
      color: #cbd5e1;
      border: 1px solid #334155;
      padding: 4px 12px;
      border-radius: 999px;
      font-size: 12px;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .chip:hover {
      background: #334155;
      color: white;
      border-color: var(--accent);
    }
    #loading {
      display: none;
      text-align: center;
      padding: 40px;
    }
    .spinner {
      width: 40px;
      height: 40px;
      border: 3px solid rgba(59, 130, 246, 0.2);
      border-top-color: var(--accent);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      margin: 0 auto 15px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    #resultArea {
      display: none;
    }
    .verdict-header {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }
    .verdict-tag {
      font-size: 26px;
      font-weight: 800;
      text-transform: uppercase;
      padding: 8px 20px;
      border-radius: 10px;
      letter-spacing: 1px;
    }
    .tag-false { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }
    .tag-true { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }
    .tag-misleading { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }
    .tag-unverified { background: rgba(107, 114, 128, 0.15); color: #9ca3af; border: 1px solid rgba(107, 114, 128, 0.4); }
    .confidence-box {
      text-align: right;
    }
    .conf-val {
      font-size: 28px;
      font-weight: 800;
      font-family: 'JetBrains Mono', monospace;
    }
    .conf-label {
      font-size: 12px;
      color: var(--muted);
      text-transform: uppercase;
    }
    .section-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 24px;
      margin-bottom: 20px;
    }
    .section-title {
      font-size: 16px;
      font-weight: 700;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }
    .meta-box {
      background: #0d1322;
      border: 1px solid #1f2937;
      border-radius: 10px;
      padding: 14px;
    }
    .meta-box .k { font-size: 11px; text-transform: uppercase; color: var(--muted); font-weight: 600; margin-bottom: 4px; }
    .meta-box .v { font-size: 14px; color: #e2e8f0; }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    th {
      text-align: left;
      padding: 12px 14px;
      background: #0d1322;
      color: var(--muted);
      font-weight: 600;
      border-bottom: 1px solid var(--border);
    }
    td {
      padding: 12px 14px;
      border-bottom: 1px solid #1f2937;
      vertical-align: top;
    }
    tr:last-child td { border-bottom: none; }
    .time-cell { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #94a3b8; }
    .source-tag { font-weight: 600; color: #60a5fa; }
    .tier-badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
    }
    .tier-registry { background: rgba(59, 130, 246, 0.2); color: #93c5fd; }
    .tier-mainstream { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; }
    .tier-unverified { background: rgba(107, 114, 128, 0.2); color: #d1d5db; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="badge-logo">Live Multi-Agent Pipeline</div>
      <h1>TruthTrace Forensic Intelligence</h1>
      <p>Autonomous misinformation verification, diffusion timeline reconstruction & registry debunks</p>
    </header>

    <div class="search-card">
      <form id="analyzeForm" onsubmit="handleAnalyze(event)">
        <div class="input-wrapper">
          <input type="text" id="claimInput" placeholder="Enter scientific claim, research headline, or publication URL..." required autofocus autocomplete="off" />
          <button type="submit" class="btn-primary" id="submitBtn">Verify Claim</button>
        </div>
      </form>
      <div class="sample-queries">
        <span class="sample-label">Try scientific sample:</span>
        <button class="chip" onclick="fillClaim('James Webb Space Telescope detected atmospheric carbon dioxide on exoplanet WASP-39 b')">JWST Exoplanet CO2</button>
        <button class="chip" onclick="fillClaim('South Korean researchers synthesized room-temperature ambient pressure superconductor LK-99')">LK-99 Superconductor</button>
        <button class="chip" onclick="fillClaim('COVID-19 mRNA vaccines permanently alter and integrate into human genomic DNA')">mRNA Vaccine DNA Alteration</button>
        <button class="chip" onclick="fillClaim('5G mobile networks spread coronavirus or weaken human immune system')">5G Viral Transmission</button>
      </div>
    </div>

    <div id="loading">
      <div class="spinner"></div>
      <p style="color: #94a3b8; font-size: 14px;">Deploying 8 forensic agents across OSINT, registry fact-checks & timelines...</p>
    </div>

    <div id="resultArea">
      <div class="verdict-header">
        <div>
          <div style="font-size: 12px; color: var(--muted); text-transform: uppercase; margin-bottom: 4px;">Forensic Verdict</div>
          <div id="verdictTag" class="verdict-tag">FALSE</div>
        </div>
        <div class="confidence-box">
          <div id="confVal" class="conf-val">95%</div>
          <div class="conf-label">Confidence Score</div>
        </div>
      </div>

      <div class="section-card">
        <div class="section-title">Narrative & Motive Profile</div>
        <div class="grid-2">
          <div class="meta-box"><div class="k">Core Narrative</div><div class="v" id="narrativeCore">-</div></div>
          <div class="meta-box"><div class="k">Plausible Intent</div><div class="v" id="narrativeIntent">-</div></div>
          <div class="meta-box"><div class="k">Emotional Hooks</div><div class="v" id="narrativeHooks">-</div></div>
          <div class="meta-box"><div class="k">Target Demographic</div><div class="v" id="narrativeTarget">-</div></div>
        </div>
      </div>

      <div class="section-card">
        <div class="section-title">Chronological Propagation Timeline</div>
        <div style="overflow-x: auto;">
          <table>
            <thead>
              <tr>
                <th style="width: 170px;">Timestamp</th>
                <th style="width: 200px;">Platform / Source</th>
                <th>Discovered Mention / Article</th>
                <th style="width: 100px;">Tier</th>
              </tr>
            </thead>
            <tbody id="timelineBody"></tbody>
          </table>
        </div>
      </div>

      <div class="section-card">
        <div class="section-title">Corroborating & Registry Evidence</div>
        <ul id="sourcesList" style="list-style: none;"></ul>
      </div>
    </div>
  </div>

  <script>
    function fillClaim(text) {
      document.getElementById('claimInput').value = text;
      handleAnalyze();
    }

    async function handleAnalyze(e) {
      if (e) e.preventDefault();
      const claim = document.getElementById('claimInput').value.trim();
      if (!claim) return;

      const loading = document.getElementById('loading');
      const resultArea = document.getElementById('resultArea');
      const submitBtn = document.getElementById('submitBtn');

      loading.style.display = 'block';
      resultArea.style.display = 'none';
      submitBtn.disabled = true;
      submitBtn.innerText = 'Analyzing...';

      try {
        const payload = claim.startsWith('http') ? { url: claim } : { claim: claim };
        const res = await fetch('/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();

        // Render verdict
        const verdict = (data.overall_verdict || 'unverified').toLowerCase();
        const tag = document.getElementById('verdictTag');
        tag.innerText = verdict.toUpperCase();
        tag.className = 'verdict-tag tag-' + verdict;

        const conf = Math.round((data.overall_confidence || 0.5) * 100);
        document.getElementById('confVal').innerText = conf + '%';

        // Render Narrative
        const np = data.narrative_profile || {};
        document.getElementById('narrativeCore').innerText = np.core_narrative || 'Analysis of: ' + claim;
        document.getElementById('narrativeIntent').innerText = np.plausible_intent || 'Information diffusion';
        document.getElementById('narrativeHooks').innerText = (np.emotional_hooks || []).join(', ') || 'None';
        document.getElementById('narrativeTarget').innerText = np.target_demographic || 'General Public / Scientific Community';

        // Render Timeline
        const tBody = document.getElementById('timelineBody');
        tBody.innerHTML = '';
        const timeline = data.timeline || [];
        if (timeline.length === 0) {
          tBody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--muted);">No propagation timeline records found.</td></tr>';
        } else {
          timeline.forEach(ev => {
            const tr = document.createElement('tr');
            const timeStr = ev.timestamp ? ev.timestamp.substring(0, 19).replace('T', ' ') : 'Unknown';
            const tier = ev.credibility_tier || 'unverified';
            tr.innerHTML = `
              <td class="time-cell">${timeStr}</td>
              <td class="source-tag">${ev.source || 'Web Source'}</td>
              <td>${ev.title || ev.snippet || '-'}</td>
              <td><span class="tier-badge tier-${tier}">${tier}</span></td>
            `;
            tBody.appendChild(tr);
          });
        }

        // Render Evidence
        const srcList = document.getElementById('sourcesList');
        srcList.innerHTML = '';
        const subClaims = data.sub_claims || [];
        let count = 0;
        subClaims.forEach(sc => {
          (sc.evidence || []).forEach(ev => {
            count++;
            const li = document.createElement('li');
            li.style.padding = '8px 0';
            li.style.borderBottom = '1px solid #1f2937';
            const url = ev.source ? ev.source.url : '';
            li.innerHTML = `<strong>${ev.source ? ev.source.domain : 'Source'}:</strong> ${ev.excerpt} <br/><a href="${url}" target="_blank" style="color: #60a5fa; font-size: 12px; text-decoration: none;">${url}</a>`;
            srcList.appendChild(li);
          });
        });
        if (count === 0) {
          srcList.innerHTML = '<li style="color: var(--muted);">No external registry evidence linked.</li>';
        }

        resultArea.style.display = 'block';
      } catch (err) {
        alert('Analysis error: ' + err.message);
      } finally {
        loading.style.display = 'none';
        submitBtn.disabled = false;
        submitBtn.innerText = 'Verify Claim';
      }
    }
  </script>
</body>
</html>
"""
