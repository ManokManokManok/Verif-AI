import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useAuth } from '../../../hooks/useAuth';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
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
      await login(data);
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
              {...register('email', { 
                required: 'Email is required',
                pattern: {
                  value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
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
              {...register('password', { 
                required: 'Password is required',
                minLength: {
                  value: 8,
                  message: 'Password must be at least 8 characters'
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

      {/* Social Login */}
      <div className="space-y-4">
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-slate-600"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-slate-950 text-slate-400">or continue with</span>
          </div>
        </div>
        
        <div className="flex justify-center space-x-4">
          <button className="p-2 border border-slate-600 rounded-lg hover:bg-slate-800 transition-colors duration-200">
            <svg className="w-5 h-5 text-slate-300" fill="currentColor" viewBox="0 0 24 24">
              <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
            </svg>
          </button>
          <button className="p-2 border border-slate-600 rounded-lg hover:bg-slate-800 transition-colors duration-200">
            <svg className="w-5 h-5 text-slate-300" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C6.477 2 2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.879V14.89h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.989C18.343 21.129 22 16.99 22 12c0-5.523-4.477-10-10-10z"/>
            </svg>
          </button>
          <button className="p-2 border border-slate-600 rounded-lg hover:bg-slate-800 transition-colors duration-200">
            <svg className="w-5 h-5 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012-2v-1a2 2 0 012-2h1.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 002-2v-1a2 2 0 012-2h1.945M12 3.935V5.5A2.5 2.5 0 0114.5 8h.5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 002-2v-1a2 2 0 012-2h1.945" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};
