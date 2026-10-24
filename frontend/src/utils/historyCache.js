// Lightweight stale-while-revalidate cache for history lists and opened items.
// - Entries are scoped to the logged-in user, so one account never sees another's data.
// - Lists are mirrored to sessionStorage so a page refresh paints instantly (cleared when the tab closes).
// - Items (full details/messages) stay in memory only: they can be large (image previews).
const PREFIX = 'verfai_hc:';
const memory = new Map();

function currentScope() {
  try {
    const raw = window.localStorage.getItem('user');
    if (!raw || !window.localStorage.getItem('access_token')) return null;
    const user = JSON.parse(raw);
    const id = user?.user_id || user?.id || user?.email;
    return id ? String(id) : null;
  } catch {
    return null;
  }
}

function scopedKey(key) {
  const scope = currentScope();
  return scope ? `${PREFIX}${scope}:${key}` : null;
}

export function getCached(key, { persisted = false } = {}) {
  const full = scopedKey(key);
  if (!full) return undefined;
  if (memory.has(full)) return memory.get(full);
  if (persisted) {
    try {
      const raw = window.sessionStorage.getItem(full);
      if (raw) {
        const value = JSON.parse(raw);
        memory.set(full, value);
        return value;
      }
    } catch {
      // Corrupt or unavailable storage: behave as a cache miss
    }
  }
  return undefined;
}

export function setCached(key, value, { persisted = false } = {}) {
  const full = scopedKey(key);
  if (!full) return;
  memory.set(full, value);
  if (persisted) {
    try {
      window.sessionStorage.setItem(full, JSON.stringify(value));
    } catch {
      // Quota exceeded: the in-memory copy is still valid
    }
  }
}

export function removeCached(key) {
  const full = scopedKey(key);
  if (!full) return;
  memory.delete(full);
  try {
    window.sessionStorage.removeItem(full);
  } catch {
    // ignore
  }
}

export function clearHistoryCache() {
  memory.clear();
  try {
    Object.keys(window.sessionStorage)
      .filter((k) => k.startsWith(PREFIX))
      .forEach((k) => window.sessionStorage.removeItem(k));
  } catch {
    // ignore
  }
}

// Cheap change detection so we only re-render when the server data actually differs.
export function isSameData(a, b) {
  try {
    return JSON.stringify(a) === JSON.stringify(b);
  } catch {
    return false;
  }
}
