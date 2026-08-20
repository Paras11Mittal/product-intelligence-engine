/* ==========================================================================
   AI Product Intelligence Engine - Frontend Application Script
   ========================================================================== */

let currentResult = null;
let allSpecs = [];
let csvProducts = [];
let csvBatchStart = 0;
const csvProcessedResults = new Map();

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

  document.getElementById('csv-input').addEventListener('change', handleCsvUpload);
  document.getElementById('btn-process-csv').addEventListener('click', processCsvBatch);
  document.getElementById('btn-previous-csv').addEventListener('click', () => moveCsvBatch(-1));
  document.getElementById('btn-next-csv').addEventListener('click', () => moveCsvBatch(1));
  document.getElementById('csv-start-row').addEventListener('change', selectCsvStartRow);
  document.getElementById('csv-batch-size').addEventListener('change', updateCsvBatchView);
  document.getElementById('btn-download-csv').addEventListener('click', downloadProcessedCsv);
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

function parseCsv(text) {
  const rows = [];
  let row = [];
  let value = '';
  let quoted = false;

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    if (char === '"') {
      if (quoted && text[i + 1] === '"') {
        value += '"';
        i += 1;
      } else {
        quoted = !quoted;
      }
    } else if (char === ',' && !quoted) {
      row.push(value.trim());
      value = '';
    } else if ((char === '\n' || char === '\r') && !quoted) {
      if (char === '\r' && text[i + 1] === '\n') i += 1;
      row.push(value.trim());
      if (row.some(cell => cell !== '')) rows.push(row);
      row = [];
      value = '';
    } else {
      value += char;
    }
  }
  row.push(value.trim());
  if (row.some(cell => cell !== '')) rows.push(row);

  if (rows.length < 2) return [];
  const headers = rows[0].map(header => header.replace(/^\uFEFF/, '').trim());
  return rows.slice(1).map(cells => Object.fromEntries(headers.map((header, index) => [header, cells[index] || ''])));
}

function isUsableBrand(value) {
  return value && !value.trim().startsWith('--');
}

function mapCsvRow(row) {
  const brand = [row.E1_Brand, row.Unilog_Brand, row.DIB_Brand, row.Part_Manuf]
    .find(isUsableBrand) || 'Unknown manufacturer';
  return {
    brand,
    mpn: row.Mfg_Part_Num || '',
    description: row.Part_Desc || ''
  };
}

async function handleCsvUpload(event) {
  const file = event.target.files[0];
  const status = document.getElementById('csv-status');
  const previewWrap = document.getElementById('csv-preview-wrap');
  const processButton = document.getElementById('btn-process-csv');
  document.getElementById('csv-results').style.display = 'none';

  if (!file) return;
  if (!file.name.toLowerCase().endsWith('.csv')) {
    status.textContent = 'Please choose a CSV file.';
    previewWrap.style.display = 'none';
    processButton.disabled = true;
    return;
  }

  const rows = parseCsv(await file.text());
  const required = ['Mfg_Part_Num', 'Part_Desc'];
  if (!rows.length || required.some(column => !(column in rows[0]))) {
    status.textContent = 'This file does not contain the required Mfg_Part_Num and Part_Desc columns.';
    previewWrap.style.display = 'none';
    processButton.disabled = true;
    return;
  }

  csvProducts = rows.map(mapCsvRow).filter(product => product.mpn && product.description);
  csvBatchStart = 0;
  csvProcessedResults.clear();
  document.getElementById('csv-controls').style.display = 'flex';
  updateCsvBatchView();
  previewWrap.style.display = 'block';
  processButton.disabled = csvProducts.length === 0;
}

function getCsvBatchSize() {
  return Number(document.getElementById('csv-batch-size').value) || 10;
}

function getActiveCsvBatch() {
  return csvProducts.slice(csvBatchStart, csvBatchStart + getCsvBatchSize());
}

function updateCsvBatchView() {
  if (!csvProducts.length) return;
  const batchSize = getCsvBatchSize();
  const lastPossibleStart = Math.max(0, csvProducts.length - 1);
  csvBatchStart = Math.min(Math.max(0, csvBatchStart), lastPossibleStart);
  const products = getActiveCsvBatch();
  document.getElementById('csv-start-row').value = csvBatchStart + 1;
  renderCsvPreview(products, csvBatchStart);
  document.getElementById('csv-status').textContent = `Showing rows ${csvBatchStart + 1}–${csvBatchStart + products.length} of ${csvProducts.length}.`;
  document.getElementById('btn-process-csv').disabled = products.length === 0;
  document.getElementById('btn-process-csv').innerHTML = `<span>⚡ Process Rows ${csvBatchStart + 1}–${csvBatchStart + products.length}</span>`;
  document.getElementById('btn-previous-csv').disabled = csvBatchStart === 0;
  document.getElementById('btn-next-csv').disabled = csvBatchStart + batchSize >= csvProducts.length;
}

function moveCsvBatch(direction) {
  csvBatchStart += direction * getCsvBatchSize();
  updateCsvBatchView();
}

function selectCsvStartRow() {
  const selectedRow = Number(document.getElementById('csv-start-row').value) || 1;
  csvBatchStart = selectedRow - 1;
  updateCsvBatchView();
}

function renderCsvPreview(products, startIndex) {
  const body = document.getElementById('csv-preview-body');
  body.innerHTML = '';
  products.forEach((product, index) => {
    const row = document.createElement('tr');
    [startIndex + index + 1, product.brand, product.mpn, product.description].forEach(value => {
      const cell = document.createElement('td');
      cell.textContent = value;
      row.appendChild(cell);
    });
    body.appendChild(row);
  });
}

async function processCsvBatch() {
  const products = getActiveCsvBatch();
  const button = document.getElementById('btn-process-csv');
  const status = document.getElementById('csv-status');
  const results = document.getElementById('csv-results');
  if (!products.length) return;

  button.disabled = true;
  button.innerHTML = `<span>⏳ Processing ${products.length} products...</span>`;
  status.textContent = 'Processing products one at a time. This may take a short while.';
  results.style.display = 'none';

  const processed = [];
  for (let index = 0; index < products.length; index += 1) {
    const product = products[index];
    status.textContent = `Processing ${index + 1} of ${products.length}: ${product.mpn}`;
    try {
      const response = await fetch(`${API_BASE}/api/v1/enrich`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(product)
      });
      if (!response.ok) throw new Error('Could not process this product');
      const data = await response.json();
      const sourceCount = data.sources.length;
      const result = {
        rowNumber: csvBatchStart + index + 1,
        product,
        status: sourceCount > 0 ? 'Processed' : 'No source found',
        sourceCount,
        sourceItems: data.sources,
        specifications: data.specifications.length,
        confidence: data.confidence.overall_score
      };
      processed.push(result);
      csvProcessedResults.set(result.rowNumber, result);
    } catch (error) {
      const result = { rowNumber: csvBatchStart + index + 1, product, status: 'Could not process', sourceCount: 0, sourceItems: [], specifications: 0, confidence: null };
      processed.push(result);
      csvProcessedResults.set(result.rowNumber, result);
    }
  }

  renderCsvResults([...csvProcessedResults.values()].sort((a, b) => a.rowNumber - b.rowNumber));
  status.textContent = `Finished rows ${csvBatchStart + 1}–${csvBatchStart + products.length}. You can select the next batch now.`;
  button.disabled = false;
  document.getElementById('btn-download-csv').disabled = csvProcessedResults.size === 0;
  updateCsvBatchView();
}

function renderCsvResults(processed) {
  const results = document.getElementById('csv-results');
  results.innerHTML = '<div class="csv-preview-title">Batch test results</div>';
  const table = document.createElement('table');
  table.className = 'specs-table csv-preview-table';
  table.innerHTML = '<thead><tr><th>Row</th><th>MPN</th><th>Status</th><th>Sources found</th><th>Specifications found</th><th>Confidence</th><th>Source links</th></tr></thead>';
  const body = document.createElement('tbody');
  processed.forEach(item => {
    const row = document.createElement('tr');
    [item.rowNumber, item.product.mpn, item.status, item.sourceCount, item.specifications, item.confidence === null ? '—' : `${Math.round(item.confidence * 100)}%`].forEach(value => {
      const cell = document.createElement('td');
      cell.textContent = value;
      row.appendChild(cell);
    });
    const linksCell = document.createElement('td');
    if (item.sourceItems.length === 0) {
      linksCell.textContent = '—';
    } else {
      const details = document.createElement('details');
      const summary = document.createElement('summary');
      summary.textContent = 'View links';
      details.appendChild(summary);
      item.sourceItems.forEach(source => {
        const link = document.createElement('a');
        link.href = source.url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.textContent = source.domain;
        link.className = 'batch-source-link';
        details.appendChild(link);
      });
      linksCell.appendChild(details);
    }
    row.appendChild(linksCell);
    body.appendChild(row);
  });
  table.appendChild(body);
  results.appendChild(table);
  results.style.display = 'block';
}

function downloadProcessedCsv() {
  const rows = [["Row", "MPN", "Brand", "Description", "Status", "Sources found", "Specifications found", "Confidence", "Source URLs"]];
  [...csvProcessedResults.values()].sort((a, b) => a.rowNumber - b.rowNumber).forEach(item => {
    rows.push([
      item.rowNumber, item.product.mpn, item.product.brand, item.product.description, item.status,
      item.sourceCount, item.specifications, item.confidence === null ? "" : item.confidence,
      item.sourceItems.map(source => source.url).join(" | ")
    ]);
  });
  const csvText = rows.map(row => row.map(value => `"${String(value).replaceAll('"', '""')}"`).join(',')).join('\n');
  const link = document.createElement('a');
  link.href = URL.createObjectURL(new Blob([csvText], { type: 'text/csv;charset=utf-8;' }));
  link.download = 'processed_product_results.csv';
  link.click();
  URL.revokeObjectURL(link.href);
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

  renderSources(data.sources);

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

function renderSources(sources) {
  const container = document.getElementById('sources-container');
  container.innerHTML = '';
  if (!sources || sources.length === 0) {
    container.textContent = 'No product sources were found for this search.';
    container.className = 'source-empty';
    return;
  }

  container.className = 'source-list';
  sources.forEach(source => {
    const item = document.createElement('a');
    item.className = 'source-link';
    item.href = source.url;
    item.target = '_blank';
    item.rel = 'noopener noreferrer';
    item.textContent = `${source.source_type}: ${source.name} (${source.domain}) ↗`;
    container.appendChild(item);
  });
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
