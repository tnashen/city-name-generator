// ── Tabs ──────────────────────────────────────────────────
document.querySelectorAll('.tab').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
  });
});

function setActive(g, el) { g.forEach(b => b.classList.remove('active')); el.classList.add('active'); }

const catBtns    = document.querySelectorAll('.cat-btn');
catBtns.forEach(b => b.addEventListener('click', () => setActive(catBtns, b)));
const genCatBtns = document.querySelectorAll('.gen-cat-btn');
genCatBtns.forEach(b => b.addEventListener('click', () => setActive(genCatBtns, b)));
const countBtns  = document.querySelectorAll('.count-btn');
countBtns.forEach(b => b.addEventListener('click', () => setActive(countBtns, b)));

function copyName(text) { navigator.clipboard.writeText(text).catch(() => {}); }
function sleep(ms)      { return new Promise(r => setTimeout(r, ms)); }
function showError(el, msg) { el.innerHTML = `<div class="error-msg">⚠️ ${msg}</div>`; }
function showSpinner(el, msg) { el.innerHTML = `<div class="spinner">${msg}</div>`; }

const icons = ['🏙️','🏰','🚀','🏛️','⚔️','🌊','🌋','🗺️','🏔️','🌿'];

// ── Random ────────────────────────────────────────────────
document.getElementById('btn-random').addEventListener('click', async () => {
  const category = document.querySelector('.cat-btn.active')?.dataset.cat || 'all';
  const count    = parseInt(document.querySelector('.count-btn.active')?.dataset.n || '3');
  const out = document.getElementById('results-random');
  const btn = document.getElementById('btn-random');
  btn.disabled = true;
  showSpinner(out, 'Consulting the ancient maps...');
  try {
    const res  = await fetch(`/api/random?category=${encodeURIComponent(category)}&count=${count}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    let html = '<div class="name-list">';
    data.names.forEach((name, i) => {
      html += `<div class="name-card" onclick="copyName('${name}')" style="animation-delay:${i*.05}s">
        <span class="icon">${icons[i % icons.length]}</span>
        <span class="name-text">${name}</span>
        <span class="copy-hint">click to copy</span>
      </div>`;
    });
    html += '</div>';
    out.innerHTML = html;
  } catch (e) {
    showError(out, e.message);
  } finally {
    btn.disabled = false;
  }
});

// ── Generate ──────────────────────────────────────────────
document.getElementById('btn-generate').addEventListener('click', async () => {
  const description = document.getElementById('description').value.trim();
  const category    = document.querySelector('.gen-cat-btn.active')?.dataset.cat || 'any';
  const out = document.getElementById('results-generate');
  const btn = document.getElementById('btn-generate');
  if (!description) { showError(out, 'Please describe your city first.'); return; }
  btn.disabled = true;
  try {
    const res  = await fetch('/api/generate', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description, category }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    await pollJob(data.job_id, out);
  } catch (e) {
    showError(out, e.message);
  } finally {
    btn.disabled = false;
  }
});

async function pollJob(jobId, out) {
  const MAX_WAIT = 120000;
  const started  = Date.now();
  while (Date.now() - started < MAX_WAIT) {
    await sleep(2000);
    const res  = await fetch(`/api/generate/status/${jobId}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    if      (data.status === 'queued')     showSpinner(out, `Position ${data.position} in queue...`);
    else if (data.status === 'processing') showSpinner(out, 'The cartographer is naming your city...');
    else if (data.status === 'done') {
      const names = Array.isArray(data.result?.names) ? data.result.names : [];
      if (!names.length) { showError(out, 'No names returned. Please try again.'); return; }
      const reasoning = data.result?.reasoning || '';
      let html = '<div class="name-list">';
      names.forEach((name, i) => {
        html += `<div class="name-card" onclick="copyName('${name}')" style="animation-delay:${i*.05}s">
          <span class="icon">${icons[i % icons.length]}</span>
          <span class="name-text">${name}</span>
          <span class="copy-hint">click to copy</span>
        </div>`;
      });
      html += '</div>';
      if (reasoning) {
        const parts = reasoning.split(/\s{2,}(?=\*\*)/).filter(Boolean);
        const fmt   = parts.map(p => `<p>${p.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')}</p>`).join('');
        html += `<div class="reasoning-box"><strong>◆ The Cartographer's Notes</strong>${fmt}</div>`;
      }
      out.innerHTML = html;
      return;
    } else if (data.status === 'error') {
      throw new Error(data.error || 'Generation failed');
    }
  }
  throw new Error('Timed out. Please try again.');
}
