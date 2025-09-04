import React, { useState, useEffect, useMemo } from 'react';
import { Tool, Server } from '../../types';
import { ToolExecution } from './ToolExecution';
// Simple input component
const Input = ({ 
  type = 'text', 
  placeholder = '', 
  value, 
  onChange, 
  className = '',
  disabled = false 
}: {
  type?: string;
  placeholder?: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  className?: string;
  disabled?: boolean;
}) => (
  <input
    type={type}
    placeholder={placeholder}
    value={value}
    onChange={onChange}
    disabled={disabled}
    className={`
      block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 
      sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white ${className}
      ${disabled ? 'cursor-not-allowed bg-gray-100 dark:bg-gray-800' : ''}
    `}
  />
);
import { classNames } from '../../utils/classNames';

// Simple icon components
const SearchIcon = ({ className = '' }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
  </svg>
);

const CodeIcon = ({ className = '' }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
  </svg>
);

const CollectionIcon = ({ className = '' }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
  </svg>
);

const Spinner = ({ className = '' }) => (
  <svg className={`animate-spin h-5 w-5 ${className}`} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
  </svg>
);

const XCircleIcon = ({ className = '' }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

// Simple tooltip component
const Tooltip = ({ content, children, placement = 'top' }: { content: string; children: React.ReactNode; placement?: 'top' | 'bottom' | 'left' | 'right' }) => {
  const [isVisible, setIsVisible] = React.useState(false);
  
  return (
    <div className="relative inline-block">
      <div
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        className="inline-block"
      >
        {children}
      </div>
      {isVisible && (
        <div 
          className={`
            absolute z-10 px-2 py-1 text-xs text-white bg-gray-900 rounded-md whitespace-nowrap
            ${{
              'bottom-full left-1/2 transform -translate-x-1/2 mb-2': placement === 'top',
              'top-full left-1/2 transform -translate-x-1/2 mt-2': placement === 'bottom',
              'right-full top-1/2 transform -translate-y-1/2 mr-2': placement === 'left',
              'left-full top-1/2 transform -translate-y-1/2 ml-2': placement === 'right',
            }[placement]}
          `}
        >
          {content}
          <div className={`
            absolute w-2 h-2 bg-gray-900 transform rotate-45 -translate-x-1/2
            ${{
              'bottom-0 left-1/2 -mb-1': placement === 'top',
              'top-0 left-1/2 -mt-1': placement === 'bottom',
              'right-0 top-1/2 -mr-1': placement === 'left',
              'left-0 top-1/2 -ml-1': placement === 'right',
            }[placement]}
          `} />
        </div>
      )}
    </div>
  );
};

interface ToolExplorerProps {
  server: Server | null;
  tools: Tool[];
  loading?: boolean;
  error?: string | null;
  onExecuteTool: (toolId: string, parameters: Record<string, any>) => Promise<any>;
  className?: string;
}

export const ToolExplorer: React.FC<ToolExplorerProps> = ({
  server,
  tools,
  loading = false,
  error = null,
  onExecuteTool,
  className = '',
}) => {
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [categories, setCategories] = useState<string[]>([]);

  // Extract categories from tools
  useEffect(() => {
    if (!tools?.length) return;
    
    const allCategories = new Set<string>();
    
    tools.forEach(tool => {
      if (tool.metadata?.category) {
        allCategories.add(tool.metadata.category);
      } else {
        // Default category for uncategorized tools
        allCategories.add('General');
      }
    });
    
    const sortedCategories = Array.from(allCategories).sort();
    setCategories(sortedCategories);
    
    // Select the first category by default if none selected
    if (!selectedCategory && sortedCategories.length > 0) {
      setSelectedCategory(sortedCategories[0]);
    }
  }, [tools, selectedCategory]);

  // Filter tools based on search query and selected category
  const filteredTools = React.useMemo(() => {
    if (loading || error || !tools) return [];
    
    return tools.filter(tool => {
      const searchLower = searchQuery.toLowerCase();
      const matchesSearch = tool.name.toLowerCase().includes(searchLower) ||
                         (tool.description || '').toLowerCase().includes(searchLower);
      const matchesCategory = !selectedCategory || 
                            tool.metadata?.category === selectedCategory ||
                            (!tool.metadata?.category && selectedCategory === 'General');
      
      return matchesSearch && matchesCategory;
    });
  }, [tools, searchQuery, selectedCategory, loading, error]);

  // Reset selected tool when server changes
  useEffect(() => {
    setSelectedTool(null);
  }, [server?.id]);
  
  // Handle case where server is not available
  if (!server) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400 p-4 text-center">
        <XCircleIcon className="h-12 w-12 text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No Server Selected</h3>
        <p className="mb-4">Please select a server to view available tools.</p>
      </div>
    );
  }

  const handleToolSelect = (tool: Tool) => {
    setSelectedTool(tool);
  };

  const handleBackToList = () => {
    setSelectedTool(null);
  };

  const handleExecuteTool = async (toolId: string, parameters: Record<string, any>) => {
    return onExecuteTool(toolId, parameters);
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
        <Spinner className="h-8 w-8 text-blue-500 animate-spin mb-2" />
        <p>Loading tools...</p>
        {server && (
          <p className="text-sm mt-1">Connecting to {server.name}</p>
        )}
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-4 text-center">
        <XCircleIcon className="h-12 w-12 text-red-500 mb-3" />
        <h3 className="text-lg font-medium text-red-600 dark:text-red-400 mb-1">
          Failed to load tools
        </h3>
        <p className="text-gray-600 dark:text-gray-300 mb-4">
          {error || 'An unknown error occurred while loading tools.'}
        </p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          Retry
        </button>
      </div>
    );
  }

  // No tools available
  if (!tools || tools.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400 p-4 text-center">
        <CollectionIcon className="h-12 w-12 text-gray-300 mb-3" />
        <h3 className="text-lg font-medium text-gray-600 dark:text-gray-300 mb-1">
          No tools available
        </h3>
        <p className="mb-4">
          {server 
            ? 'This server does not have any tools configured.'
            : 'Please select a server to view available tools.'}
        </p>
      </div>
    );
  }

  return (
    <div className={classNames('flex flex-col h-full', className)}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100">
            {server?.name || 'No server selected'}
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {filteredTools.length} {filteredTools.length === 1 ? 'tool' : 'tools'} available
          </p>
        </div>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <SearchIcon className="h-5 w-5 text-gray-400" />
          </div>
          <Input
            type="text"
            placeholder="Search tools..."
            className="pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            disabled={!server}
          />
        </div>
      </div>

      {categories.length > 0 && (
        <div className="mb-4">
          <div className="flex items-center mb-2">
            <CollectionIcon className="h-4 w-4 text-gray-400 mr-2" />
            <span className="text-sm font-medium text-gray-500 dark:text-gray-400">
              Categories
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {categories.map((category) => (
              <Tooltip key={category} content={`Show ${category} tools`}>
                <button
                  type="button"
                  onClick={() => setSelectedCategory(category)}
                  className={classNames(
                    'px-3 py-1 text-sm font-medium rounded-full transition-colors',
                    'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
                    selectedCategory === category
                      ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600'
                  )}
                >
                  {category}
                  <span className="ml-1.5 inline-flex items-center justify-center px-2 py-0.5 text-xs rounded-full bg-blue-200 text-blue-800 dark:bg-blue-800 dark:text-blue-200">
                    {tools.filter(t => t.metadata?.category === category || (!t.metadata?.category && category === 'General')).length}
                  </span>
                </button>
              </Tooltip>
            ))}
          </div>
        </div>
      )}

      {filteredTools.length === 0 ? (
        <div className="text-center py-12">
          <SearchIcon className="mx-auto h-12 w-12 text-gray-300" />
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
            No tools found
          </h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            No tools match "{searchQuery}" in {selectedCategory}.
          </p>
          <div className="mt-4">
            <button
              type="button"
              onClick={() => {
                setSearchQuery('');
                setSelectedCategory(null);
              }}
              className="text-sm font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300"
            >
              Clear search and filters<span aria-hidden="true"> &rarr;</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
          {filteredTools.map((tool) => (
            <Tooltip key={tool.id} content={`Click to use ${tool.name}`} placement="top">
              <div
                onClick={() => setSelectedTool(tool)}
                className={classNames(
                  'group p-4 border rounded-lg cursor-pointer transition-all',
                  'hover:shadow-md hover:border-blue-300 dark:hover:border-blue-700',
                  'dark:border-gray-700 dark:bg-gray-800/50',
                  'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
                  selectedTool?.id === tool.id 
                    ? 'ring-2 ring-blue-500 border-transparent' 
                    : 'hover:ring-1 hover:ring-blue-200 dark:hover:ring-blue-900/50'
                )}
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setSelectedTool(tool);
                  }
                }}
              >
                <div className="flex items-start">
                  <div className="flex-shrink-0 h-10 w-10 rounded-full bg-blue-100 dark:bg-blue-900/70 flex items-center justify-center group-hover:bg-blue-200 dark:group-hover:bg-blue-800 transition-colors">
                    <CodeIcon className="h-5 w-5 text-blue-600 dark:text-blue-300" />
                  </div>
                  <div className="ml-4 flex-1 min-w-0">
                    <div className="flex justify-between items-start">
                      <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {tool.name}
                      </h3>
                      {tool.metadata?.deprecated && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300">
                          Deprecated
                        </span>
                      )}
                    </div>
                    {tool.description && (
                      <p className="mt-1 text-sm text-gray-500 dark:text-gray-400 line-clamp-2">
                        {tool.description}
                      </p>
                    )}
                    {tool.metadata?.version && (
                      <div className="mt-2 flex items-center text-xs text-gray-400">
                        <span>v{tool.metadata.version}</span>
                        {tool.metadata?.lastUpdated && (
                          <span className="mx-1">•</span>
                        )}
                        {tool.metadata?.lastUpdated && (
                          <span>Updated {new Date(tool.metadata.lastUpdated).toLocaleDateString()}</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </Tooltip>
          ))}
        </div>
      )}
    </div>
  );

  if (selectedTool && server) {
    return (
      <div className={className}>
        <button
          type="button"
          onClick={handleBackToList}
          className="inline-flex items-center text-sm font-medium text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 mb-4"
        >
          <svg
            className="h-5 w-5 mr-1"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
              clipRule="evenodd"
            />
          </svg>
          Back to tools
        </button>

        <ToolExecution
          tool={selectedTool}
          serverId={server.id}
          onExecute={handleExecuteTool}
        />
      </div>
    );
  }

  return (
    <div className={classNames('flex flex-col h-full', className)}>
      {/* ... rest of the JSX ... */}
    </div>
  );
};
