import React from 'react';
import { Shield, ShieldCheck, ShieldX, ShieldAlert, Loader2 } from 'lucide-react';
import type { VerificationStatus } from '../../../domain/types/blockchain';

interface VerificationBadgeProps {
  status: VerificationStatus;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

/**
 * Badge component displaying verification status with appropriate icon and color
 */
export const VerificationBadge: React.FC<VerificationBadgeProps> = ({
  status,
  size = 'md',
  showLabel = true
}) => {
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base'
  };

  const iconSizes = {
    sm: 12,
    md: 16,
    lg: 20
  };

  const statusConfig = {
    VERIFIED: {
      icon: ShieldCheck,
      label: 'Verified',
      bgColor: 'bg-green-100',
      textColor: 'text-green-800',
      borderColor: 'border-green-200'
    },
    NOT_VERIFIED: {
      icon: ShieldX,
      label: 'Not Verified',
      bgColor: 'bg-red-100',
      textColor: 'text-red-800',
      borderColor: 'border-red-200'
    },
    NOT_ANCHORED: {
      icon: Shield,
      label: 'Not Anchored',
      bgColor: 'bg-gray-100',
      textColor: 'text-gray-600',
      borderColor: 'border-gray-200'
    },
    ERROR: {
      icon: ShieldAlert,
      label: 'Error',
      bgColor: 'bg-yellow-100',
      textColor: 'text-yellow-800',
      borderColor: 'border-yellow-200'
    }
  };

  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <span
      className={`
        inline-flex items-center gap-1.5 rounded-full font-medium border
        ${sizeClasses[size]}
        ${config.bgColor}
        ${config.textColor}
        ${config.borderColor}
      `}
    >
      <Icon size={iconSizes[size]} />
      {showLabel && <span>{config.label}</span>}
    </span>
  );
};

interface VerificationLoadingProps {
  size?: 'sm' | 'md' | 'lg';
}

/**
 * Loading state badge for verification in progress
 */
export const VerificationLoading: React.FC<VerificationLoadingProps> = ({ size = 'md' }) => {
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base'
  };

  const iconSizes = {
    sm: 12,
    md: 16,
    lg: 20
  };

  return (
    <span
      className={`
        inline-flex items-center gap-1.5 rounded-full font-medium border
        ${sizeClasses[size]}
        bg-blue-50 text-blue-700 border-blue-200
      `}
    >
      <Loader2 size={iconSizes[size]} className="animate-spin" />
      <span>Verifying...</span>
    </span>
  );
};
