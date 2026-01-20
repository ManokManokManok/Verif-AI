import { useState } from 'react';
import { authApi, userApi } from '../infrastructure/api';
import { validationService } from '../domain/services';

interface TestResult {
  name: string;
  status: 'pending' | 'success' | 'error';
  message: string;
  details?: string;
}

export const ApiIntegrationTest = () => {
  const [results, setResults] = useState<TestResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [testEmail] = useState(`test${Date.now()}@example.com`);
  const [testPassword] = useState('TestPass123!');

  const addResult = (result: TestResult) => {
    setResults(prev => [...prev, result]);
  };

  const runTests = async () => {
    setResults([]);
    setIsRunning(true);

    try {
      // Test 1: Health Check
      addResult({ name: 'Health Check', status: 'pending', message: 'Testing backend health endpoint...' });
      try {
        const response = await fetch('http://127.0.0.1:8000/api/health');
        const data = await response.json();
        addResult({
          name: 'Health Check',
          status: 'success',
          message: 'Backend is healthy',
          details: `MongoDB: ${data.mongodb}, Django: ${data.django}`
        });
      } catch (error) {
        addResult({
          name: 'Health Check',
          status: 'error',
          message: 'Backend health check failed',
          details: error instanceof Error ? error.message : 'Unknown error'
        });
        setIsRunning(false);
        return;
      }

      // Test 2: User Registration
      addResult({ name: 'User Registration', status: 'pending', message: 'Registering new user...' });
      try {
        const registerResult = await authApi.register({
          email: testEmail,
          password: testPassword,
          confirmPassword: testPassword,
          username: 'testuser'
        });
        addResult({
          name: 'User Registration',
          status: 'success',
          message: 'User registered successfully',
          details: `Email: ${registerResult.user.email}, ID: ${registerResult.user.id}`
        });
      } catch (error: any) {
        addResult({
          name: 'User Registration',
          status: 'error',
          message: 'Registration failed',
          details: error.response?.data?.error?.message || error.message
        });
      }

      // Test 3: User Login
      addResult({ name: 'User Login', status: 'pending', message: 'Logging in...' });
      try {
        const loginResult = await authApi.login({
          email: testEmail,
          password: testPassword
        });
        addResult({
          name: 'User Login',
          status: 'success',
          message: 'Login successful',
          details: `Access token received, expires at: ${new Date(Date.now() + 15 * 60 * 1000).toLocaleTimeString()}`
        });

        // Test 4: Get User Profile
        addResult({ name: 'Get Profile', status: 'pending', message: 'Fetching user profile...' });
        try {
          const profileUser = await userApi.getProfile();
          addResult({
            name: 'Get Profile',
            status: 'success',
            message: 'Profile retrieved successfully',
            details: `Email: ${profileUser.email}, Roles: ${profileUser.roles.join(', ')}`
          });
        } catch (error: any) {
          addResult({
            name: 'Get Profile',
            status: 'error',
            message: 'Failed to get profile',
            details: error.response?.data?.error?.message || error.message
          });
        }

        // Test 5: Token Refresh
        addResult({ name: 'Token Refresh', status: 'pending', message: 'Testing token refresh...' });
        try {
          await authApi.refreshToken(loginResult.tokens.refresh_token);
          addResult({
            name: 'Token Refresh',
            status: 'success',
            message: 'Token refreshed successfully',
            details: 'New access token received'
          });
        } catch (error: any) {
          addResult({
            name: 'Token Refresh',
            status: 'error',
            message: 'Token refresh failed',
            details: error.response?.data?.error?.message || error.message
          });
        }

        // Test 6: Check Permission
        addResult({ name: 'Check Permission', status: 'pending', message: 'Checking user permissions...' });
        try {
          const permissionResult = await userApi.checkPermission({
            permission: 'view_profile'
          });
          addResult({
            name: 'Check Permission',
            status: 'success',
            message: `Permission check: ${permissionResult.hasPermission ? 'Granted' : 'Denied'}`,
            details: `Permission: ${permissionResult.permission}`
          });
        } catch (error: any) {
          addResult({
            name: 'Check Permission',
            status: 'error',
            message: 'Permission check failed',
            details: error.response?.data?.error?.message || error.message
          });
        }

        // Test 7: Logout
        addResult({ name: 'Logout', status: 'pending', message: 'Logging out...' });
        try {
          await authApi.logout();
          addResult({
            name: 'Logout',
            status: 'success',
            message: 'Logout successful',
            details: 'Tokens blacklisted'
          });
        } catch (error: any) {
          addResult({
            name: 'Logout',
            status: 'error',
            message: 'Logout failed',
            details: error.response?.data?.error?.message || error.message
          });
        }

      } catch (error: any) {
        addResult({
          name: 'User Login',
          status: 'error',
          message: 'Login failed',
          details: error.response?.data?.error?.message || error.message
        });
      }

      // Test 8: Validation Service Integration
      addResult({ name: 'Validation Service', status: 'pending', message: 'Testing validation...' });
      const emailValidation = validationService.validateEmail(testEmail);
      const passwordValidation = validationService.validatePassword(testPassword);
      addResult({
        name: 'Validation Service',
        status: emailValidation && passwordValidation.isValid ? 'success' : 'error',
        message: 'Validation tests completed',
        details: `Email valid: ${emailValidation}, Password valid: ${passwordValidation.isValid}`
      });

    } catch (error) {
      addResult({
        name: 'Test Suite',
        status: 'error',
        message: 'Test suite failed',
        details: error instanceof Error ? error.message : 'Unknown error'
      });
    } finally {
      setIsRunning(false);
    }
  };

  const getStatusIcon = (status: TestResult['status']) => {
    switch (status) {
      case 'success': return '✅';
      case 'error': return '❌';
      case 'pending': return '⏳';
    }
  };

  const getStatusColor = (status: TestResult['status']) => {
    switch (status) {
      case 'success': return 'text-green-600';
      case 'error': return 'text-red-600';
      case 'pending': return 'text-yellow-600';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Backend API Integration Tests
            </h1>
            <p className="text-gray-600">
              Testing all authentication and user management endpoints
            </p>
          </div>

          <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h2 className="font-semibold text-blue-900 mb-2">Test Configuration</h2>
            <div className="text-sm text-blue-800">
              <p><strong>Backend URL:</strong> http://127.0.0.1:8000/api</p>
              <p><strong>Test Email:</strong> {testEmail}</p>
              <p><strong>Test Password:</strong> {testPassword}</p>
            </div>
          </div>

          <button
            onClick={runTests}
            disabled={isRunning}
            className={`w-full py-3 px-6 rounded-lg font-semibold transition-colors mb-6 ${
              isRunning
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-700 text-white'
            }`}
          >
            {isRunning ? 'Running Tests...' : 'Run Integration Tests'}
          </button>

          {results.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Test Results:</h2>
              {results.map((result, index) => (
                <div
                  key={index}
                  className={`p-4 rounded-lg border ${
                    result.status === 'success'
                      ? 'bg-green-50 border-green-200'
                      : result.status === 'error'
                      ? 'bg-red-50 border-red-200'
                      : 'bg-yellow-50 border-yellow-200'
                  }`}
                >
                  <div className="flex items-start">
                    <span className="text-2xl mr-3">{getStatusIcon(result.status)}</span>
                    <div className="flex-1">
                      <h3 className={`font-semibold ${getStatusColor(result.status)}`}>
                        {result.name}
                      </h3>
                      <p className="text-gray-700 mt-1">{result.message}</p>
                      {result.details && (
                        <p className="text-sm text-gray-600 mt-2 font-mono bg-white p-2 rounded">
                          {result.details}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {results.length === 0 && !isRunning && (
            <div className="text-center text-gray-500 py-12">
              Click the button above to run integration tests
            </div>
          )}
        </div>

        <div className="mt-6 bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Test Coverage</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
            <div className="flex items-center">
              <span className="text-gray-400 mr-2">📡</span>
              <span>Backend Health Check</span>
            </div>
            <div className="flex items-center">
              <span className="text-gray-400 mr-2">👤</span>
              <span>User Registration</span>
            </div>
            <div className="flex items-center">
              <span className="text-gray-400 mr-2">🔐</span>
              <span>User Login (JWT)</span>
            </div>
            <div className="flex items-center">
              <span className="text-gray-400 mr-2">👨‍💼</span>
              <span>Get User Profile</span>
            </div>
            <div className="flex items-center">
              <span className="text-gray-400 mr-2">🔄</span>
              <span>Token Refresh</span>
            </div>
            <div className="flex items-center">
              <span className="text-gray-400 mr-2">🔒</span>
              <span>Permission Check</span>
            </div>
            <div className="flex items-center">
              <span className="text-gray-400 mr-2">🚪</span>
              <span>Logout (Token Blacklist)</span>
            </div>
            <div className="flex items-center">
              <span className="text-gray-400 mr-2">✅</span>
              <span>Validation Service</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
