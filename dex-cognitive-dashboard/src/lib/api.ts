const getApiBase = () => {
  if (typeof window === 'undefined') return 'http://127.0.0.1:8000';
  
  const hostname = window.location.hostname;
  // If we're accessing via localhost, use localhost. 
  // If we're accessing via IP (like on a phone), use that same IP.
  return `${window.location.protocol}//${hostname}:8000`;
};

const API_BASE = getApiBase();

export async function fetchTelemetry() {
  const res = await fetch(`${API_BASE}/telemetry/summary`);
  if (!res.ok) throw new Error('Failed to fetch telemetry');
  return res.json();
}

export async function fetchActiveTasks() {
  const res = await fetch(`${API_BASE}/tasks/active`);
  if (!res.ok) throw new Error('Failed to fetch active tasks');
  return res.json();
}

export async function fetchSystemState() {
  const res = await fetch(`${API_BASE}/state/system`);
  if (!res.ok) throw new Error('Failed to fetch system state');
  return res.json();
}

export async function searchMemory(query: string, semantic: boolean = true) {
  const res = await fetch(`${API_BASE}/memory/search?q=${encodeURIComponent(query)}&semantic=${semantic}`);
  if (!res.ok) throw new Error('Failed to search memory');
  return res.json();
}

export async function runTask(request: string) {
  const res = await fetch(`${API_BASE}/tasks/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ request })
  });
  if (!res.ok) throw new Error('Failed to run task');
  return res.json();
}

export async function fetchReminders() {
  const res = await fetch(`${API_BASE}/reminders`);
  if (!res.ok) throw new Error('Failed to fetch reminders');
  return res.json();
}

export async function fetchNotes() {
  const res = await fetch(`${API_BASE}/notes`);
  if (!res.ok) throw new Error('Failed to fetch notes');
  return res.json();
}

export async function fetchConfig() {
  const res = await fetch(`${API_BASE}/config`);
  if (!res.ok) throw new Error('Failed to fetch config');
  return res.json();
}

export async function fetchModes() {
  const res = await fetch(`${API_BASE}/modes`);
  if (!res.ok) throw new Error('Failed to fetch modes');
  return res.json();
}
