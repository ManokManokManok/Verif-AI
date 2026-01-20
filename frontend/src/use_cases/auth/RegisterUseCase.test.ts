import { describe, it, expect, vi, beforeEach } from 'vitest';
import { RegisterUseCase } from './RegisterUseCase';

// Mock dependencies
vi.mock('../../infrastructure/api', () => ({
  authApi: {
    register: vi.fn(),
  },
}));

vi.mock('../../domain/services', () => ({
  validationService: {
    validateEmail: vi.fn(),
    validatePassword: vi.fn(),
    validatePasswordMatch: vi.fn(),
  },
}));

describe('RegisterUseCase', () => {
  let registerUseCase: RegisterUseCase;

  beforeEach(() => {
    registerUseCase = new RegisterUseCase();
    vi.clearAllMocks();
  });

  it('should successfully register with valid data', async () => {
    const { authApi } = await import('../../infrastructure/api');
    const { validationService } = await import('../../domain/services');

    vi.mocked(validationService.validateEmail).mockReturnValue(true);
    vi.mocked(validationService.validatePassword).mockReturnValue({ isValid: true, errors: [] });
    vi.mocked(validationService.validatePasswordMatch).mockReturnValue({ isValid: true, errors: [] });
    vi.mocked(authApi.register).mockResolvedValue({
      success: true,
      user: {
        id: '456',
        email: 'newuser@example.com',
        roles: ['user'],
        is_active: true,
        is_verified: false,
        created_at: '2024-01-15T00:00:00Z',
      },
      message: 'Registration successful',
    });

    const result = await registerUseCase.execute({
      email: 'newuser@example.com',
      password: 'SecureP@ss123',
      confirmPassword: 'SecureP@ss123',
      username: 'newuser',
    });

    expect(result.success).toBe(true);
    expect(result.email).toBe('newuser@example.com');
  });

  it('should throw error for invalid email', async () => {
    const { validationService } = await import('../../domain/services');
    vi.mocked(validationService.validateEmail).mockReturnValue(false);

    await expect(
      registerUseCase.execute({
        email: 'invalid',
        password: 'SecureP@ss123',
        confirmPassword: 'SecureP@ss123',
        username: 'testuser',
      })
    ).rejects.toThrow('Invalid email format');
  });

  it('should throw error for weak password', async () => {
    const { validationService } = await import('../../domain/services');
    vi.mocked(validationService.validateEmail).mockReturnValue(true);
    vi.mocked(validationService.validatePassword).mockReturnValue({
      isValid: false,
      errors: ['Password must be at least 8 characters long'],
    });

    await expect(
      registerUseCase.execute({
        email: 'test@example.com',
        password: 'weak',
        confirmPassword: 'weak',
        username: 'testuser',
      })
    ).rejects.toThrow();
  });

  it('should throw error when passwords do not match', async () => {
    const { validationService } = await import('../../domain/services');
    vi.mocked(validationService.validateEmail).mockReturnValue(true);
    vi.mocked(validationService.validatePassword).mockReturnValue({ isValid: true, errors: [] });
    vi.mocked(validationService.validatePasswordMatch).mockReturnValue({
      isValid: false,
      errors: ['Passwords do not match'],
    });

    await expect(
      registerUseCase.execute({
        email: 'test@example.com',
        password: 'SecureP@ss123',
        confirmPassword: 'DifferentP@ss123',
        username: 'testuser',
      })
    ).rejects.toThrow('Passwords do not match');
  });

  it('should handle API errors correctly', async () => {
    const { authApi } = await import('../../infrastructure/api');
    const { validationService } = await import('../../domain/services');

    vi.mocked(validationService.validateEmail).mockReturnValue(true);
    vi.mocked(validationService.validatePassword).mockReturnValue({ isValid: true, errors: [] });
    vi.mocked(validationService.validatePasswordMatch).mockReturnValue({ isValid: true, errors: [] });
    vi.mocked(authApi.register).mockRejectedValue(new Error('Email already exists'));

    await expect(
      registerUseCase.execute({
        email: 'existing@example.com',
        password: 'SecureP@ss123',
        confirmPassword: 'SecureP@ss123',
        username: 'existinguser',
      })
    ).rejects.toThrow('Email already exists');
  });
});
