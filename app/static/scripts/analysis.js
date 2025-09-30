const AnalysisUI = (function(){
  const state = {
    project: null,
    file: null,
    summary: null,
    numericStats: null,
    corr: null
  };

  function resolveProjectFile(){
    if (state.project && state.file) return;
    // Kaynak: upload tabındaki inputlar
    const p = document.getElementById('projectNameInput');
    // Varsayım: Yüklenen dosya bilgisi #file-details içinde "Dosya Adı:" satırıyla var
    const fileDetails = document.getElementById('file-details');
    let fileName = null;
    if (fileDetails){
      const txt = fileDetails.textContent || '';
      const match = txt.match(/Dosya Adı:\s*(\S+)/i);
      if (match) fileName = match[1];
    }
    state.project = state.project || (p && p.value.trim()) || null;
    state.file = state.file || fileName;
  }

  async function loadSummary(){
    resolveProjectFile();
    if(!state.project || !state.file){
      alert('Önce proje adı ve dosya yüklenmiş olmalı.');
      return;
    }
    const url = `/analysis/${encodeURIComponent(state.project)}/${encodeURIComponent(state.file)}/summary`;
    const res = await fetch(url);
    if(!res.ok){ alert('Summary alınamadı'); return; }
    const data = await res.json();
    state.summary = data.summary;
    state.numericStats = data.numeric_stats;
    renderSummary();
    renderNumericTable();
  }

  async function loadCorrelation(){
    resolveProjectFile();
    if(!state.project || !state.file){
      alert('Önce proje adı ve dosya yüklenmiş olmalı.');
      return;
    }
    const url = `/analysis/${encodeURIComponent(state.project)}/${encodeURIComponent(state.file)}/correlation`;
    const res = await fetch(url);
    if(!res.ok){ alert('Korelasyon alınamadı'); return; }
    state.corr = await res.json();
    renderCorrelation();
  }

  function renderSummary(){
    const s = state.summary || {}; 
    setText('an-rows', s.rows);
    setText('an-cols', s.cols);
    setText('an-file-size', s.file_size_human || '-');
    setText('an-num-count', s.numeric_count);
    setText('an-cat-count', s.categorical_count);
    setText('an-sample', s.sample_limited ? 'Evet' : 'Hayır');
  }

  function renderNumericTable(){
    const holder = document.getElementById('an-numeric-table');
    if(!holder) return;
    const stats = state.numericStats || {};
    const keys = Object.keys(stats);
    if(!keys.length){ holder.innerHTML = '<div style="text-align:center; opacity:.6;">Veri yok</div>'; return; }
    const columns = ['col','mean','std','var','min','q1','median','q3','max','iqr','skew','null_ratio'];
    let html = '<table class="an-table" style="width:100%; border-collapse:collapse;">';
    html += '<thead><tr>' + columns.map(c=>`<th style=\"position:sticky;top:0;background:#0f172a;color:#94a3b8;font-weight:600;font-size:11px;padding:4px;\">${c}</th>`).join('') + '</tr></thead><tbody>';
    for(const col of keys){
      const st = stats[col];
      html += '<tr>' + columns.map(c=>{
        let v = (c==='col')? col : (st[c]===null||st[c]===undefined?'-': st[c]);
        if(typeof v === 'number') v = Number(v).toPrecision(4);
        const safe = esc(String(v));
        return `<td style=\"border-top:1px solid #1e293b;padding:3px 4px;font-size:11px;\">${safe}</td>`;
      }).join('') + '</tr>';
    }
    html += '</tbody></table>';
    holder.innerHTML = html;
  }

  function renderCorrelation(){
    const canvas = document.getElementById('an-corr-canvas');
    if(!canvas) return;
    const ctx = canvas.getContext('2d');
    const corr = state.corr;
    if(!corr || !corr.columns.length){
      ctx.clearRect(0,0,canvas.width,canvas.height);
      ctx.fillStyle = '#64748b';
      ctx.font = '12px sans-serif';
      ctx.fillText('Korelasyon verisi yok', 10, 20);
      return;
    }
    // Basit ısı haritası
    const cols = corr.columns;
    const m = corr.matrix;
    const n = cols.length;
    const size = Math.min(Math.floor((canvas.width - 120)/n), Math.floor((canvas.height - 60)/n));
    const startX = 100; const startY = 20;
    // Eksen başlıkları
    ctx.clearRect(0,0,canvas.width,canvas.height);
    ctx.font = '10px sans-serif';
    ctx.fillStyle = '#e2e8f0';
    // Column labels (x)
    for(let i=0;i<n;i++){
      ctx.save();
      ctx.translate(startX + i*size + size/2, startY - 5);
      ctx.rotate(-Math.PI/4);
      ctx.textAlign = 'right';
      ctx.fillText(cols[i],0,0);
      ctx.restore();
    }
    // Row labels (y)
    for(let i=0;i<n;i++){
      ctx.textAlign = 'right';
      ctx.fillText(cols[i], startX - 6, startY + i*size + size/2+3);
    }
    // Cells
    for(let r=0;r<n;r++){
      for(let c=0;c<n;c++){
        const val = m[r][c];
        const color = heatColor(val);
        ctx.fillStyle = color;
        ctx.fillRect(startX + c*size, startY + r*size, size, size);
      }
    }
    // Legend (simple)
    const gradSteps = 50;
    for(let i=0;i<gradSteps;i++){
      const t = i/(gradSteps-1) * 2 - 1; // -1..1
      ctx.fillStyle = heatColor(t);
      ctx.fillRect(startX + n*size + 10, startY + i*(size*n)/gradSteps, 12, (size*n)/gradSteps);
    }
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px sans-serif';
    ctx.fillText('1.0', startX + n*size + 26, startY + 8);
    ctx.fillText('0', startX + n*size + 26, startY + (size*n)/2);
    ctx.fillText('-1.0', startX + n*size + 26, startY + size*n -4);
  }

  function heatColor(v){
    // v -1..1 -> mavi -> beyaz -> kırmızı
    const t = (v+1)/2; // 0..1
    const r = Math.round(255 * t);
    const g = Math.round(255 * (1 - Math.abs(t-0.5)*2));
    const b = Math.round(255 * (1-t));
    return `rgb(${r},${g},${b})`;
  }

  function setText(id, val){
    const el = document.getElementById(id);
    if(el) el.textContent = (val===undefined||val===null)?'-':val;
  }

  function esc(s){
    return s
      .replace(/&/g,'&amp;')
      .replace(/</g,'&lt;')
      .replace(/>/g,'&gt;')
      .replace(/"/g,'&quot;')
      .replace(/'/g,'&#39;');
  }

  return { state, loadSummary, loadCorrelation };
})();
