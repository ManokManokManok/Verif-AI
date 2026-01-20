import React, { useEffect, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { Card } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { GetProfileUseCase } from '../../use_cases/user/GetProfileUseCase';
import {
  User,
  Mail,
  Calendar,
  Shield,
  CheckCircle,
  AlertCircle,
  Edit,
  Key,
  Activity
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const ProfilePage: React.FC = () => {
  const { user } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [profileData, setProfileData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        setIsLoading(true);
        const getProfileUseCase = new GetProfileUseCase();
        const profile = await getProfileUseCase.execute();
        setProfileData(profile);
        setError(null);
      } catch (err) {
        setError('Failed to load profile data');
        console.error('Profile fetch error:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProfile();
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading profile...</p>
        </div>
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="max-w-4xl mx-auto">
        <Card className="p-6">
          <div className="text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Error Loading Profile</h3>
            <p className="text-gray-600 mb-4">{error || 'Unable to load user data'}</p>
            <Button onClick={() => window.location.reload()}>Retry</Button>
          </div>
        </Card>
      </div>
    );
  }

  const currentUser = profileData || user;

  return (
    <div className="max-w-4xl mx-auto">
      {/* Page header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Profile</h1>
          <p className="text-gray-600 mt-1">Manage your account information and preferences</p>
        </div>
        <Link to="/dashboard/settings">
          <Button>
            <Edit size={16} className="mr-2" />
            Edit Profile
          </Button>
        </Link>
      </div>

      {/* Profile header card */}
      <Card className="p-6 mb-6">
        <div className="flex items-start space-x-6">
          {/* Avatar */}
          <div className="`shrink-0`">
            <div className="w-24 h-24 rounded-full bg-linear-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-3xl font-bold">
              {currentUser.email.charAt(0).toUpperCase()}
            </div>
          </div>

          {/* User info */}
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              <h2 className="text-2xl font-bold text-gray-900">
                {currentUser.email.split('@')[0]}
              </h2>
              {currentUser.isVerified && (
                <CheckCircle className="h-6 w-6 text-green-500" aria-label="Verified Account" />
              )}
            </div>
            <p className="text-gray-600 mb-3">{currentUser.email}</p>
            <div className="flex flex-wrap gap-2">
              {currentUser.roles?.map((role: string) => (
                <span
                  key={role}
                  className="px-3 py-1 bg-indigo-100 text-indigo-700 text-sm font-medium rounded-full"
                >
                  {role.charAt(0).toUpperCase() + role.slice(1)}
                </span>
              ))}
              {currentUser.isActive && (
                <span className="px-3 py-1 bg-green-100 text-green-700 text-sm font-medium rounded-full">
                  Active
                </span>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* Verification status */}
      {!currentUser.isVerified && (
        <Card className="p-4 mb-6 border-yellow-200 bg-yellow-50">
          <div className="flex items-start">
            <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5 mr-3" />
            <div className="flex-1">
              <h3 className="text-sm font-medium text-yellow-800 mb-1">
                Email Verification Required
              </h3>
              <p className="text-sm text-yellow-700 mb-3">
                Please verify your email address to unlock all features and secure your account.
              </p>
              <Button size="sm" variant="outline" className="border-yellow-300 text-yellow-700 hover:bg-yellow-100">
                Resend Verification Email
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Account details grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Personal Information */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <User size={20} className="mr-2 text-indigo-600" />
            Personal Information
          </h3>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-600 block mb-1">Email Address</label>
              <div className="flex items-center text-gray-900">
                <Mail size={16} className="mr-2 text-gray-400" />
                {currentUser.email}
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600 block mb-1">Account Type</label>
              <div className="flex items-center text-gray-900">
                <Shield size={16} className="mr-2 text-gray-400" />
                {currentUser.roles?.join(', ') || 'User'}
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600 block mb-1">Member Since</label>
              <div className="flex items-center text-gray-900">
                <Calendar size={16} className="mr-2 text-gray-400" />
                {new Date(currentUser.createdAt).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </div>
            </div>
          </div>
        </Card>

        {/* Account Security */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Shield size={20} className="mr-2 text-indigo-600" />
            Account Security
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center">
                <CheckCircle size={16} className={`mr-2 ${currentUser.isVerified ? 'text-green-500' : 'text-gray-400'}`} />
                <span className="text-sm text-gray-700">Email Verified</span>
              </div>
              <span className={`text-sm font-medium ${currentUser.isVerified ? 'text-green-600' : 'text-yellow-600'}`}>
                {currentUser.isVerified ? 'Yes' : 'No'}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center">
                <Activity size={16} className="mr-2 text-gray-400" />
                <span className="text-sm text-gray-700">Account Status</span>
              </div>
              <span className={`text-sm font-medium ${currentUser.isActive ? 'text-green-600' : 'text-red-600'}`}>
                {currentUser.isActive ? 'Active' : 'Inactive'}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center">
                <Key size={16} className="mr-2 text-gray-400" />
                <span className="text-sm text-gray-700">Password</span>
              </div>
              <Link to="/dashboard/settings">
                <Button size="sm" variant="outline">Change</Button>
              </Link>
            </div>
          </div>
        </Card>
      </div>

      {/* Activity Information */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Activity size={20} className="mr-2 text-indigo-600" />
          Recent Activity
        </h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between py-3 border-b border-gray-100">
            <div className="flex items-center">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
              <div>
                <p className="text-sm font-medium text-gray-900">Last Login</p>
                <p className="text-xs text-gray-500">
                  {currentUser.lastLogin
                    ? new Date(currentUser.lastLogin).toLocaleString()
                    : 'Current session'}
                </p>
              </div>
            </div>
          </div>
          <div className="flex items-center justify-between py-3 border-b border-gray-100">
            <div className="flex items-center">
              <div className="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
              <div>
                <p className="text-sm font-medium text-gray-900">Account Created</p>
                <p className="text-xs text-gray-500">
                  {new Date(currentUser.createdAt).toLocaleString()}
                </p>
              </div>
            </div>
          </div>
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center">
              <div className="w-2 h-2 bg-purple-500 rounded-full mr-3"></div>
              <div>
                <p className="text-sm font-medium text-gray-900">Profile Updated</p>
                <p className="text-xs text-gray-500">Never</p>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Actions */}
      <Card className="p-6 mt-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="flex flex-wrap gap-3">
          <Link to="/dashboard/settings">
            <Button variant="outline">
              <Edit size={16} className="mr-2" />
              Edit Profile
            </Button>
          </Link>
          <Link to="/dashboard/settings">
            <Button variant="outline">
              <Key size={16} className="mr-2" />
              Change Password
            </Button>
          </Link>
          <Button variant="outline">
            <Activity size={16} className="mr-2" />
            View Activity Log
          </Button>
        </div>
      </Card>
    </div>
  );
};
