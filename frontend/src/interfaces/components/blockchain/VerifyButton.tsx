import React, { useState } from 'react';
import { Shield, Loader2, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { Button } from '../../../components/ui/button';
import { blockchainApi } from '../../../infrastructure/api';
import type { VerificationResult, VerificationStatus } from '../../../domain/types/blockchain';

interface VerifyButtonProps {
  refId: string;
  onVerified?: (result: VerificationResult) => void;
  variant?: 'default' | 'outline' | 'ghost';
  size?: 'default' | 'sm' | 'lg';
  showResultInline?: boolean;
}

/**
 * Button component that triggers blockchain verification for an analysis
 * Displays verification result inline or passes to callback
 */
export const VerifyButton: React.FC<VerifyButtonProps> = ({
  refId,
  onVerified,
  variant = 'outline',
  size = 'default',
  showResultInline = true
}) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleVerify = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const verificationResult = await blockchainApi.verifyAnalysis(refId);
      setResult(verificationResult);
      onVerified?.(verificationResult);
    } catch (err: any) {
      // Handle both string and object error responses
      const errorData = err.response?.data?.error;
      let errorMessage: string;
      
      if (typeof errorData === 'object' && errorData !== null) {
        errorMessage = errorData.message || errorData.code || 'Verification failed';
      } else if (typeof errorData === 'string') {
        errorMessage = errorData;
      } else {
        errorMessage = err.message || 'Verification failed';
      }
      
      setError(errorMessage);
      // Create error result
      const errorResult: VerificationResult = {
        verified: false,
        status: 'ERROR' as VerificationStatus,
        refId,
        error: errorMessage
      };
      onVerified?.(errorResult);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = () => {
    if (!result) return null;
    
    switch (result.status) {
      case 'VERIFIED':
        return <CheckCircle className="text-green-600" size={16} />;
      case 'NOT_VERIFIED':
        return <XCircle className="text-red-600" size={16} />;
      case 'NOT_ANCHORED':
        return <AlertCircle className="text-gray-500" size={16} />;
      default:
        return <AlertCircle className="text-yellow-600" size={16} />;
    }
  };

  const getStatusText = () => {
    if (!result) return null;
    
    switch (result.status) {
      case 'VERIFIED':
        return <span className="text-green-600 font-medium">Verified ✓</span>;
      case 'NOT_VERIFIED':
        return <span className="text-red-600 font-medium">Not Verified ✗</span>;
      case 'NOT_ANCHORED':
        return <span className="text-gray-500 font-medium">Not Anchored</span>;
      default:
        return <span className="text-yellow-600 font-medium">Error</span>;
    }
  };

  return (
    <div className="inline-flex items-center gap-2">
      <Button
        variant={variant}
        size={size}
        onClick={handleVerify}
        disabled={loading}
        className="gap-2"
      >
        {loading ? (
          <>
            <Loader2 size={16} className="animate-spin" />
            Verifying...
          </>
        ) : (
          <>
            <Shield size={16} />
            Verify Integrity
          </>
        )}
      </Button>

      {showResultInline && !loading && (result || error) && (
        <div className="flex items-center gap-1.5">
          {error ? (
            <span className="text-red-500 text-sm">{error}</span>
          ) : (
            <>
              {getStatusIcon()}
              {getStatusText()}
            </>
          )}
        </div>
      )}
    </div>
  );
};
