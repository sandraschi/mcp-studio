import React from 'react';

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

interface RuntCardProps {
  repo: RepoInfo;
  onClick?: () => void;
}

const colorClasses = {
  red: {
    bg: 'bg-red-50 dark:bg-red-900/20',
    border: 'border-red-300 dark:border-red-700',
    badge: 'bg-red-500',
    text: 'text-red-700 dark:text-red-400',
  },
  orange: {
    bg: 'bg-orange-50 dark:bg-orange-900/20',
    border: 'border-orange-300 dark:border-orange-700',
    badge: 'bg-orange-500',
    text: 'text-orange-700 dark:text-orange-400',
  },
  green: {
    bg: 'bg-green-50 dark:bg-green-900/20',
    border: 'border-green-300 dark:border-green-700',
    badge: 'bg-green-500',
    text: 'text-green-700 dark:text-green-400',
  },
};

export const RuntCard: React.FC<RuntCardProps> = ({ repo, onClick }) => {
  const colors = colorClasses[repo.status_color];

  return (
    <div
      className={`rounded-xl border-2 ${colors.border} ${colors.bg} p-4 cursor-pointer 
                  hover:shadow-lg transition-all duration-200 hover:scale-[1.02]`}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{repo.status_emoji}</span>
          <h3 className="font-bold text-lg text-gray-900 dark:text-white">
            {repo.name}
          </h3>
        </div>
        <span className={`px-3 py-1 rounded-full text-white text-sm font-medium ${colors.badge}`}>
          {repo.status_label}
        </span>
      </div>

      {/* FastMCP Version */}
      <div className="flex items-center gap-4 mb-3 text-sm">
        <span className="text-gray-600 dark:text-gray-400">
          FastMCP: <strong className={repo.fastmcp_version ? '' : 'text-red-500'}>
            {repo.fastmcp_version || 'Not found'}
          </strong>
        </span>
        <span className="text-gray-600 dark:text-gray-400">
          Tools: <strong>{repo.tool_count}</strong>
        </span>
        {repo.sota_score !== undefined && (
          <span className="text-gray-600 dark:text-gray-400">
            Score: <strong>{repo.sota_score}/100</strong>
          </span>
        )}
      </div>

      {/* Feature badges */}
      <div className="flex flex-wrap gap-2 mb-3">
        <FeatureBadge label="CI" has={repo.has_ci} />
        <FeatureBadge label="Ruff" has={repo.has_ruff} />
        <FeatureBadge label="Tests" has={repo.has_tests} />
        <FeatureBadge label="Help" has={repo.has_help_tool} />
        <FeatureBadge label="Status" has={repo.has_status_tool} />
        <FeatureBadge label="DXT" has={repo.has_dxt} />
        <FeatureBadge label="Logging" has={repo.has_proper_logging} />
        {repo.has_portmanteau && <FeatureBadge label="Portmanteau" has={true} />}
      </div>

      {/* Issues count */}
      {repo.runt_reasons.length > 0 && (
        <div className={`text-sm ${colors.text}`}>
          {repo.runt_reasons.length} issue{repo.runt_reasons.length !== 1 ? 's' : ''} found
        </div>
      )}
    </div>
  );
};

const FeatureBadge: React.FC<{ label: string; has: boolean }> = ({ label, has }) => (
  <span
    className={`px-2 py-0.5 rounded text-xs font-medium ${
      has
        ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100'
        : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400 line-through'
    }`}
  >
    {label}
  </span>
);

export default RuntCard;

