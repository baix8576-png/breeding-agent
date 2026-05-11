"""Minimal web console endpoints for run board and diagnostics."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from runtime.bootstrap import create_application_context

router = APIRouter(tags=["console"])


@router.get("/v2/console", response_class=HTMLResponse)
def console_home() -> HTMLResponse:
    """Serve a minimal runtime console for board/status/report/diagnostic workflows."""

    html = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>GeneAgent V2 Console</title>
  <style>
    :root { --bg: #f4f7ec; --card: #ffffff; --ink: #1f2a1f; --accent: #1f6f43; --muted: #4c5f4d; }
    body { margin: 0; font-family: "Segoe UI", "PingFang SC", sans-serif; background: linear-gradient(145deg, #eef5dd 0%, #f8f2e7 100%); color: var(--ink); }
    main { max-width: 1080px; margin: 0 auto; padding: 24px; }
    h1 { margin: 0 0 12px; font-size: 1.8rem; }
    .grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }
    .card { background: var(--card); border: 1px solid #dbe6cd; border-radius: 14px; padding: 14px; box-shadow: 0 10px 20px rgba(20, 60, 30, 0.06); }
    .meta { color: var(--muted); font-size: 0.9rem; }
    .item { margin: 8px 0; font-family: Consolas, monospace; font-size: 0.86rem; word-break: break-all; }
    button { border: none; border-radius: 10px; padding: 8px 12px; background: var(--accent); color: #fff; cursor: pointer; }
    input { width: 100%; box-sizing: border-box; border: 1px solid #d0ddc4; border-radius: 10px; padding: 8px; margin-top: 8px; }
    pre { background: #f6f8f4; border: 1px solid #dde8cf; border-radius: 10px; padding: 10px; max-height: 280px; overflow: auto; }
    .board-item { border-top: 1px dashed #d7e3cb; padding-top: 8px; margin-top: 8px; }
  </style>
</head>
<body>
<main>
  <h1>GeneAgent V2 Console</h1>
  <p class="meta">Task board, status flow, report traceability, and diagnostic entry.</p>
  <div class="grid">
    <section class="card">
      <h2>Task Board</h2>
      <button onclick="loadBoard()">Refresh Board</button>
      <div id="board"></div>
    </section>
    <section class="card">
      <h2>Run Snapshot</h2>
      <input id="runId" placeholder="run_id" />
      <input id="taskId" placeholder="task_id (optional)" />
      <button onclick="loadRun()">Load Snapshot</button>
      <pre id="runSnapshot">{}</pre>
    </section>
    <section class="card">
      <h2>Diagnostic Entry</h2>
      <input id="diagText" placeholder="request_text" value="Summarize local SOP diagnostics for failed run" />
      <input id="diagWorkdir" placeholder="working_directory (optional)" />
      <button onclick="runDiagnostic()">Run Diagnostic</button>
      <pre id="diagResult">{}</pre>
    </section>
    <section class="card">
      <h2>Observability</h2>
      <button onclick="loadMetrics()">Refresh Metrics</button>
      <pre id="metricsResult">{}</pre>
    </section>
  </div>
</main>
<script>
async function loadBoard() {
  const res = await fetch('/v2/console/board?limit=20');
  const payload = await res.json();
  const runs = payload.board?.runs || [];
  const root = document.getElementById('board');
  if (!runs.length) {
    root.innerHTML = '<p class="meta">No run closure records found yet.</p>';
    return;
  }
  root.innerHTML = runs.map(item => `
    <div class="board-item">
      <div><strong>${item.task_id || 'unknown_task'}</strong> / ${item.run_id || 'unknown_run'}</div>
      <div class="meta">stage=${item.runtime_stage || 'unknown'} | path=${item.runtime_path || 'unknown'}</div>
      <div class="item">${item.summary || ''}</div>
    </div>
  `).join('');
}
async function loadRun() {
  const runId = document.getElementById('runId').value.trim();
  const taskId = document.getElementById('taskId').value.trim();
  if (!runId) return;
  const q = taskId ? `?task_id=${encodeURIComponent(taskId)}` : '';
  const res = await fetch(`/v2/console/runs/${encodeURIComponent(runId)}${q}`);
  const payload = await res.json();
  document.getElementById('runSnapshot').textContent = JSON.stringify(payload, null, 2);
}
async function runDiagnostic() {
  const text = document.getElementById('diagText').value.trim();
  const workdir = document.getElementById('diagWorkdir').value.trim();
  const body = {
    request_text: text || 'Inspect local diagnostics',
    identity: { working_directory: workdir || null }
  };
  const res = await fetch('/v2/tasks/diagnostic', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body)
  });
  const payload = await res.json();
  document.getElementById('diagResult').textContent = JSON.stringify(payload, null, 2);
}
async function loadMetrics() {
  const res = await fetch('/v2/observability/metrics?limit=200');
  const payload = await res.json();
  document.getElementById('metricsResult').textContent = JSON.stringify(payload, null, 2);
}
loadBoard();
loadMetrics();
</script>
</body>
</html>
"""
    return HTMLResponse(content=html)


@router.get("/v2/console/board")
def board(
    limit: int = Query(default=20, ge=1, le=100),
    working_directory: str | None = None,
) -> dict[str, object]:
    """Return recent run board entries from persisted audit events."""

    context = create_application_context()
    payload = context.facade.list_task_board(
        working_directory=working_directory,
        limit=limit,
    )
    return {"board": payload}


@router.get("/v2/console/runs/{run_id}")
def run_snapshot(
    run_id: str,
    task_id: str | None = None,
    working_directory: str | None = None,
) -> dict[str, object]:
    """Return one run snapshot for status flow and report traceability browsing."""

    context = create_application_context()
    try:
        snapshot = context.facade.get_run_snapshot(
            run_id=run_id,
            task_id=task_id,
            working_directory=working_directory,
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return {"run": snapshot}
