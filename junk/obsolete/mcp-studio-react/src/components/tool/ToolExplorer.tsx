import React, { useState, useEffect } from 'react';
import { Tool } from '../../types';
import { useApi } from '../../services';

interface ToolExplorerProps {
  serverId: string;
  onSelectTool: (tool: Tool) => void;
  className?: string;
}

export const ToolExplorer: React.FC<ToolExplorerProps> = ({
  serverId,
  onSelectTool,
  className = '',
}) => {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const { getTools } = useApi();

  // Load tools when serverId changes
  useEffect(() => {
    const loadTools = async () => {
      if (!serverId) {
        setTools([]);
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const serverTools = await getTools(serverId);
        setTools(serverTools);
      } catch (err) {
        console.error('Failed to load tools:', err);
        setError('Failed to load tools. Please try again.');
        setTools([]);
      } finally {
        setLoading(false);
      }
    };

    loadTools();
  }, [serverId, getTools]);

  // Extract unique categories from tools
  const categories = React.useMemo(() => {
    const cats = new Set<string>();
    tools.forEach(tool => {
      const category = tool.metadata?.category || 'Uncategorized';
      cats.add(category);
    });
    return ['all', ...Array.from(cats).sort()];
  }, [tools]);

  // Filter tools based on search query and selected category
  const filteredTools = React.useMemo(() => {
    return tools.filter(tool => {
      const matchesSearch = tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tool.description?.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesCategory = selectedCategory === 'all' || 
        (tool.metadata?.category || 'Uncategorized') === selectedCategory;
      
      return matchesSearch && matchesCategory;
    });
  }, [tools, searchQuery, selectedCategory]);

  if (loading) {
    return (
      <div className={`p-4 ${className}`}>
        <div className="animate-pulse space-y-3">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="space-y-2">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`p-4 text-red-600 ${className}`}>
        <p>{error}</p>
      </div>
    );
  }

  if (tools.length === 0) {
    return (
      <div className={`p-4 text-center text-gray-500 ${className}`}>
        <p>No tools available for this server.</p>
      </div>
    );
  }

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Search and filter */}
      <div className="p-4 border-b border-gray-200">
        <div className="mb-4">
          <div className="relative rounded-md shadow-sm">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg
                className="h-5 w-5 text-gray-400"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <input
              type="text"
              className="focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 sm:text-sm border-gray-300 rounded-md py-2 border"
              placeholder="Search tools..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        <div className="flex overflow-x-auto pb-2 -mx-1">
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-3 py-1 text-sm font-medium rounded-full mx-1 whitespace-nowrap ${
                selectedCategory === category
                  ? 'bg-blue-100 text-blue-800'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {category.charAt(0).toUpperCase() + category.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Tool list */}
      <div className="flex-1 overflow-y-auto">
        {filteredTools.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <p>No tools match your search criteria.</p>
          </div>
        ) : (
          <ul className="divide-y divide-gray-200">
            {filteredTools.map((tool) => (
              <li key={tool.name}>
                <button
                  onClick={() => onSelectTool(tool)}
                  className="w-full text-left p-4 hover:bg-gray-50 focus:outline-none focus:bg-gray-50 transition-colors"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">
                        {tool.name}
                      </h3>
                      <p className="mt-1 text-sm text-gray-500">
                        {tool.description || 'No description available'}
                      </p>
                      {tool.metadata?.category && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mt-2">
                          {tool.metadata.category}
                        </span>
                      )}
                    </div>
                    <div className="ml-4 flex-shrink-0">
                      <svg
                        className="h-5 w-5 text-gray-400"
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                        aria-hidden="true"
                      >
                        <path
                          fillRule="evenodd"
                          d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};
