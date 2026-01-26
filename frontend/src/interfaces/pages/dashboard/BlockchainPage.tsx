import React, { useState, useEffect } from 'react';
import { Shield, RefreshCw, Search, Filter } from 'lucide-react';
import { useAuth } from '../../../hooks/useAuth';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { blockchainApi } from '../../../infrastructure/api';
import {
  BlockchainStatusCard,
  AnalysisCard
} from '../../components/blockchain';
import type { BlockchainAnalysisItem } from '../../../domain/types/blockchain';

/**
 * Blockchain verification admin page
 * Allows viewing analyses, verifying integrity, and anchoring (admin only)
 */
export const BlockchainPage: React.FC = () => {
  const { user } = useAuth();
  const [analyses, setAnalyses] = useState<BlockchainAnalysisItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterAnchored, setFilterAnchored] = useState<'all' | 'anchored' | 'not-anchored'>('all');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [total, setTotal] = useState(0);

  // Check if user is admin
  const isAdmin = user?.roles?.includes('admin') || false;

  const fetchAnalyses = async (resetPage = false) => {
    const currentPage = resetPage ? 1 : page;
    setLoading(true);
    setError(null);

    try {
      const response = await blockchainApi.listAnalyses(currentPage, 12);
      
      if (resetPage) {
        setAnalyses(response.analyses);
        setPage(1);
      } else {
        setAnalyses(prev => [...prev, ...response.analyses]);
      }
      
      setHasMore(response.hasMore);
      setTotal(response.total);
    } catch (err: any) {
      // Handle both string and object error responses
      const errorData = err.response?.data?.error;
      let errorMessage: string;
      
      if (typeof errorData === 'object' && errorData !== null) {
        errorMessage = errorData.message || errorData.code || 'Failed to load analyses';
      } else if (typeof errorData === 'string') {
        errorMessage = errorData;
      } else {
        errorMessage = err.message || 'Failed to load analyses';
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyses(true);
  }, []);

  const handleLoadMore = () => {
    setPage(prev => prev + 1);
    fetchAnalyses(false);
  };

  const handleRefresh = () => {
    fetchAnalyses(true);
  };

  const handleAnchored = () => {
    // Refresh list after anchoring
    fetchAnalyses(true);
  };

  // Filter analyses
  const filteredAnalyses = analyses.filter(analysis => {
    // Search filter
    if (searchQuery && !analysis.refId.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    // Anchored filter
    if (filterAnchored === 'anchored' && !analysis.isAnchored) {
      return false;
    }
    if (filterAnchored === 'not-anchored' && analysis.isAnchored) {
      return false;
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
          <Shield className="text-indigo-400" />
          Blockchain Verification
        </h1>
        <p className="text-slate-300">
          Verify analysis integrity and manage blockchain anchoring
          {isAdmin && <span className="ml-2 text-indigo-400">(Admin Mode)</span>}
        </p>
      </div>

      {/* Status Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <BlockchainStatusCard autoRefresh refreshInterval={60000} />
        </div>
        
        {/* Quick Stats */}
        <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-gray-50 rounded-xl shadow-sm p-6 border border-gray-200">
            <p className="text-sm text-gray-500 mb-1">Total Analyses</p>
            <p className="text-3xl font-bold text-gray-900">{total}</p>
          </div>
          <div className="bg-gray-50 rounded-xl shadow-sm p-6 border border-gray-200">
            <p className="text-sm text-gray-500 mb-1">Anchored</p>
            <p className="text-3xl font-bold text-green-600">
              {analyses.filter(a => a.isAnchored).length}
            </p>
          </div>
          <div className="bg-gray-50 rounded-xl shadow-sm p-6 border border-gray-200">
            <p className="text-sm text-gray-500 mb-1">Pending</p>
            <p className="text-3xl font-bold text-yellow-600">
              {analyses.filter(a => !a.isAnchored).length}
            </p>
          </div>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="bg-gray-50 rounded-xl shadow-sm p-4 border border-gray-200">
        <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
          <div className="flex items-center gap-4 w-full sm:w-auto">
            <div className="relative flex-1 sm:w-64">
              <Search size={18} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <Input
                type="text"
                placeholder="Search by Ref ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <div className="flex items-center gap-2">
              <Filter size={18} className="text-gray-400" />
              <select
                value={filterAnchored}
                onChange={(e) => setFilterAnchored(e.target.value as any)}
                className="px-3 py-2 border border-gray-200 rounded-md text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="all">All</option>
                <option value="anchored">Anchored</option>
                <option value="not-anchored">Not Anchored</option>
              </select>
            </div>
          </div>
          
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={loading}
            className="gap-2"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700">
          {error}
        </div>
      )}

      {/* Analyses Grid */}
      {!error && (
        <>
          {filteredAnalyses.length === 0 ? (
            <div className="bg-gray-50 rounded-xl shadow-sm p-12 border border-gray-200 text-center">
              <Shield size={48} className="mx-auto text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Analyses Found</h3>
              <p className="text-gray-500">
                {searchQuery || filterAnchored !== 'all'
                  ? 'No analyses match your current filters.'
                  : 'No analyses have been created yet.'}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {filteredAnalyses.map((analysis) => (
                <AnalysisCard
                  key={analysis.refId}
                  refId={analysis.refId}
                  createdAt={analysis.createdAt}
                  isAnchored={analysis.isAnchored}
                  payloadHash={analysis.payloadHash}
                  txHash={analysis.txHash}
                  anchoredAt={analysis.anchoredAt}
                  isAdmin={isAdmin}
                  onAnchored={handleAnchored}
                />
              ))}
            </div>
          )}

          {/* Load More */}
          {hasMore && filteredAnalyses.length > 0 && (
            <div className="text-center pt-4">
              <Button
                variant="outline"
                onClick={handleLoadMore}
                disabled={loading}
                className="border-white text-white hover:bg-gray-800 hover:border-gray-800 hover:text-white"
              >
                {loading ? 'Loading...' : 'Load More'}
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
};
