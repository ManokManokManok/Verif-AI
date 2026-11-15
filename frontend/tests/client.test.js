import { afterEach, describe, expect, it, vi } from 'vitest';
import { loginRequest, sendMfaCodeRequest } from '../src/api/client';

const credentials = { email: 'user@example.com', password: 'password' };
const unavailableMessage = 'Having trouble connecting to Verif-AI. The servers may be turned off or access may be restricted. To request access, contact kenchitomeldan@gmail.com.';

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('login connection errors', () => {
  it('explains that the servers may be offline and provides a contact', async () => {
    const cause = new TypeError('Failed to fetch');
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(cause));

    await expect(loginRequest(credentials)).rejects.toMatchObject({
      name: 'NetworkError',
      message: unavailableMessage,
      cause,
    });
  });

  it.each([
    'Forbidden',
    'Forbidden. For troubleshooting Function URL authorization issues, see AWS documentation.',
  ])('explains an AWS function URL access denial during MFA login: %s', async (awsMessage) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      headers: { get: () => 'application/json' },
      json: async () => ({ Message: awsMessage }),
    }));

    await expect(sendMfaCodeRequest(credentials)).rejects.toMatchObject({
      status: 403,
      message: unavailableMessage,
    });
  });

  it('preserves application permission errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      headers: { get: () => 'application/json' },
      json: async () => ({ error: { message: 'Permission denied' } }),
    }));

    await expect(sendMfaCodeRequest(credentials)).rejects.toMatchObject({
      status: 403,
      message: 'Permission denied',
    });
  });

  it('preserves the server message for incorrect credentials', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      headers: { get: () => 'application/json' },
      json: async () => ({ error: { message: 'Invalid email or password' } }),
    }));

    await expect(loginRequest(credentials)).rejects.toMatchObject({
      status: 401,
      message: 'Invalid email or password',
    });
  });
});
