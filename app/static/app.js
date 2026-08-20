/* ==========================================================================
   AI Product Intelligence Engine - Frontend Application Script
   ========================================================================== */

let currentResult = null;
let allSpecs = [];

const PRESETS = {
  bosch: {
    brand: "Bosch",
    mpn: "GSR 18V-55",
    desc: "18V Professional Cordless Drill Driver with Brushless Motor and 55Nm max torque"
  },
  apple: {
    brand: "Apple",
    mpn: "MRX33LL/A",
    desc: "MacBook Pro 14-inch with M3 Pro chip, 18GB Unified Memory, 512GB SSD"
  },
  fluke: {
    brand: "Fluke",
    mpn: "Fluke-117",
    desc: "Electricians Multimeter with Non-Contact Voltage Detection CAT III 600V"
  },
  dewalt: {
    brand: "DeWalt",
    mpn: "DCD791B",
    desc: "20V MAX XR Li-Ion Brushless Compact Drill/Driver 1/2-Inch"
  }
};

function loadPreset(key) {
  const p = PRESETS[key];
  if (!p) return;
  document.getElementById('brand-input').value = p.brand;
  document.getElementById('mpn-input').value = p.mpn;
  document.getElementById('desc-input').value = p.desc;
}

document.addEventListener('DOMContentLoaded', () => {
  checkAPIHealth();

  const form = document.getElementById('product-form');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    await processEnrichment();
  });
});

const API_BASE = (window.location.protocol === 'file:' || (window.location.port !== '8000' && window.location.hostname === '')) 
  ? 'http://127.0.0.1:8000' 
  : (window.location.origin.includes('8000') ? '' : 'http://127.0.0.1:8000');

async function checkAPIHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) {
      document.getElementById('api-status').style.opacity = '1';
    }
  } catch (err) {
    document.getElementById('api-status').innerHTML = '<span class="status-dot" style="background:var(--accent-rose)"></span> API OFFLINE';
  }
}

async function processEnrichment() {
  const brand = document.getElementById('brand-input').value.trim();
  const mpn = document.getElementById('mpn-input').value.trim();
  const description = document.getElementById('desc-input').value.trim();

  const btn = document.getElementById('btn-submit');
  btn.disabled = true;
  btn.innerHTML = '<span>⏳ Processing Pipeline...</span>';

  // Animate Stepper
  await animateStepper();

  try {
    const res = await fetch(`${API_BASE}/api/v1/enrich`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ brand, mpn, description })
    });

    if (!res.ok) {
      throw new Error(`API error: ${res.statusText}`);
    }

    const data = await res.json();
    currentResult = data;
    renderResults(data);

  } catch (err) {
    alert(`Failed to enrich product: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span>⚡ Enrich & Process Product Intelligence</span>';
  }
}

async function animateStepper() {
  for (let i = 1; i <= 6; i++) {
    const el = document.getElementById(`step-${i}`);
    el.className = 'step-card active';
    await new Promise(r => setTimeout(r, 150));
    el.className = 'step-card completed';
  }
}

function renderResults(data) {
  document.getElementById('results-wrapper').style.display = 'block';

  // 1. Identity & Classification
  document.getElementById('res-brand-badge').innerText = data.identity.normalized_brand.toUpperCase();
  document.getElementById('res-product-name').innerText = data.identity.product_name;

  const taxBox = document.getElementById('res-taxonomy-box');
  taxBox.innerHTML = '';
  data.classification.category_path.forEach(cat => {
    const pill = document.createElement('span');
    pill.className = 'tax-pill';
    pill.innerText = cat;
    taxBox.appendChild(pill);
  });

  if (data.classification.unspsc_code) {
    const unspscPill = document.createElement('span');
    unspscPill.className = 'tax-code-pill';
    unspscPill.innerText = `UNSPSC ${data.classification.unspsc_code}`;
    taxBox.appendChild(unspscPill);
  }

  if (data.classification.hs_code) {
    const hsPill = document.createElement('span');
    hsPill.className = 'tax-code-pill';
    hsPill.innerText = `HS ${data.classification.hs_code}`;
    taxBox.appendChild(hsPill);
  }

  // 2. Confidence Score Gauge
  const scorePct = Math.round(data.confidence.overall_score * 100);
  document.getElementById('gauge-circle').style.setProperty('--score-pct', scorePct);
  document.getElementById('res-overall-score').innerText = `${scorePct}%`;
  document.getElementById('res-verified-count').innerText = data.confidence.verified_attributes_count;
  document.getElementById('res-unverified-count').innerText = `${data.confidence.unverified_attributes_count} Unverified`;

  // 3. Specifications Table
  allSpecs = data.specifications;
  renderSpecCategories(allSpecs);
  renderSpecsTable(allSpecs);

  // 4. Conflicts
  const conflictContainer = document.getElementById('conflicts-container');
  conflictContainer.innerHTML = '';
  if (data.conflicts && data.conflicts.length > 0) {
    document.getElementById('conflicts-card').style.display = 'block';
    data.conflicts.forEach(c => {
      const item = document.createElement('div');
      item.className = 'conflict-item';
      item.innerHTML = `
        <div class="conflict-header">
          <span>⚠️ Attribute Discrepancy: ${c.attribute}</span>
          <span>Resolved: ${c.resolved_value}</span>
        </div>
        <div class="competing-box">
          ${c.competing_values.map(v => `<span class="competing-pill">${v.value} (Src: ${v.source_id}, Weight: ${v.reliability})</span>`).join('')}
        </div>
        <div class="conflict-reason">${c.resolution_reason}</div>
      `;
      conflictContainer.appendChild(item);
    });
  } else {
    document.getElementById('conflicts-card').style.display = 'block';
    conflictContainer.innerHTML = '<div style="color: var(--accent-emerald); font-weight: 600; font-size: 13px;">✓ Zero cross-source conflicts detected. Full agreement across datasheets.</div>';
  }

  // 5. Commerce Deliverables
  document.getElementById('res-commerce-title').innerText = data.commerce.title;
  document.getElementById('res-commerce-desc').innerText = data.commerce.short_description;

  const bulletList = document.getElementById('res-feature-bullets');
  bulletList.innerHTML = '';
  data.commerce.feature_bullets.forEach(b => {
    const li = document.createElement('li');
    li.innerText = b;
    bulletList.appendChild(li);
  });

  // 6. JSON Viewer
  document.getElementById('json-output').innerText = JSON.stringify(data, null, 2);

  // Scroll smoothly to results
  document.getElementById('results-wrapper').scrollIntoView({ behavior: 'smooth' });
}

function renderSpecCategories(specs) {
  const bar = document.getElementById('spec-filter-bar');
  bar.innerHTML = '<button class="filter-chip active" onclick="filterSpecs(\'ALL\', this)">All Specifications</button>';
  
  const categories = [...new Set(specs.map(s => s.category))];
  categories.forEach(cat => {
    const chip = document.createElement('button');
    chip.className = 'filter-chip';
    chip.innerText = cat;
    chip.onclick = (e) => filterSpecs(cat, chip);
    bar.appendChild(chip);
  });
}

function filterSpecs(category, chipElement) {
  if (chipElement) {
    document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
    chipElement.classList.add('active');
  }

  if (category === 'ALL') {
    renderSpecsTable(allSpecs);
  } else {
    const filtered = allSpecs.filter(s => s.category === category);
    renderSpecsTable(filtered);
  }
}

function renderSpecsTable(specs) {
  const tbody = document.getElementById('specs-tbody');
  tbody.innerHTML = '';

  specs.forEach(s => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="spec-key">${s.key}</td>
      <td>
        <span class="spec-val-badge">${s.value} ${s.unit ? `<span class="unit-tag">${s.unit}</span>` : ''}</span>
      </td>
      <td><span class="tax-pill">${s.category}</span></td>
      <td>
        <span style="color:${s.confidence >= 0.9 ? 'var(--accent-emerald)' : 'var(--accent-amber)'}; font-weight:700;">
          ${Math.round(s.confidence * 100)}%
        </span>
      </td>
      <td>
        <button class="btn-evidence" onclick="showEvidence('${encodeURIComponent(s.key)}', '${encodeURIComponent(s.evidence)}')">
          🔍 View Quote Snippet
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function showEvidence(key, evidence) {
  document.getElementById('modal-spec-title').innerText = `Evidence: ${decodeURIComponent(key)}`;
  document.getElementById('modal-evidence-text').innerText = decodeURIComponent(evidence);
  document.getElementById('evidence-modal').classList.add('open');
}

function closeModal() {
  document.getElementById('evidence-modal').classList.remove('open');
}

function copyJSON() {
  if (!currentResult) return;
  navigator.clipboard.writeText(JSON.stringify(currentResult, null, 2));
  alert('JSON copied to clipboard!');
}

function downloadJSON() {
  if (!currentResult) return;
  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentResult, null, 2));
  const downloadAnchor = document.createElement('a');
  downloadAnchor.setAttribute("href", dataStr);
  downloadAnchor.setAttribute("download", `${currentResult.identity.normalized_mpn}_intelligence.json`);
  document.body.appendChild(downloadAnchor);
  downloadAnchor.click();
  downloadAnchor.remove();
}
