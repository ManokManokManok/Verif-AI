import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getCached, setCached, removeCached, clearHistoryCache, isSameData } from '../src/utils/historyCache';

const memoryStorage = () => {
  let store = {};
  return {
    getItem: (k) => (k in store ? store[k] : null),
    setItem: (k, v) => { store[k] = String(v); },
    removeItem: (k) => { delete store[k]; },
    clear: () => { store = {}; },
    get length() { return Object.keys(store).length; },
    key: (i) => Object.keys(store)[i] ?? null,
    // Object.keys(storage) must list stored keys, as in real browsers
    __keys: () => Object.keys(store),
  };
};

const makeEnumerable = (storage) => new Proxy(storage, {
  ownKeys: () => storage.__keys(),
  getOwnPropertyDescriptor: (target, prop) => (
    storage.__keys().includes(prop) ? { enumerable: true, configurable: true, value: target.getItem(prop) } : undefined
  ),
});

const login = (id) => {
  window.localStorage.setItem('access_token', 'token');
  window.localStorage.setItem('user', JSON.stringify({ user_id: id }));
};

describe('historyCache', () => {
  beforeEach(() => {
    vi.stubGlobal('localStorage', memoryStorage());
    vi.stubGlobal('sessionStorage', makeEnumerable(memoryStorage()));
    Object.defineProperty(window, 'localStorage', { value: globalThis.localStorage, configurable: true });
    Object.defineProperty(window, 'sessionStorage', { value: globalThis.sessionStorage, configurable: true });
    clearHistoryCache();
  });

  it('does not cache when logged out', () => {
    setCached('analysis:list', [1]);
    expect(getCached('analysis:list')).toBeUndefined();
  });

  it('returns what was stored for the logged-in user', () => {
    login('u1');
    setCached('analysis:abc', { id: 'abc' });
    expect(getCached('analysis:abc')).toEqual({ id: 'abc' });
  });

  it('never shows one user the data of another', () => {
    login('u1');
    setCached('analysis:list', [{ id: 'mine' }], { persisted: true });
    login('u2');
    expect(getCached('analysis:list', { persisted: true })).toBeUndefined();
  });

  it('restores persisted lists after memory is lost (page refresh)', () => {
    login('u1');
    setCached('analysis:list', [{ id: 'a' }], { persisted: true });
    const key = Object.keys(window.sessionStorage)[0];
    expect(key).toContain('u1');
    // Simulate a refresh: memory gone, sessionStorage kept
    const stored = window.sessionStorage.getItem(key);
    clearHistoryCache();
    window.sessionStorage.setItem(key, stored);
    expect(getCached('analysis:list', { persisted: true })).toEqual([{ id: 'a' }]);
  });

  it('keeps unpersisted items out of sessionStorage', () => {
    login('u1');
    setCached('analysis:big', { data_url: 'x'.repeat(10) });
    expect(Object.keys(window.sessionStorage)).toHaveLength(0);
  });

  it('removes single entries and clears everything', () => {
    login('u1');
    setCached('a', 1, { persisted: true });
    setCached('b', 2);
    removeCached('a');
    expect(getCached('a', { persisted: true })).toBeUndefined();
    clearHistoryCache();
    expect(getCached('b')).toBeUndefined();
    expect(Object.keys(window.sessionStorage)).toHaveLength(0);
  });

  it('detects unchanged data', () => {
    expect(isSameData([{ a: 1 }], [{ a: 1 }])).toBe(true);
    expect(isSameData([{ a: 1 }], [{ a: 2 }])).toBe(false);
  });
});
