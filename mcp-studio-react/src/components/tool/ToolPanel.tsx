import React, { useState, useEffect } from 'react';
import { Tool, ToolExecutionResult } from '../../types';
import { useApi, useWebSocket } from '../../services';

interface ToolPanelProps {
  serverId: string;
  tools: Tool[];
  className?: string;
}

export const ToolPanel: React.FC<ToolPanelProps> = ({ serverId, tools, className = '' }) => {
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null);
  const [parameters, setParameters] = useState<Record<string, any>>({});
  const [results, setResults] = useState<Record<string, ToolExecutionResult>>({});
  const [isExecuting, setIsExecuting] = useState(false);
  const [activeTab, setActiveTab] = useState<'form' | 'results'>('form');
  const { executeTool: wsExecuteTool } = useWebSocket();
  const { executeTool: apiExecuteTool } = useApi();

  useEffect(() => {
    // Reset form when tool changes
    if (selectedTool) {
      const initialParams = selectedTool.parameters.reduce((acc, param) => {
        if (param.default !== undefined) {
          acc[param.name] = param.default;
        } else if (param.type === 'boolean') {
          acc[param.name] = false;
        } else if (param.type === 'number') {
          acc[param.name] = 0;
        } else if (param.type === 'array') {
          acc[param.name] = [];
        } else if (param.type === 'object') {
          acc[param.name] = {};
        } else {
          acc[param.name] = '';
        }
        return acc;
      }, {} as Record<string, any>);
      setParameters(initialParams);
    }
  }, [selectedTool]);

  const handleParameterChange = (name: string, value: any) => {
    setParameters(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTool) return;

    setIsExecuting(true);
    setActiveTab('results');
    
    try {
      // First try WebSocket
      const executionId = wsExecuteTool(serverId, selectedTool.name, parameters);
      
      // Fallback to REST API if WebSocket fails
      if (!executionId) {
        const result = await apiExecuteTool(serverId, selectedTool.name, parameters);
        setResults(prev => ({
          ...prev,
          [Date.now()]: {
            success: true,
            result,
            timestamp: new Date().toISOString(),
          }
        }));
      }
    } catch (error) {
      console.error('Error executing tool:', error);
      setResults(prev => ({
        ...prev,
        [Date.now()]: {
          success: false,
          error: error instanceof Error ? error.message : 'Failed to execute tool',
          timestamp: new Date().toISOString(),
        }
      }));
    } finally {
      setIsExecuting(false);
    }
  };

  const renderParameterInput = (param: Tool['parameters'][0]) => {
    const value = parameters[param.name] ?? '';
    
    if (param.enum) {
      return (
        <select
          className="w-full p-2 border rounded"
          value={value}
          onChange={(e) => handleParameterChange(param.name, e.target.value)}
        >
          {param.enum.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      );
    }

    switch (param.type) {
      case 'boolean':
        return (
          <input
            type="checkbox"
            checked={!!value}
            onChange={(e) => handleParameterChange(param.name, e.target.checked)}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
        );
      case 'number':
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => handleParameterChange(param.name, Number(e.target.value))}
            className="w-full p-2 border rounded"
          />
        );
      case 'string':
      default:
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleParameterChange(param.name, e.target.value)}
            className="w-full p-2 border rounded"
            placeholder={param.description}
          />
        );
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow overflow-hidden ${className}`}>
      <div className="border-b border-gray-200">
        <nav className="flex -mb-px">
          <button
            type="button"
            className={`py-4 px-6 text-center border-b-2 font-medium text-sm ${
              activeTab === 'form'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('form')}
          >
            Tool Form
          </button>
          <button
            type="button"
            className={`py-4 px-6 text-center border-b-2 font-medium text-sm ${
              activeTab === 'results'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('results')}
          >
            Results
          </button>
        </nav>
      </div>

      <div className="p-4">
        {activeTab === 'form' ? (
          <div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Select Tool
              </label>
              <select
                className="w-full p-2 border rounded"
                value={selectedTool?.name || ''}
                onChange={(e) => {
                  const tool = tools.find(t => t.name === e.target.value) || null;
                  setSelectedTool(tool);
                }}
              >
                <option value="">-- Select a tool --</option>
                {tools.map((tool) => (
                  <option key={tool.name} value={tool.name}>
                    {tool.name}
                  </option>
                ))}
              </select>
            </div>

            {selectedTool && (
              <form onSubmit={handleSubmit}>
                <div className="space-y-4">
                  {selectedTool.parameters.map((param) => (
                    <div key={param.name}>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {param.name}
                        {param.required && <span className="text-red-500">*</span>}
                        {param.description && (
                          <span className="text-xs text-gray-500 ml-2">
                            {param.description}
                          </span>
                        )}
                      </label>
                      {renderParameterInput(param)}
                    </div>
                  ))}
                </div>

                <div className="mt-6">
                  <button
                    type="submit"
                    disabled={isExecuting}
                    className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                  >
                    {isExecuting ? 'Executing...' : 'Execute Tool'}
                  </button>
                </div>
              </form>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {Object.entries(results).length === 0 ? (
              <p className="text-gray-500 text-center py-4">
                No execution results yet. Run a tool to see results here.
              </p>
            ) : (
              Object.entries(results)
                .sort(([a], [b]) => Number(b) - Number(a))
                .map(([timestamp, result]) => (
                  <div
                    key={timestamp}
                    className={`p-4 rounded border ${
                      result.success ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-medium">
                          {result.success ? 'Execution Succeeded' : 'Execution Failed'}
                        </h3>
                        <p className="text-sm text-gray-500">
                          {new Date(result.timestamp || timestamp).toLocaleString()}
                        </p>
                      </div>
                      {!result.success && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          Error
                        </span>
                      )}
                    </div>
                    
                    <div className="mt-2">
                      <pre className="text-xs p-2 bg-white rounded border overflow-auto max-h-60">
                        {result.error
                          ? result.error
                          : JSON.stringify(result.result, null, 2)}
                      </pre>
                    </div>
                  </div>
                ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};
