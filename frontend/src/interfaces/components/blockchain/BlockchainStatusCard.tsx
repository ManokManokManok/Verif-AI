import React, { useState, useEffect } from 'react';
import { Activity, CheckCircle, XCircle, RefreshCw } from 'lucide-react';
import { Button } from '../../../components/ui/button';
import { blockchainApi } from '../../../infrastructure/api';
import type { BlockchainStatus } from '../../../domain/types/blockchain';

interface BlockchainStatusCardProps {
  autoRefresh?: boolean;
  refreshInterval?: number; // in milliseconds
}

/**
 * Card component displaying blockchain connection status
 * Shows network info, contract address, and connection health
 */
export const BlockchainStatusCard: React.FC<BlockchainStatusCardProps> = ({
  autoRefresh = false,
  refreshInterval = 30000
}) => {
  const [status, setStatus] = useState<BlockchainStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await blockchainApi.getStatus();
      setStatus(result);
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || 'Failed to fetch status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();

    if (autoRefresh) {
      const interval = setInterval(fetchStatus, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const truncateAddress = (address: string) => {
    if (!address || address.length < 20) return address;
    return `${address.slice(0, 10)}...${address.slice(-8)}`;
  };

  return (
    <div className="bg-gray-50 rounded-xl shadow-sm p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Activity size={20} className="text-indigo-600" />
          Blockchain Status
        </h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={fetchStatus}
          disabled={loading}
          className="gap-1"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh
        </Button>
      </div>

      {error ? (
        <div className="flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-lg">
          <XCircle size={18} />
          <span>{error}</span>
        </div>
      ) : status ? (
        <div className="space-y-3">
          {/* Connection Status */}
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="text-sm text-gray-600">Connection</span>
            <span className={`flex items-center gap-1.5 text-sm font-medium ${
              status.connected ? 'text-green-600' : 'text-red-600'
            }`}>
              {status.connected ? (
                <>
                  <CheckCircle size={14} />
                  Connected
                </>
              ) : (
                <>
                  <XCircle size={14} />
                  Disconnected
                </>
              )}
            </span>
          </div>

          {/* Network */}
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="text-sm text-gray-600">Network</span>
            <span className="text-sm font-medium text-gray-900">
              {status.network || 'Unknown'}
            </span>
          </div>

          {/* Contract Address */}
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="text-sm text-gray-600">Contract</span>
            <span className="text-sm font-mono text-gray-900" title={status.contractAddress}>
              {truncateAddress(status.contractAddress)}
            </span>
          </div>

          {/* Block Number */}
          {status.blockNumber && (
            <div className="flex items-center justify-between py-2">
              <span className="text-sm text-gray-600">Latest Block</span>
              <span className="text-sm font-medium text-gray-900">
                #{status.blockNumber.toLocaleString()}
              </span>
            </div>
          )}
        </div>
      ) : (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      )}
    </div>
  );
};
