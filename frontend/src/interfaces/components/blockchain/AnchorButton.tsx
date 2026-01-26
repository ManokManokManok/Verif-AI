import React, { useState } from 'react';
import { Anchor, Loader2, CheckCircle, XCircle } from 'lucide-react';
import { Button } from '../../../components/ui/button';
import { blockchainApi } from '../../../infrastructure/api';
import type { AnchorResult } from '../../../domain/types/blockchain';

interface AnchorButtonProps {
  refId: string;
  isAnchored?: boolean;
  onAnchored?: (result: AnchorResult) => void;
  variant?: 'default' | 'outline' | 'ghost' | 'destructive';
  size?: 'default' | 'sm' | 'lg';
}

/**
 * Button component that triggers blockchain anchoring for an analysis
 * Admin-only action that writes analysis hash to the blockchain
 */
export const AnchorButton: React.FC<AnchorButtonProps> = ({
  refId,
  isAnchored = false,
  onAnchored,
  variant = 'default',
  size = 'default'
}) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnchorResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnchor = async () => {
    if (isAnchored && !confirm('This analysis is already anchored. Re-anchoring will create a new blockchain record. Continue?')) {
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // Pass force=true if re-anchoring (already anchored)
      const anchorResult = await blockchainApi.anchorAnalysis(refId, isAnchored);
      setResult(anchorResult);
      onAnchored?.(anchorResult);
    } catch (err: any) {
      // Handle both string and object error responses
      const errorData = err.response?.data?.error;
      let errorMessage: string;
      
      if (typeof errorData === 'object' && errorData !== null) {
        errorMessage = errorData.message || errorData.code || 'Anchoring failed';
      } else if (typeof errorData === 'string') {
        errorMessage = errorData;
      } else {
        errorMessage = err.message || 'Anchoring failed';
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  if (result?.success) {
    return (
      <div className="flex items-center gap-2 text-green-600">
        <CheckCircle size={16} />
        <span className="text-sm font-medium">Anchored successfully</span>
      </div>
    );
  }

  return (
    <div className="inline-flex flex-col gap-1">
      <Button
        variant={variant}
        size={size}
        onClick={handleAnchor}
        disabled={loading}
        className="gap-2"
      >
        {loading ? (
          <>
            <Loader2 size={16} className="animate-spin" />
            Anchoring...
          </>
        ) : (
          <>
            <Anchor size={16} />
            {isAnchored ? 'Re-anchor' : 'Anchor to Chain'}
          </>
        )}
      </Button>

      {error && (
        <div className="flex items-start gap-1.5 text-red-500 text-sm max-w-xs">
          <XCircle size={14} className="shrink-0 mt-0.5" />
          <span className="wrap-break-words">{error}</span>
        </div>
      )}
    </div>
  );
};
