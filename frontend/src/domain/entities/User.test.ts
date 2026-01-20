import { describe, it, expect } from 'vitest';
import { User } from './User';

describe('User Entity', () => {
  const mockUser = new User(
    '123',
    'test@example.com',
    ['user'],
    true,
    true,
    new Date('2024-01-01'),
    'testuser',
    new Date('2024-01-10')
  );

  describe('constructor', () => {
    it('should create a user with all properties', () => {
      expect(mockUser.id).toBe('123');
      expect(mockUser.email).toBe('test@example.com');
      expect(mockUser.roles).toEqual(['user']);
      expect(mockUser.isActive).toBe(true);
      expect(mockUser.isVerified).toBe(true);
      expect(mockUser.createdAt).toBeInstanceOf(Date);
      expect(mockUser.lastLogin).toBeInstanceOf(Date);
    });

    it('should allow optional lastLogin', () => {
      const userWithoutLogin = new User(
        '456',
        'another@example.com',
        ['user'],
        true,
        false,
        new Date()
      );
      expect(userWithoutLogin.lastLogin).toBeUndefined();
    });
  });

  describe('canAccess', () => {
    it('should return true for admin role with any permission', () => {
      const adminUser = new User(
        '789',
        'admin@example.com',
        ['admin'],
        true,
        true,
        new Date()
      );
      expect(adminUser.canAccess('delete_user')).toBe(true);
      expect(adminUser.canAccess('any_permission')).toBe(true);
    });

    it('should return true for user role with valid user permissions', () => {
      expect(mockUser.canAccess('view_profile')).toBe(true);
      expect(mockUser.canAccess('update_profile')).toBe(true);
    });

    it('should return false for user role with admin permissions', () => {
      expect(mockUser.canAccess('delete_user')).toBe(false);
      expect(mockUser.canAccess('create_user')).toBe(false);
    });

    it('should return true for moderator role with moderator permissions', () => {
      const moderator = new User(
        '999',
        'mod@example.com',
        ['moderator'],
        true,
        true,
        new Date()
      );
      expect(moderator.canAccess('view_analytics')).toBe(true);
      expect(moderator.canAccess('moderate_content')).toBe(true);
    });

    it('should handle multiple roles correctly', () => {
      const multiRoleUser = new User(
        '111',
        'multi@example.com',
        ['user', 'moderator'],
        true,
        true,
        new Date()
      );
      expect(multiRoleUser.canAccess('view_profile')).toBe(true);
      expect(multiRoleUser.canAccess('moderate_content')).toBe(true);
    });
  });
});
