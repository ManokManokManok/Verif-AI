import React from 'react';
import { ExternalLink, Clock, Hash, FileText } from 'lucide-react';
import { VerificationBadge } from './VerificationBadge';
import { VerifyButton } from './VerifyButton';
import { AnchorButton } from './AnchorButton';
import type { VerificationResult, VerificationStatus } from '../../../domain/types/blockchain';

interface AnalysisCardProps {
  refId: string;
  createdAt: string;
  isAnchored: boolean;
  payloadHash?: string;
  txHash?: string;
  anchoredAt?: string;
  isAdmin?: boolean;
  onVerified?: (result: VerificationResult) => void;
  onAnchored?: () => void;
}

/**
 * Card component displaying analysis blockchain info with verify/anchor actions
 */
export const AnalysisCard: React.FC<AnalysisCardProps> = ({
  refId,
  createdAt,
  isAnchored,
  payloadHash,
  txHash,
  anchoredAt,
  isAdmin = false,
  onVerified,
  onAnchored
}) => {
  const [verificationStatus, setVerificationStatus] = React.useState<VerificationStatus | null>(
    isAnchored ? null : 'NOT_ANCHORED'
  );

  const handleVerified = (result: VerificationResult) => {
    setVerificationStatus(result.status);
    onVerified?.(result);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const truncateHash = (hash: string) => {
    if (!hash || hash.length < 20) return hash;
    return `${hash.slice(0, 12)}...${hash.slice(-10)}`;
  };

  return (
    <div className="bg-gray-50 rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileText size={20} className="text-indigo-600" />
          <div>
            <h4 className="font-medium text-gray-900 font-mono text-sm">
              {refId}
            </h4>
            <p className="text-xs text-gray-500 flex items-center gap-1">
              <Clock size={12} />
              Created: {formatDate(createdAt)}
            </p>
          </div>
        </div>
        
        {verificationStatus && (
          <VerificationBadge status={verificationStatus} size="md" />
        )}
      </div>

      {/* Body */}
      <div className="px-6 py-4 space-y-3">
        {/* Payload Hash */}
        {payloadHash && (
          <div className="flex items-start gap-2">
            <Hash size={14} className="text-gray-400 mt-0.5" />
            <div>
              <p className="text-xs text-gray-500">Payload Hash</p>
              <p className="text-sm font-mono text-gray-700" title={payloadHash}>
                {truncateHash(payloadHash)}
              </p>
            </div>
          </div>
        )}

        {/* Transaction Hash */}
        {txHash && (
          <div className="flex items-start gap-2">
            <ExternalLink size={14} className="text-gray-400 mt-0.5" />
            <div>
              <p className="text-xs text-gray-500">Transaction Hash</p>
              <p className="text-sm font-mono text-gray-700" title={txHash}>
                {truncateHash(txHash)}
              </p>
            </div>
          </div>
        )}

        {/* Anchored At */}
        {anchoredAt && (
          <div className="flex items-start gap-2">
            <Clock size={14} className="text-gray-400 mt-0.5" />
            <div>
              <p className="text-xs text-gray-500">Anchored</p>
              <p className="text-sm text-gray-700">
                {formatDate(anchoredAt)}
              </p>
            </div>
          </div>
        )}

        {!isAnchored && (
          <p className="text-sm text-gray-500 italic">
            This analysis has not been anchored to the blockchain yet.
          </p>
        )}
      </div>

      {/* Footer - Actions */}
      <div className="px-6 py-4 bg-gray-100 border-t border-gray-200 flex items-center gap-3">
        {isAnchored && (
          <VerifyButton
            refId={refId}
            onVerified={handleVerified}
            variant="outline"
            size="sm"
          />
        )}
        
        {isAdmin && (
          <AnchorButton
            refId={refId}
            isAnchored={isAnchored}
            onAnchored={onAnchored}
            variant={isAnchored ? 'ghost' : 'default'}
            size="sm"
          />
        )}
      </div>
    </div>
  );
};
