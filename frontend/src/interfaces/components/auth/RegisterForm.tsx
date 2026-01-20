import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useAuth } from '../../../hooks/useAuth';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import type { RegisterData } from '../../../domain/types';

interface RegisterFormData extends RegisterData {
  confirmPassword: string;
  username: string;
}

/**
 * Registration form component
 * Handles new user account creation
 */
export const RegisterForm: React.FC = () => {
  const { register: registerUser } = useAuth();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting }
  } = useForm<RegisterFormData>();

  const password = watch('password');

  const onSubmit = async (data: RegisterFormData) => {
    setServerError(null);
    setSuccessMessage(null);
    
    try {
      const result = await registerUser({
        email: data.email,
        password: data.password,
        confirmPassword: data.confirmPassword,
        username: data.username
      });
      
      setSuccessMessage(result.message || 'Registration successful! Please check your email for verification.');
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (error: any) {
      if (error?.response?.status === 409) {
        setServerError('This email address is already registered. Please use a different email or try logging in.');
      } else if (error?.response?.status === 400) {
        setServerError('Please check your information and try again. Make sure all fields are filled correctly.');
      } else if (error?.response?.status === 422) {
        setServerError('Invalid information provided. Please check your email format and password requirements.');
      } else if (error instanceof Error) {
        setServerError(error.message);
      } else {
        setServerError('Registration failed. Please try again later or contact support if the problem persists.');
      }
    }
  };

  return (
    <div className="w-full space-y-6">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {serverError && (
          <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-3 rounded-lg relative" role="alert">
            <span className="block sm:inline">{serverError}</span>
          </div>
        )}
        
        {successMessage && (
          <div className="bg-green-900/50 border border-green-500 text-green-200 px-4 py-3 rounded-lg relative" role="alert">
            <span className="block sm:inline">{successMessage}</span>
          </div>
        )}
        
        {/* Email Field */}
        <div className="space-y-2">
          <Label htmlFor="email" className="text-slate-300 text-sm font-medium">Email</Label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
              </svg>
            </div>
            <Input
              id="email"
              type="email"
              placeholder="name@example.com"
              {...register('email', { 
                required: 'Email is required',
                pattern: {
                  value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                  message: 'Invalid email format'
                }
              })}
              className={`pl-10 bg-slate-800 border-slate-600 text-white placeholder-slate-400 focus:border-pink-500 focus:ring-pink-500 ${errors.email ? 'border-red-500' : ''}`}
              disabled={isSubmitting || !!successMessage}
            />
          </div>
          {errors.email && (
            <p className="text-sm text-red-400 mt-1">{errors.email.message}</p>
          )}
        </div>
        
        {/* Username Field */}
        <div className="space-y-2">
          <Label htmlFor="username" className="text-slate-300 text-sm font-medium">Username</Label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <Input
              id="username"
              type="text"
              placeholder="Choose a username"
              {...register('username', { 
                required: 'Username is required',
                minLength: {
                  value: 3,
                  message: 'Username must be at least 3 characters'
                }
              })}
              className={`pl-10 bg-slate-800 border-slate-600 text-white placeholder-slate-400 focus:border-pink-500 focus:ring-pink-500 ${errors.username ? 'border-red-500' : ''}`}
              disabled={isSubmitting || !!successMessage}
            />
          </div>
          {errors.username && (
            <p className="text-sm text-red-400 mt-1">{errors.username.message}</p>
          )}
        </div>
        
        {/* Password Field */}
        <div className="space-y-2">
          <Label htmlFor="password" className="text-slate-300 text-sm font-medium">Password</Label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <Input
              id="password"
              type="password"
              placeholder="Create a strong password"
              {...register('password', { 
                required: 'Password is required',
                minLength: {
                  value: 8,
                  message: 'Password must be at least 8 characters'
                },
                pattern: {
                  value: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>])/,
                  message: 'Password must contain uppercase, lowercase, number, and special character'
                }
              })}
              className={`pl-10 bg-slate-800 border-slate-600 text-white placeholder-slate-400 focus:border-pink-500 focus:ring-pink-500 ${errors.password ? 'border-red-500' : ''}`}
              disabled={isSubmitting || !!successMessage}
            />
          </div>
          {errors.password && (
            <p className="text-sm text-red-400 mt-1">{errors.password.message}</p>
          )}
          <p className="text-xs text-slate-500">
            Must be at least 8 characters with uppercase, lowercase, number, and special character
          </p>
        </div>
        
        {/* Confirm Password Field */}
        <div className="space-y-2">
          <Label htmlFor="confirmPassword" className="text-slate-300 text-sm font-medium">Confirm Password</Label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <Input
              id="confirmPassword"
              type="password"
              placeholder="Confirm your password"
              {...register('confirmPassword', { 
                required: 'Please confirm your password',
                validate: (value) => value === password || 'Passwords do not match'
              })}
              className={`pl-10 bg-slate-800 border-slate-600 text-white placeholder-slate-400 focus:border-pink-500 focus:ring-pink-500 ${errors.confirmPassword ? 'border-red-500' : ''}`}
              disabled={isSubmitting || !!successMessage}
            />
          </div>
          {errors.confirmPassword && (
            <p className="text-sm text-red-400 mt-1">{errors.confirmPassword.message}</p>
          )}
        </div>
        
        {/* Register Button */}
        <Button 
          type="submit" 
          className="w-full bg-pink-600 hover:bg-pink-700 text-white font-semibold py-3 rounded-lg transition-colors duration-200" 
          disabled={isSubmitting || !!successMessage}
        >
          {isSubmitting ? 'Creating account...' : 'Register'}
        </Button>
      </form>
    </div>
  );
};
