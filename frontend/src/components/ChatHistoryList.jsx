import { useMemo, useState } from 'react';

const parseDate = (value) => {
  if (!value) return null;
  let str = String(value);
  if (!str.endsWith('Z') && !/[+-]\d{2}:\d{2}$/.test(str)) str += 'Z';
  const date = new Date(str);
  return Number.isNaN(date.getTime()) ? null : date;
};

const startOfDay = (d) => new Date(d.getFullYear(), d.getMonth(), d.getDate());

const getGroupLabel = (date) => {
  if (!date) return 'Older';
  const diffDays = Math.round((startOfDay(new Date()) - startOfDay(date)) / 86400000);
  if (diffDays <= 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays <= 7) return 'Previous 7 days';
  if (diffDays <= 30) return 'Previous 30 days';
  return 'Older';
};

const GROUP_ORDER = ['Today', 'Yesterday', 'Previous 7 days', 'Previous 30 days', 'Older'];

const formatTime = (date) => {
  if (!date) return '';
  const label = getGroupLabel(date);
  if (label === 'Today') return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  if (label === 'Yesterday' || label === 'Previous 7 days') {
    return date.toLocaleDateString([], { weekday: 'short' });
  }
  return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
};

/**
 * items: [{ id, title, subtitle, date, badge, active, deleting, onSelect, onDelete }]
 */
export default function ChatHistoryList({ items, loading = false, emptyText = 'No conversations yet' }) {
  const [query, setQuery] = useState('');
  const [confirmingId, setConfirmingId] = useState(null);

  const groups = useMemo(() => {
    const q = query.trim().toLowerCase();
    const filtered = q
      ? items.filter((i) => `${i.title} ${i.subtitle || ''}`.toLowerCase().includes(q))
      : items;
    const map = new Map();
    filtered.forEach((item) => {
      const date = parseDate(item.date);
      const label = getGroupLabel(date);
      if (!map.has(label)) map.set(label, []);
      map.get(label).push({ ...item, parsedDate: date });
    });
    return GROUP_ORDER.filter((l) => map.has(l)).map((label) => ({ label, entries: map.get(label) }));
  }, [items, query]);

  return (
    <>
      <div className="chat-history__search">
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search chats..."
          aria-label="Search chats"
        />
      </div>
      <div className="detect__chat-list">
        {loading ? (
          <div className="chatbot__history-empty">Loading...</div>
        ) : groups.length === 0 ? (
          <div className="chatbot__history-empty">{query ? 'No matching chats' : emptyText}</div>
        ) : (
          groups.map((group) => (
            <div className="chat-history__group" key={group.label}>
              <div className="chat-history__group-label">{group.label}</div>
              {group.entries.map((item) => {
                const confirming = confirmingId === item.id;
                return (
                  <div
                    key={item.id}
                    className={`detect__chat-item${item.active ? ' detect__chat-item--active' : ''}`}
                    onClick={item.onSelect}
                  >
                    <div className="detect__chat-item-header">
                      <div className="detect__chat-item-title" title={item.title}>
                        {item.title}
                      </div>
                      {item.onDelete && !confirming && (
                        <button
                          type="button"
                          className="detect__chat-delete"
                          title="Delete"
                          aria-label="Delete"
                          disabled={item.deleting}
                          onClick={(e) => {
                            e.stopPropagation();
                            setConfirmingId(item.id);
                          }}
                        >
                          🗑
                        </button>
                      )}
                    </div>
                    {confirming ? (
                      <div className="chat-history__confirm" onClick={(e) => e.stopPropagation()}>
                        <span>Delete?</span>
                        <button
                          type="button"
                          className="chat-history__confirm-yes"
                          onClick={() => {
                            setConfirmingId(null);
                            item.onDelete();
                          }}
                        >
                          Yes
                        </button>
                        <button
                          type="button"
                          className="chat-history__confirm-no"
                          onClick={() => setConfirmingId(null)}
                        >
                          No
                        </button>
                      </div>
                    ) : (
                      <div className="detect__chat-item-meta">
                        {item.badge && <span className="chat-history__badge">{item.badge}</span>}
                        {item.subtitle && (
                          <span className="detect__chat-item-preview">{item.subtitle}</span>
                        )}
                        <span className="detect__chat-item-time">{formatTime(item.parsedDate)}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ))
        )}
      </div>
    </>
  );
}
