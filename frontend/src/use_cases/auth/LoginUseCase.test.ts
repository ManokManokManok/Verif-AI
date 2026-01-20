import { describe, it, expect, vi, beforeEach } from 'vitest';
import { LoginUseCase } from './LoginUseCase';

// Mock dependencies
vi.mock('../../infrastructure/api', () => ({
  authApi: {
    login: vi.fn(),
  },
}));

vi.mock('../../domain/services', () => ({
  validationService: {
    validateEmail: vi.fn(),
    validateRequired: vi.fn(),
  },
}));

vi.mock('../../infrastructure/storage', () => ({
  TokenStorage: {
    storeTokens: vi.fn(),
  },
  UserStorage: {
    storeUser: vi.fn(),
  },
}));

describe('LoginUseCase', () => {
  let loginUseCase: LoginUseCase;

  beforeEach(() => {
    loginUseCase = new LoginUseCase();
    vi.clearAllMocks();
  });

  it('should successfully login with valid credentials', async () => {
    const { authApi } = await import('../../infrastructure/api');
    const { validationService } = await import('../../domain/services');

    vi.mocked(validationService.validateEmail).mockReturnValue(true);
    vi.mocked(validationService.validateRequired).mockReturnValue({ isValid: true, errors: [] });
    vi.mocked(authApi.login).mockResolvedValue({
      success: true,
      tokens: {
        access_token: 'mock_access_token',
        refresh_token: 'mock_refresh_token',
        token_type: 'Bearer',
      },
      user: {
        id: '123',
        email: 'test@example.com',
        roles: ['user'],
        is_active: true,
        is_verified: true,
        created_at: '2024-01-15T00:00:00Z',
      },
    });

    const result = await loginUseCase.execute({
      email: 'test@example.com',
      password: 'password123',
    });

    expect(result.success).toBe(true);
    expect(result.user.email).toBe('test@example.com');
  });

  it('should throw error for invalid email format', async () => {
    const { validationService } = await import('../../domain/services');
    vi.mocked(validationService.validateEmail).mockReturnValue(false);

    await expect(
      loginUseCase.execute({
        email: 'invalid',
        password: 'password123',
      })
    ).rejects.toThrow('Invalid email format');
  });

  it('should throw error for empty password', async () => {
    const { validationService } = await import('../../domain/services');
    vi.mocked(validationService.validateEmail).mockReturnValue(true);
    vi.mocked(validationService.validateRequired).mockReturnValue({
      isValid: false,
      errors: ['Password is required'],
    });

    await expect(
      loginUseCase.execute({
        email: 'test@example.com',
        password: '',
      })
    ).rejects.toThrow('Password is required');
  });

  it('should handle API errors correctly', async () => {
    const { authApi } = await import('../../infrastructure/api');
    const { validationService } = await import('../../domain/services');

    vi.mocked(validationService.validateEmail).mockReturnValue(true);
    vi.mocked(validationService.validateRequired).mockReturnValue({ isValid: true, errors: [] });
    vi.mocked(authApi.login).mockRejectedValue(new Error('Invalid credentials'));

    await expect(
      loginUseCase.execute({
        email: 'test@example.com',
        password: 'wrongpassword',
      })
    ).rejects.toThrow('Invalid credentials');
  });
});
