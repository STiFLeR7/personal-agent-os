const API_BASE = "http://127.0.0.1:8000";

export async function fetchTelemetry() {
  const res = await fetch(`${API_BASE}/telemetry/summary`);
  return res.json();
}

export async function fetchActiveTasks() {
  const res = await fetch(`${API_BASE}/tasks/active`);
  return res.json();
}

export async function fetchSystemState() {
  const res = await fetch(`${API_BASE}/state/system`);
  return res.json();
}

export async function searchMemory(query: string) {
  const res = await fetch(`${API_BASE}/memory/search?q=${encodeURIComponent(query)}`);
  return res.json();
}
