// Multi-Agent Research Assistant Frontend Logic
const API_BASE = window.location.origin;

// Tab Switching
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    const tabId = btn.getAttribute('data-tab');
    document.getElementById(tabId).classList.add('active');

    if (tabId === 'tab-benchmark') {
      loadEvaluationResults();
    }
  });
});

// Set Preset Query
function setQuery(text) {
  const textarea = document.getElementById('question-input');
  textarea.value = text;
  textarea.focus();
}

// Health Check on Startup
async function checkSystemHealth() {
  const badge = document.getElementById('system-status-badge');
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) {
      const data = await res.json();
      const toolCount = data.mcp_server?.tool_count || 0;
      const mode = data.llm_engine?.mode || 'deterministic';
      badge.textContent = `MCP: ${toolCount} Tools • Engine: ${mode.toUpperCase()}`;
      badge.className = 'badge online';
    } else {
      badge.textContent = 'Backend: Degraded';
      badge.className = 'badge';
    }
  } catch (err) {
    badge.textContent = 'Backend: Offline';
    badge.className = 'badge';
  }
}

// Pipeline Stepper Progress
function updateStepper(activeStep) {
  const steps = ['planner', 'researcher', 'verifier', 'writer', 'evaluator'];
  const activeIdx = steps.indexOf(activeStep);

  steps.forEach((step, idx) => {
    const el = document.getElementById(`step-${step}`);
    if (!el) return;
    el.classList.remove('active', 'completed');
    if (idx < activeIdx) {
      el.classList.add('completed');
    } else if (idx === activeIdx) {
      el.classList.add('active');
    }
  });
}

function resetStepper() {
  ['planner', 'researcher', 'verifier', 'writer', 'evaluator'].forEach(s => {
    const el = document.getElementById(`step-${s}`);
    if (el) el.classList.remove('active', 'completed');
  });
}

// Form Submission
document.getElementById('research-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const input = document.getElementById('question-input');
  const question = input.value.trim();
  if (!question) return;

  const useBaseline = document.getElementById('baseline-toggle').checked;
  const submitBtn = document.getElementById('submit-btn');
  const spinner = submitBtn.querySelector('.spinner');
  const btnText = submitBtn.querySelector('.btn-text');

  submitBtn.disabled = true;
  spinner.style.display = 'inline-block';
  btnText.textContent = useBaseline ? 'Running Baseline...' : 'Executing Multi-Agent...';

  // Stepper animation
  resetStepper();
  updateStepper('planner');
  setTimeout(() => updateStepper('researcher'), 300);
  setTimeout(() => updateStepper('verifier'), 700);
  setTimeout(() => updateStepper('writer'), 1100);

  try {
    const res = await fetch(`${API_BASE}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: question,
        max_subtasks: 4,
        use_baseline: useBaseline
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Query execution failed');
    }

    const data = await res.json();
    updateStepper('evaluator');
    setTimeout(() => {
      ['planner', 'researcher', 'verifier', 'writer', 'evaluator'].forEach(s => {
        const el = document.getElementById(`step-${s}`);
        if (el) el.classList.add('completed');
      });
    }, 200);

    renderResults(data);
  } catch (err) {
    alert(`Error: ${err.message}`);
    resetStepper();
  } finally {
    submitBtn.disabled = false;
    spinner.style.display = 'none';
    btnText.textContent = 'Execute Research';
  }
});

// Render Results
function renderResults(data) {
  document.getElementById('metrics-bar').style.display = 'grid';
  document.getElementById('results-container').style.display = 'grid';

  // Metrics
  const m = data.metrics;
  document.getElementById('m-groundedness').textContent = `${(m.groundedness * 100).toFixed(1)}%`;
  document.getElementById('m-hallucination').textContent = `${(m.hallucination_rate * 100).toFixed(1)}%`;
  document.getElementById('m-citation').textContent = `${(m.citation_correctness * 100).toFixed(1)}%`;
  document.getElementById('m-latency').textContent = `${m.latency_ms.toFixed(0)} ms`;
  document.getElementById('m-tools').textContent = m.tool_calls;
  document.getElementById('m-cost').textContent = `$${m.cost_usd.toFixed(4)}`;

  // Run ID tag
  document.getElementById('run-id-tag').textContent = `Run ID: ${data.run_id}`;

  // Report Markdown (simple clean formatting)
  const reportEl = document.getElementById('report-content');
  reportEl.innerHTML = formatMarkdown(data.answer);

  // Claims List
  const claimsEl = document.getElementById('claims-list');
  claimsEl.innerHTML = '';
  if (!data.claims || data.claims.length === 0) {
    claimsEl.innerHTML = '<p class="hint">No claims extracted.</p>';
  } else {
    data.claims.forEach(c => {
      const item = document.createElement('div');
      item.className = 'claim-item';
      item.innerHTML = `
        <div class="claim-header">
          <strong>${c.claim_id}</strong>
          <span class="claim-status ${c.status}">${c.status} (${(c.confidence * 100).toFixed(0)}%)</span>
        </div>
        <div class="claim-body">${c.statement}</div>
        <div class="hint" style="margin-top:0.3rem;">Cited Evidence: ${c.evidence_ids.join(', ') || 'None'}</div>
        ${c.contradiction_notes ? `<div style="color:var(--danger);font-size:0.75rem;margin-top:0.25rem;">⚠️ ${c.contradiction_notes}</div>` : ''}
      `;
      claimsEl.appendChild(item);
    });
  }

  // Evidence List
  const evEl = document.getElementById('evidence-list');
  evEl.innerHTML = '';
  if (!data.evidence || data.evidence.length === 0) {
    evEl.innerHTML = '<p class="hint">No local evidence retrievable for this query.</p>';
  } else {
    data.evidence.forEach(e => {
      const item = document.createElement('div');
      item.className = 'evidence-item';
      item.innerHTML = `
        <div class="evidence-header">
          <span>[${e.evidence_id}] ${e.document_id}</span>
          <span>Rel: ${(e.relevance * 100).toFixed(0)}%</span>
        </div>
        <div style="font-weight:500;color:#fff;margin-bottom:0.25rem;">${e.source}</div>
        <div style="color:var(--text-secondary);font-size:0.8rem;">${e.text}</div>
      `;
      evEl.appendChild(item);
    });
  }
}

// Simple Markdown to HTML formatter
function formatMarkdown(text) {
  if (!text) return '<p>No content generated.</p>';
  let html = text
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\[(E\d+)\]/g, '<span style="color:var(--primary);font-weight:bold;">[$1]</span>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^- (.*$)/gim, '<li>$1</li>');

  // Wrap lists
  html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
  return `<p>${html}</p>`;
}

// Trigger Evaluation Suite
async function triggerEvaluation() {
  const btn = document.getElementById('run-bench-btn');
  const spinner = document.getElementById('bench-spinner');
  btn.disabled = true;
  spinner.style.display = 'inline-block';

  try {
    const res = await fetch(`${API_BASE}/evaluation/run`, { method: 'POST' });
    if (!res.ok) throw new Error('Evaluation failed to run');
    await loadEvaluationResults();
  } catch (err) {
    alert(`Evaluation Error: ${err.message}`);
  } finally {
    btn.disabled = false;
    spinner.style.display = 'none';
  }
}

// Load Evaluation Results
async function loadEvaluationResults() {
  try {
    const res = await fetch(`${API_BASE}/evaluation/results`);
    if (!res.ok) return;
    const data = await res.json();
    if (data.status === 'not_run') return;

    const s = data.summary;
    const summaryEl = document.getElementById('bench-summary');
    summaryEl.innerHTML = `
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-bottom:1.5rem;">
        <div class="card" style="border-color:var(--primary);">
          <h3>✨ Multi-Agent System + MCP (Variant D)</h3>
          <p>Accuracy: <strong>${(s.multi_agent.accuracy * 100).toFixed(1)}%</strong></p>
          <p>Groundedness: <strong>${(s.multi_agent.groundedness * 100).toFixed(1)}%</strong></p>
          <p>Hallucination Rate: <strong>${(s.multi_agent.hallucination_rate * 100).toFixed(1)}%</strong></p>
          <p>Mean Latency: <strong>${s.multi_agent.mean_latency_ms} ms</strong> (P95: ${s.multi_agent.p95_latency_ms} ms)</p>
          <p>Avg Tool Invocations: <strong>${s.multi_agent.tool_calls_per_query} / query</strong></p>
          <p>API Cost: <strong>$0.00 (Zero-Cost Localhost)</strong></p>
        </div>
        <div class="card" style="border-color:var(--border-color);">
          <h3>⚠️ Single-Agent Baseline (Variant A)</h3>
          <p>Accuracy: <strong>${(s.baseline.accuracy * 100).toFixed(1)}%</strong></p>
          <p>Groundedness: <strong>${(s.baseline.groundedness * 100).toFixed(1)}%</strong></p>
          <p>Hallucination Rate: <strong>${(s.baseline.hallucination_rate * 100).toFixed(1)}%</strong></p>
          <p>Mean Latency: <strong>${s.baseline.mean_latency_ms} ms</strong></p>
          <p>Avg Tool Invocations: <strong>0 / query</strong></p>
          <p>API Cost: <strong>$0.00</strong></p>
        </div>
      </div>
    `;

    // Table rows
    const tbody = document.getElementById('test-cases-tbody');
    tbody.innerHTML = '';
    data.multi_agent_results.forEach(r => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${r.test_id}</strong></td>
        <td>${r.category}</td>
        <td>${r.question}</td>
        <td><span class="status-tag ${r.pass ? 'pass' : 'fail'}">${r.pass ? 'PASS' : 'FAIL'}</span></td>
        <td>${(r.groundedness * 100).toFixed(0)}%</td>
        <td>${(r.hallucination_detected ? '⚠️ Yes' : '✅ None')}</td>
        <td>${r.latency_ms.toFixed(0)} ms</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error(err);
  }
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
  checkSystemHealth();
});
