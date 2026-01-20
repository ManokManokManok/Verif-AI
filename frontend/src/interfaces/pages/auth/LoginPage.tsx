import React from 'react';
import { LoginForm } from '../../components/auth';

/**
 * Login page component
 * Displays the login form for user authentication
 */
export const LoginPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-900 flex">
      {/* Left Panel - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-linear-to-br from-slate-800 to-slate-900 items-center justify-center p-12">
        <div className="text-center space-y-6">
          <div className="space-y-2">
            <h1 className="text-4xl font-bold text-white">Know Whats Real</h1>
            <h2 className="text-3xl font-bold text-white">VerifAI</h2>
          </div>
          
          {/* Security Illustration */}
          <div className="relative w-64 h-64 mx-auto">
            <div className="absolute inset-0 bg-slate-700/20 rounded-2xl flex items-center justify-center">
              <svg className="w-32 h-32 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-48 h-1 bg-linear-to-r from-transparent via-pink-500 to-transparent"></div>
          </div>
        </div>
      </div>

      {/* Right Panel - Login Form */}
      <div className="flex-1 lg:max-w-md xl:max-w-lg flex items-center justify-center p-8 bg-slate-950">
        <div className="w-full max-w-sm space-y-8">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-white mb-2">Log In</h1>
            <p className="text-slate-400 text-sm">
              If you don't have an account register You can Register here !
            </p>
          </div>
          
          <LoginForm />
        </div>
      </div>
    </div>
  );
};
