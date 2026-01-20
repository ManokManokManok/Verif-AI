import React, { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { Card } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { UpdateProfileUseCase } from '../../use_cases/user/UpdateProfileUseCase';
import {
  Settings as SettingsIcon,
  User,
  Shield,
  Bell,
  Key,
  Trash2,
  Save,
  AlertCircle,
  CheckCircle,
  Eye,
  EyeOff
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'profile' | 'security' | 'notifications' | 'danger'>('profile');
  
  // Profile state
  const [email, setEmail] = useState(user?.email || '');
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateMessage, setUpdateMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Password state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  // Notification settings
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [securityAlerts, setSecurityAlerts] = useState(true);
  const [marketingEmails, setMarketingEmails] = useState(false);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsUpdating(true);
    setUpdateMessage(null);

    try {
      const updateProfileUseCase = new UpdateProfileUseCase();
      await updateProfileUseCase.execute({ email });
      setUpdateMessage({ type: 'success', text: 'Profile updated successfully!' });
    } catch (error: any) {
      setUpdateMessage({ 
        type: 'error', 
        text: error.message || 'Failed to update profile. Please try again.' 
      });
    } finally {
      setIsUpdating(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError(null);

    // Validation
    if (!currentPassword || !newPassword || !confirmPassword) {
      setPasswordError('All password fields are required');
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      setPasswordError('New password must be at least 8 characters long');
      return;
    }

    // TODO: Implement password change via API
    setPasswordError('Password change functionality coming soon');
  };

  const handleSaveNotifications = () => {
    setUpdateMessage({ type: 'success', text: 'Notification preferences saved!' });
  };

  const tabs = [
    { id: 'profile' as const, label: 'Profile', icon: User },
    { id: 'security' as const, label: 'Security', icon: Shield },
    { id: 'notifications' as const, label: 'Notifications', icon: Bell },
    { id: 'danger' as const, label: 'Danger Zone', icon: AlertCircle },
  ];

  return (
    <div className="max-w-5xl mx-auto">
      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center">
          <SettingsIcon size={28} className="mr-2" />
          Settings
        </h1>
        <p className="text-gray-600 mt-1">Manage your account settings and preferences</p>
      </div>

      {/* Success/Error messages */}
      {updateMessage && (
        <div className={`mb-6 p-4 rounded-lg ${updateMessage.type === 'success' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
          <div className="flex items-center">
            {updateMessage.type === 'success' ? (
              <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
            ) : (
              <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
            )}
            <p className={`text-sm ${updateMessage.type === 'success' ? 'text-green-800' : 'text-red-800'}`}>
              {updateMessage.text}
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Tabs sidebar */}
        <div className="lg:col-span-1">
          <Card className="p-2">
            <nav className="space-y-1">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`
                      w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors
                      ${activeTab === tab.id
                        ? 'bg-indigo-50 text-indigo-700 font-medium'
                        : 'text-gray-700 hover:bg-gray-50'
                      }
                    `}
                  >
                    <Icon size={18} />
                    <span className="text-sm">{tab.label}</span>
                  </button>
                );
              })}
            </nav>
          </Card>
        </div>

        {/* Content area */}
        <div className="lg:col-span-3">
          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <Card className="p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Profile Information</h2>
              <form onSubmit={handleUpdateProfile} className="space-y-6">
                <div>
                  <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="your@email.com"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Your email address is used for login and notifications
                  </p>
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                  <div>
                    <p className="text-sm font-medium text-gray-900">Account Status</p>
                    <p className="text-xs text-gray-500">
                      Your account is {user?.isActive ? 'active' : 'inactive'} and {user?.isVerified ? 'verified' : 'unverified'}
                    </p>
                  </div>
                  <div className="flex space-x-2">
                    {user?.isActive && (
                      <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">Active</span>
                    )}
                    {user?.isVerified && (
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">Verified</span>
                    )}
                  </div>
                </div>

                <div className="flex justify-end space-x-3">
                  <Button type="button" variant="outline" onClick={() => setEmail(user?.email || '')}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={isUpdating}>
                    {isUpdating ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save size={16} className="mr-2" />
                        Save Changes
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </Card>
          )}

          {/* Security Tab */}
          {activeTab === 'security' && (
            <div className="space-y-6">
              <Card className="p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">Change Password</h2>
                <form onSubmit={handleChangePassword} className="space-y-4">
                  {passwordError && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-sm text-red-800">{passwordError}</p>
                    </div>
                  )}

                  <div>
                    <Label htmlFor="currentPassword">Current Password</Label>
                    <div className="relative">
                      <Input
                        id="currentPassword"
                        type={showCurrentPassword ? 'text' : 'password'}
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        placeholder="Enter current password"
                      />
                      <button
                        type="button"
                        onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                      >
                        {showCurrentPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="newPassword">New Password</Label>
                    <div className="relative">
                      <Input
                        id="newPassword"
                        type={showNewPassword ? 'text' : 'password'}
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        placeholder="Enter new password"
                      />
                      <button
                        type="button"
                        onClick={() => setShowNewPassword(!showNewPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                      >
                        {showNewPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      Must be at least 8 characters long
                    </p>
                  </div>

                  <div>
                    <Label htmlFor="confirmPassword">Confirm New Password</Label>
                    <div className="relative">
                      <Input
                        id="confirmPassword"
                        type={showConfirmPassword ? 'text' : 'password'}
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        placeholder="Confirm new password"
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                      >
                        {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>

                  <div className="flex justify-end pt-4">
                    <Button type="submit">
                      <Key size={16} className="mr-2" />
                      Update Password
                    </Button>
                  </div>
                </form>
              </Card>

              <Card className="p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Two-Factor Authentication</h2>
                <p className="text-sm text-gray-600 mb-4">
                  Add an extra layer of security to your account by enabling two-factor authentication.
                </p>
                <Button variant="outline" disabled>
                  <Shield size={16} className="mr-2" />
                  Enable 2FA (Coming Soon)
                </Button>
              </Card>
            </div>
          )}

          {/* Notifications Tab */}
          {activeTab === 'notifications' && (
            <Card className="p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Notification Preferences</h2>
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">Email Notifications</p>
                    <p className="text-sm text-gray-500">Receive email updates about your account</p>
                  </div>
                  <button
                    onClick={() => setEmailNotifications(!emailNotifications)}
                    className={`
                      relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                      ${emailNotifications ? 'bg-indigo-600' : 'bg-gray-200'}
                    `}
                  >
                    <span
                      className={`
                        inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                        ${emailNotifications ? 'translate-x-6' : 'translate-x-1'}
                      `}
                    />
                  </button>
                </div>

                <div className="flex items-center justify-between border-t border-gray-200 pt-6">
                  <div>
                    <p className="font-medium text-gray-900">Security Alerts</p>
                    <p className="text-sm text-gray-500">Get notified about unusual account activity</p>
                  </div>
                  <button
                    onClick={() => setSecurityAlerts(!securityAlerts)}
                    className={`
                      relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                      ${securityAlerts ? 'bg-indigo-600' : 'bg-gray-200'}
                    `}
                  >
                    <span
                      className={`
                        inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                        ${securityAlerts ? 'translate-x-6' : 'translate-x-1'}
                      `}
                    />
                  </button>
                </div>

                <div className="flex items-center justify-between border-t border-gray-200 pt-6">
                  <div>
                    <p className="font-medium text-gray-900">Marketing Emails</p>
                    <p className="text-sm text-gray-500">Receive news and product updates</p>
                  </div>
                  <button
                    onClick={() => setMarketingEmails(!marketingEmails)}
                    className={`
                      relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                      ${marketingEmails ? 'bg-indigo-600' : 'bg-gray-200'}
                    `}
                  >
                    <span
                      className={`
                        inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                        ${marketingEmails ? 'translate-x-6' : 'translate-x-1'}
                      `}
                    />
                  </button>
                </div>

                <div className="flex justify-end pt-4 border-t border-gray-200">
                  <Button onClick={handleSaveNotifications}>
                    <Save size={16} className="mr-2" />
                    Save Preferences
                  </Button>
                </div>
              </div>
            </Card>
          )}

          {/* Danger Zone Tab */}
          {activeTab === 'danger' && (
            <Card className="p-6 border-red-200">
              <h2 className="text-xl font-semibold text-red-600 mb-6 flex items-center">
                <AlertCircle size={24} className="mr-2" />
                Danger Zone
              </h2>
              <div className="space-y-6">
                <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                  <h3 className="font-medium text-gray-900 mb-2">Deactivate Account</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Temporarily disable your account. You can reactivate it anytime by logging in.
                  </p>
                  <Button variant="outline" className="border-red-300 text-red-600 hover:bg-red-50" disabled>
                    Deactivate Account
                  </Button>
                </div>

                <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                  <h3 className="font-medium text-gray-900 mb-2">Delete Account</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Permanently delete your account and all associated data. This action cannot be undone.
                  </p>
                  <Button className="bg-red-600 hover:bg-red-700" disabled>
                    <Trash2 size={16} className="mr-2" />
                    Delete Account
                  </Button>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
