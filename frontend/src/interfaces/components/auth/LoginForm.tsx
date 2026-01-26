import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useAuth } from '../../../hooks/useAuth';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { validationService } from '../../../domain/services';
import type { LoginCredentials } from '../../../domain/types';

/**
 * Login form component
 * Handles user authentication with email and password
 */
export const LoginForm: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);
  
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm<LoginCredentials>();

  const onSubmit = async (data: LoginCredentials) => {
    setServerError(null);
    
    try {
      // Sanitize email before sending
      const sanitizedData = {
        email: validationService.sanitizeEmail(data.email),
        password: data.password // Don't sanitize passwords
      };
      
      await login(sanitizedData);
      navigate('/dashboard');
    } catch (error: any) {
      // Check if error has a response from the backend
      if (error?.response?.data?.error) {
        // Backend returned structured error
        const backendError = error.response.data.error;
        setServerError(backendError.message || 'An error occurred during login');
      } else if (error?.response?.status === 401) {
        setServerError('Invalid email or password. Please check your credentials and try again.');
      } else if (error?.response?.status === 400) {
        setServerError('Please enter a valid email and password.');
      } else if (error?.response?.status === 429) {
        setServerError('Too many login attempts. Please wait a few minutes before trying again.');
      } else if (error?.response?.status === 403) {
        setServerError('Account access denied. Please verify your email or contact support.');
      } else if (error instanceof Error) {
        setServerError(error.message);
      } else {
        setServerError('Login failed. Please try again later or contact support if the problem persists.');
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
              maxLength={254}
              {...register('email', { 
                required: 'Email is required',
                maxLength: {
                  value: 254,
                  message: 'Email must not exceed 254 characters'
                },
                pattern: {
                  value: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
                  message: 'Invalid email format'
                }
              })}
              className={`pl-10 bg-slate-800 border-slate-600 text-white placeholder-slate-400 focus:border-pink-500 focus:ring-pink-500 ${errors.email ? 'border-red-500' : ''}`}
            />
          </div>
          {errors.email && (
            <p className="text-sm text-red-400 mt-1">{errors.email.message}</p>
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
              placeholder="Enter your password"
              maxLength={128}
              {...register('password', { 
                required: 'Password is required',
                minLength: {
                  value: 1,
                  message: 'Password is required'
                },
                maxLength: {
                  value: 128,
                  message: 'Password must not exceed 128 characters'
                }
              })}
              className={`pl-10 bg-slate-800 border-slate-600 text-white placeholder-slate-400 focus:border-pink-500 focus:ring-pink-500 ${errors.password ? 'border-red-500' : ''}`}
            />
          </div>
          {errors.password && (
            <p className="text-sm text-red-400 mt-1">{errors.password.message}</p>
          )}
        </div>

        {/* Remember Me & Forgot Password */}
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <input
              id="remember"
              type="checkbox"
              className="h-4 w-4 rounded border-slate-600 bg-slate-800 text-pink-500 focus:ring-pink-500 focus:ring-offset-slate-900"
            />
            <Label htmlFor="remember" className="ml-2 block text-sm text-slate-300">
              Remember me
            </Label>
          </div>
          <div className="text-sm">
            <Link to="/forgot-password" className="text-pink-500 hover:text-pink-400 font-medium">
              Forgot Password?
            </Link>
          </div>
        </div>
        
        {/* Login Button */}
        <Button 
          type="submit" 
          className="w-full bg-pink-600 hover:bg-pink-700 text-white font-semibold py-3 rounded-lg transition-colors duration-200" 
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Signing in...' : 'Login'}
        </Button>
      </form>

      {/* Register Link */}
      <div className="text-center mt-6">
        <p className="text-slate-400">
          Don't have an account?{' '}
          <Link to="/register" className="text-pink-500 hover:text-pink-400 font-medium">
            Register Here!
          </Link>
        </p>
      </div>
    </div>
  );
};
