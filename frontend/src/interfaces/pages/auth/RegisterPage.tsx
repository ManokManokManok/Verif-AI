import React from 'react';
import { Link } from 'react-router-dom';
import { RegisterForm } from '../../components/auth';

/**
 * Registration page component
 * Displays the registration form for new user signup
 */
export const RegisterPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-900 flex">
      {/* Left Panel - Branding */}
      <div className="hidden lg:flex lg:w-1/2 `bg-linear-to-br` from-slate-800 to-slate-900 items-center justify-center p-12">
        <div className="text-center space-y-6">
          <div className="space-y-2">
            <h1 className="text-4xl font-bold text-white">Keeping you Safe</h1>
            <h2 className="text-3xl font-bold text-white">VerifAI</h2>
          </div>
          
          {/* Security Illustration */}
          <div className="relative w-64 h-64 mx-auto">
            <div className="absolute inset-0 bg-slate-700/20 rounded-2xl flex items-center justify-center">
              <svg className="w-32 h-32 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-48 h-1 bg-linear-to-r from-transparent via-pink-500 to-transparent"></div>
          </div>
        </div>
      </div>

      {/* Right Panel - Register Form */}
      <div className="flex-1 lg:max-w-md xl:max-w-lg flex items-center justify-center p-8 bg-slate-950">
        <div className="w-full max-w-sm space-y-8">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-white mb-2">Sign up</h1>
            <p className="text-slate-400 text-sm">
              If you already have an account{' '}
              <Link to="/login" className="text-pink-500 hover:text-pink-400 font-medium">
                Login here!
              </Link>
            </p>
          </div>
          
          <RegisterForm />
        </div>
      </div>
    </div>
  );
};
