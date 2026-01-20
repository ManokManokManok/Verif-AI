import React from 'react';
import { Card } from '../ui/card';

/**
 * Skeleton loader for card components
 */
export const CardSkeleton: React.FC<{ className?: string }> = ({ className = '' }) => {
  return (
    <Card className={`p-6 ${className}`}>
      <div className="animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
        <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
        <div className="h-3 bg-gray-200 rounded w-5/6"></div>
      </div>
    </Card>
  );
};

/**
 * Skeleton loader for stat cards in dashboard
 */
export const StatCardSkeleton: React.FC = () => {
  return (
    <Card className="p-6">
      <div className="animate-pulse">
        <div className="flex items-center justify-between mb-4">
          <div className="w-12 h-12 bg-gray-200 rounded-lg"></div>
        </div>
        <div className="h-3 bg-gray-200 rounded w-24 mb-2"></div>
        <div className="h-8 bg-gray-200 rounded w-16 mb-1"></div>
        <div className="h-2 bg-gray-200 rounded w-20"></div>
      </div>
    </Card>
  );
};

/**
 * Skeleton loader for profile page
 */
export const ProfileSkeleton: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-32 mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-64"></div>
      </div>

      <Card className="p-6 mb-6">
        <div className="flex items-start space-x-6 animate-pulse">
          <div className="w-24 h-24 bg-gray-200 rounded-full `shrink-0`"></div>
          <div className="flex-1">
            <div className="h-6 bg-gray-200 rounded w-48 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-64 mb-3"></div>
            <div className="flex gap-2">
              <div className="h-6 bg-gray-200 rounded-full w-16"></div>
              <div className="h-6 bg-gray-200 rounded-full w-20"></div>
            </div>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <CardSkeleton />
        <CardSkeleton />
      </div>
    </div>
  );
};

/**
 * Skeleton loader for dashboard home page
 */
export const DashboardSkeleton: React.FC = () => {
  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-64 mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-96"></div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCardSkeleton />
        <StatCardSkeleton />
        <StatCardSkeleton />
        <StatCardSkeleton />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <CardSkeleton />
        <CardSkeleton className="lg:col-span-2" />
      </div>
    </div>
  );
};

/**
 * Skeleton loader for table rows
 */
export const TableRowSkeleton: React.FC<{ columns?: number }> = ({ columns = 4 }) => {
  return (
    <tr className="animate-pulse">
      {Array.from({ length: columns }).map((_, index) => (
        <td key={index} className="px-6 py-4">
          <div className="h-4 bg-gray-200 rounded"></div>
        </td>
      ))}
    </tr>
  );
};

/**
 * Skeleton loader for list items
 */
export const ListItemSkeleton: React.FC = () => {
  return (
    <div className="flex items-center space-x-4 p-4 animate-pulse">
      <div className="w-10 h-10 bg-gray-200 rounded-full shrink-0"></div>
      <div className="flex-1">
        <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
        <div className="h-3 bg-gray-200 rounded w-1/2"></div>
      </div>
    </div>
  );
};

/**
 * Skeleton loader for form inputs
 */
export const FormSkeleton: React.FC<{ fields?: number }> = ({ fields = 3 }) => {
  return (
    <div className="space-y-4">
      {Array.from({ length: fields }).map((_, index) => (
        <div key={index} className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
          <div className="h-10 bg-gray-200 rounded w-full"></div>
        </div>
      ))}
    </div>
  );
};

/**
 * Generic skeleton loader with customizable dimensions
 */
export const Skeleton: React.FC<{
  width?: string;
  height?: string;
  className?: string;
  rounded?: 'none' | 'sm' | 'md' | 'lg' | 'full';
}> = ({ width = 'w-full', height = 'h-4', className = '', rounded = 'md' }) => {
  const roundedClass = {
    none: '',
    sm: 'rounded-sm',
    md: 'rounded',
    lg: 'rounded-lg',
    full: 'rounded-full',
  }[rounded];

  return (
    <div className={`animate-pulse bg-gray-200 ${width} ${height} ${roundedClass} ${className}`}></div>
  );
};

/**
 * Page loading skeleton with centered spinner
 */
export const PageLoadingSkeleton: React.FC<{ message?: string }> = ({ 
  message = 'Loading...' 
}) => {
  return (
    <div className="flex items-center justify-center min-h-100">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
        <p className="text-gray-600">{message}</p>
      </div>
    </div>
  );
};
