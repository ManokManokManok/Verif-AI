import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { downloadUserDataExport } from '../src/api/analytics';

describe('downloadUserDataExport', () => {
  beforeEach(() => {
    localStorage.getItem.mockReturnValue(null);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('requests the authenticated HTML export as a downloadable blob', async () => {
    const exportFile = new Blob(['<html>Personal data</html>'], { type: 'text/html' });
    const response = {
      headers: {
        get: vi.fn((name) => {
          if (name === 'content-type') return 'text/html; charset=utf-8';
          if (name === 'X-RateLimit-Reset') return '1791741600';
          return null;
        }),
      },
      ok: true,
      blob: vi.fn().mockResolvedValue(exportFile),
    };
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(response);

    await expect(downloadUserDataExport('Asia/Manila')).resolves.toEqual({
      blob: exportFile,
      headers: response.headers,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/analytics/my-export/?timezone=Asia%2FManila'),
      expect.objectContaining({ method: 'GET' }),
    );
  });
});
