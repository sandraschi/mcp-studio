import React, { useState, useEffect } from 'react';
import { RuntCard } from './RuntCard';

interface RepoInfo {
  name: string;
  path: string;
  fastmcp_version: string | null;
  tool_count: number;
  has_portmanteau: boolean;
  has_ci: boolean;
  ci_workflows: number;
  has_dxt: boolean;
  has_help_tool: boolean;
  has_status_tool: boolean;
  has_proper_docstrings: boolean;
  has_ruff: boolean;
  has_tests: boolean;
  has_unit_tests: boolean;
  has_integration_tests: boolean;
  has_pytest_config: boolean;
  has_coverage_config: boolean;
  test_file_count: number;
  has_proper_logging: boolean;
  print_statement_count: number;
  bare_except_count: number;
  lazy_error_msg_count: number;
  is_runt: boolean;
  runt_reasons: string[];
  recommendations: string[];
  status_emoji: string;
  status_color: 'red' | 'orange' | 'green';
  status_label: string;
  sota_score?: number;
}

interface RuntAnalysisResponse {
  success: boolean;
  summary: {
    total_mcp_repos: number;
    runts: number;
    sota: number;
  };
  runts: RepoInfo[];
  sota_repos: RepoInfo[];
  scan_path: string;
}

export const RuntDashboard: React.FC = () => {
  const [data, setData] = useState<RuntAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'red' | 'orange' | 'green'>('all');
  const [selectedRepo, setSelectedRepo] = useState<RepoInfo | null>(null);

  useEffect(() => {
    fetchRunts();
  }, []);

  const fetchRunts = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/runts/?include_sota=true');
      if (!response.ok) throw new Error('Failed to fetch runt data');
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        Error: {error || 'No data'}
      </div>
    );
  }

  const allRepos = [...data.runts, ...data.sota_repos];
  const filteredRepos = filter === 'all' 
    ? allRepos 
    : allRepos.filter(r => r.status_color === filter);

  const counts = {
    red: allRepos.filter(r => r.status_color === 'red').length,
    orange: allRepos.filter(r => r.status_color === 'orange').length,
    green: allRepos.filter(r => r.status_color === 'green').length,
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          🔍 Runt Analyzer
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Scanning: <code className="bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
            {data.scan_path}
          </code>
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <SummaryCard
          label="Total MCP Repos"
          count={data.summary.total_mcp_repos}
          color="blue"
          onClick={() => setFilter('all')}
          active={filter === 'all'}
        />
        <SummaryCard
          label="Runts"
          count={counts.red}
          color="red"
          emoji="🐛"
          onClick={() => setFilter('red')}
          active={filter === 'red'}
        />
        <SummaryCard
          label="Improvable"
          count={counts.orange}
          color="orange"
          emoji="⚠️"
          onClick={() => setFilter('orange')}
          active={filter === 'orange'}
        />
        <SummaryCard
          label="SOTA"
          count={counts.green}
          color="green"
          emoji="✅"
          onClick={() => setFilter('green')}
          active={filter === 'green'}
        />
      </div>

      {/* Repo Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredRepos.map((repo) => (
          <RuntCard
            key={repo.path}
            repo={repo}
            onClick={() => setSelectedRepo(repo)}
          />
        ))}
      </div>

      {/* Detail Modal */}
      {selectedRepo && (
        <RepoDetailModal
          repo={selectedRepo}
          onClose={() => setSelectedRepo(null)}
        />
      )}
    </div>
  );
};

interface SummaryCardProps {
  label: string;
  count: number;
  color: 'blue' | 'red' | 'orange' | 'green';
  emoji?: string;
  onClick: () => void;
  active: boolean;
}

const SummaryCard: React.FC<SummaryCardProps> = ({ label, count, color, emoji, onClick, active }) => {
  const colorClasses = {
    blue: 'bg-blue-500',
    red: 'bg-red-500',
    orange: 'bg-orange-500',
    green: 'bg-green-500',
  };

  return (
    <div
      className={`p-4 rounded-xl cursor-pointer transition-all ${
        active ? 'ring-2 ring-offset-2 ring-blue-500' : ''
      } bg-white dark:bg-gray-800 shadow hover:shadow-lg`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <span className="text-gray-600 dark:text-gray-400">{label}</span>
        {emoji && <span className="text-xl">{emoji}</span>}
      </div>
      <div className="mt-2 flex items-center gap-2">
        <span className={`w-3 h-3 rounded-full ${colorClasses[color]}`}></span>
        <span className="text-2xl font-bold text-gray-900 dark:text-white">{count}</span>
      </div>
    </div>
  );
};

interface RepoDetailModalProps {
  repo: RepoInfo;
  onClose: () => void;
}

const RepoDetailModal: React.FC<RepoDetailModalProps> = ({ repo, onClose }) => {
  const colorClasses = {
    red: 'border-red-500',
    orange: 'border-orange-500',
    green: 'border-green-500',
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className={`bg-white dark:bg-gray-800 rounded-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto
                    border-t-4 ${colorClasses[repo.status_color]}`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <span className="text-3xl">{repo.status_emoji}</span>
              <div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">{repo.name}</h2>
                <span className="text-sm text-gray-500">{repo.status_label}</span>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl"
            >
              ×
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="text-2xl font-bold">{repo.fastmcp_version || '-'}</div>
              <div className="text-sm text-gray-500">FastMCP</div>
            </div>
            <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="text-2xl font-bold">{repo.tool_count}</div>
              <div className="text-sm text-gray-500">Tools</div>
            </div>
            <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="text-2xl font-bold">{repo.sota_score ?? '-'}</div>
              <div className="text-sm text-gray-500">Score</div>
            </div>
          </div>

          {/* Issues */}
          {repo.runt_reasons.length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                Issues ({repo.runt_reasons.length})
              </h3>
              <ul className="space-y-1">
                {repo.runt_reasons.map((reason, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
                    <span className="text-red-500">•</span>
                    {reason}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommendations */}
          {repo.recommendations.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                Recommendations
              </h3>
              <ul className="space-y-1">
                {repo.recommendations.map((rec, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
                    <span className="text-green-500">→</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Path */}
          <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
            <code className="text-xs text-gray-500 break-all">{repo.path}</code>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RuntDashboard;

