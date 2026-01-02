import React from 'react';
import { Tool } from '../../types';

interface ToolCardProps {
  tool: Tool;
  onClick: () => void;
}

const ToolCard: React.FC<ToolCardProps> = ({ tool, onClick }) => {
  const getCategoryColor = (category: string) => {
    // Simple hash function to generate consistent colors for categories
    const hash = category.split('').reduce((acc, char) => {
      return char.charCodeAt(0) + ((acc << 5) - acc);
    }, 0);
    
    const colors = [
      'bg-blue-100 text-blue-800',
      'bg-green-100 text-green-800',
      'bg-purple-100 text-purple-800',
      'bg-pink-100 text-pink-800',
      'bg-indigo-100 text-indigo-800',
      'bg-yellow-100 text-yellow-800',
      'bg-red-100 text-red-800',
      'bg-teal-100 text-teal-800',
    ];
    
    return colors[Math.abs(hash) % colors.length];
  };

  return (
    <div 
      className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300 cursor-pointer border border-gray-200 dark:border-gray-700"
      onClick={onClick}
    >
      <div className="p-5">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-1">
              {tool.name}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-300 line-clamp-2">
              {tool.description}
            </p>
          </div>
          <div className="ml-4 flex-shrink-0">
            <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
              <span className="text-blue-600 dark:text-blue-300 font-medium">
                {tool.name.charAt(0).toUpperCase()}
              </span>
            </div>
          </div>
        </div>

        {/* Categories */}
        {tool.categories && tool.categories.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1">
            {tool.categories.slice(0, 2).map((category) => (
              <span 
                key={category}
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  getCategoryColor(category)
                }`}
              >
                {category}
              </span>
            ))}
            {tool.categories.length > 2 && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                +{tool.categories.length - 2} more
              </span>
            )}
          </div>
        )}

        {/* Parameters */}
        {tool.parameters && tool.parameters.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
            <div className="flex items-center text-xs text-gray-500 dark:text-gray-400 mb-1">
              <svg className="w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {tool.parameters.length} parameters
            </div>
            <div className="flex flex-wrap gap-1">
              {tool.parameters.slice(0, 3).map((param) => (
                <span 
                  key={param.name}
                  className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                  title={`${param.name}: ${param.type}`}
                >
                  {param.name}
                </span>
              ))}
              {tool.parameters.length > 3 && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                  +{tool.parameters.length - 3}
                </span>
              )}
            </div>
          </div>
        )}
      </div>
      
      <div className="bg-gray-50 dark:bg-gray-700 px-5 py-3 text-right">
        <button 
          className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          onClick={(e) => {
            e.stopPropagation();
            onClick();
          }}
        >
          Test Tool
        </button>
      </div>
    </div>
  );
};

export default ToolCard;
