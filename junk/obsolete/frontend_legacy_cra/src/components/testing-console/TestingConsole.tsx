import React, { useState, useRef, useEffect } from 'react';
import { Tool } from '../../types';
import { PlayIcon, StopIcon, SaveIcon, CodeIcon, EyeIcon, ClockIcon, CpuChipIcon } from '../common/Icons';

interface Parameter {
  name: string;
  type: string;
  required?: boolean;
  description?: string;
  default?: any;
}

interface TestingConsoleProps {
  tool: Tool | null;
  onClose: () => void;
}

const TestingConsole: React.FC<TestingConsoleProps> = ({ tool, onClose }) => {
  const [activeTab, setActiveTab] = useState<'form' | 'json'>('form');
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionTime, setExecutionTime] = useState<number | null>(null);
  const [output, setOutput] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [formValues, setFormValues] = useState<Record<string, any>>({});
  const [jsonInput, setJsonInput] = useState<string>('{}');
  const outputRef = useRef<HTMLDivElement>(null);

  // Initialize form values when tool changes
  useEffect(() => {
    if (!tool) return;
    
    const initialValues: Record<string, any> = {};
    tool.parameters?.forEach(param => {
      if (param.default !== undefined) {
        initialValues[param.name] = param.default;
      } else if (param.type === 'boolean') {
        initialValues[param.name] = false;
      } else if (param.type === 'number') {
        initialValues[param.name] = 0;
      } else if (param.type === 'array') {
        initialValues[param.name] = [];
      } else if (param.type === 'object') {
        initialValues[param.name] = {};
      } else {
        initialValues[param.name] = '';
      }
    });
    
    setFormValues(initialValues);
    setJsonInput(JSON.stringify(initialValues, null, 2));
    setOutput(null);
    setError(null);
    setExecutionTime(null);
  }, [tool]);

  const handleFormChange = (param: string, value: any) => {
    setFormValues(prev => ({
      ...prev,
      [param]: value
    }));
    
    // Update JSON input when form changes
    try {
      const newJson = {
        ...formValues,
        [param]: value
      };
      setJsonInput(JSON.stringify(newJson, null, 2));
    } catch (e) {
      console.error('Error updating JSON input:', e);
    }
  };

  const handleJsonChange = (value: string) => {
    setJsonInput(value);
    
    // Try to update form values when JSON changes
    try {
      const parsed = JSON.parse(value);
      setFormValues(parsed);
    } catch (e) {
      // Invalid JSON, don't update form
    }
  };

  const executeTool = async () => {
    if (!tool) return;
    
    setIsExecuting(true);
    setError(null);
    setOutput(null);
    
    try {
      const params = activeTab === 'form' 
        ? { ...formValues }
        : JSON.parse(jsonInput);
      
      const startTime = performance.now();
      
      // Simulate API call - replace with actual API call
      const response = await new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            success: true,
            result: `Simulated execution of ${tool.name} with params: ${JSON.stringify(params)}`,
            timestamp: new Date().toISOString()
          });
        }, 1000);
      });
      
      const endTime = performance.now();
      setExecutionTime(Math.round(endTime - startTime));
      setOutput(response);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setIsExecuting(false);
    }
  };

  const renderParameterInput = (param: Parameter) => {
    const value = formValues[param.name] ?? '';
    
    switch (param.type) {
      case 'string':
        return (
          <input
            type="text"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            value={value}
            onChange={(e) => handleFormChange(param.name, e.target.value)}
            placeholder={param.description}
          />
        );
      case 'number':
        return (
          <input
            type="number"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            value={value}
            onChange={(e) => handleFormChange(param.name, Number(e.target.value))}
            placeholder={param.description}
          />
        );
      case 'boolean':
        return (
          <div className="flex items-center h-10">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
              checked={!!value}
              onChange={(e) => handleFormChange(param.name, e.target.checked)}
            />
          </div>
        );
      case 'array':
        return (
          <textarea
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            rows={3}
            value={Array.isArray(value) ? value.join('\n') : ''}
            onChange={(e) => handleFormChange(param.name, e.target.value.split('\n').filter(Boolean))}
            placeholder="Enter one item per line"
          />
        );
      case 'object':
        return (
          <textarea
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm font-mono text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            rows={3}
            value={typeof value === 'object' ? JSON.stringify(value, null, 2) : ''}
            onChange={(e) => {
              try {
                handleFormChange(param.name, JSON.parse(e.target.value));
              } catch (e) {
                // Invalid JSON, don't update
              }
            }}
            placeholder='{ "key": "value" }'
          />
        );
      default:
        return (
          <input
            type="text"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            value={value}
            onChange={(e) => handleFormChange(param.name, e.target.value)}
            placeholder={param.description}
          />
        );
    }
  };

  if (!tool) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div className="absolute inset-0 bg-black bg-opacity-50" onClick={onClose}></div>
      
      <div className="absolute inset-y-0 right-0 max-w-full flex">
        <div className="relative w-screen max-w-4xl">
          <div className="h-full flex flex-col bg-white dark:bg-gray-800 shadow-xl">
            {/* Header */}
            <div className="flex-1 flex flex-col overflow-hidden">
              <div className="px-4 py-6 bg-gray-50 dark:bg-gray-900 sm:px-6">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-lg font-medium text-gray-900 dark:text-white">
                      {tool.name}
                    </h2>
                    <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                      {tool.description}
                    </p>
                  </div>
                  <div className="ml-3 h-7 flex items-center">
                    <button
                      type="button"
                      className="rounded-md text-gray-400 hover:text-gray-500 focus:outline-none"
                      onClick={onClose}
                    >
                      <span className="sr-only">Close panel</span>
                      <svg
                        className="h-6 w-6"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          d="M6 18L18 6M6 6l12 12"
                        />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>

              {/* Tabs */}
              <div className="border-b border-gray-200 dark:border-gray-700">
                <nav className="flex -mb-px">
                  <button
                    className={`py-4 px-6 text-sm font-medium border-b-2 ${
                      activeTab === 'form'
                        ? 'border-blue-500 text-blue-600 dark:text-blue-400 dark:border-blue-400'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-200'
                    }`}
                    onClick={() => setActiveTab('form')}
                  >
                    <div className="flex items-center">
                      <EyeIcon className="w-4 h-4 mr-2" />
                      Form
                    </div>
                  </button>
                  <button
                    className={`py-4 px-6 text-sm font-medium border-b-2 ${
                      activeTab === 'json'
                        ? 'border-blue-500 text-blue-600 dark:text-blue-400 dark:border-blue-400'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-200'
                    }`}
                    onClick={() => setActiveTab('json')}
                  >
                    <div className="flex items-center">
                      <CodeIcon className="w-4 h-4 mr-2" />
                      JSON
                    </div>
                  </button>
                </nav>
              </div>

              {/* Main content */}
              <div className="flex-1 overflow-y-auto">
                <div className="p-6">
                  {activeTab === 'form' ? (
                    <div className="space-y-6">
                      {tool.parameters?.map((param) => (
                        <div key={param.name}>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                            {param.name}
                            {param.required && <span className="text-red-500">*</span>}
                            {param.description && (
                              <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
                                {param.description}
                              </span>
                            )}
                          </label>
                          <div className="mt-1">
                            {renderParameterInput(param)}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="h-96">
                      <textarea
                        className="w-full h-full p-3 font-mono text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                        value={jsonInput}
                        onChange={(e) => handleJsonChange(e.target.value)}
                        spellCheck={false}
                      />
                    </div>
                  )}
                </div>
              </div>

              {/* Output panel */}
              <div className="border-t border-gray-200 dark:border-gray-700">
                <div className="px-6 py-4 bg-gray-50 dark:bg-gray-800">
                  <h3 className="text-sm font-medium text-gray-900 dark:text-white flex items-center">
                    <CpuChipIcon className="w-4 h-4 mr-2" />
                    Output
                    {executionTime !== null && (
                      <span className="ml-2 text-xs text-gray-500 dark:text-gray-400 flex items-center">
                        <ClockIcon className="w-3 h-3 mr-1" />
                        {executionTime}ms
                      </span>
                    )}
                  </h3>
                </div>
                <div className="p-6">
                  {error ? (
                    <div className="p-4 text-sm text-red-700 bg-red-100 rounded-md dark:bg-red-200 dark:text-red-800">
                      <div className="font-medium">Error</div>
                      <div className="mt-1">{error}</div>
                    </div>
                  ) : output ? (
                    <div 
                      ref={outputRef}
                      className="p-4 text-sm bg-gray-50 dark:bg-gray-700 rounded-md overflow-auto max-h-64 font-mono text-xs"
                    >
                      <pre className="whitespace-pre-wrap">
                        {JSON.stringify(output, null, 2)}
                      </pre>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500 dark:text-gray-400 text-sm">
                      Execute the tool to see the output here
                    </div>
                  )}
                </div>
              </div>

              {/* Footer */}
              <div className="flex-shrink-0 px-4 py-4 flex justify-end space-x-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
                <button
                  type="button"
                  className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:hover:bg-gray-600"
                  onClick={onClose}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                  onClick={executeTool}
                  disabled={isExecuting}
                >
                  {isExecuting ? (
                    <>
                      <StopIcon className="w-4 h-4 mr-2 animate-pulse" />
                      Executing...
                    </>
                  ) : (
                    <>
                      <PlayIcon className="w-4 h-4 mr-2" />
                      Execute
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestingConsole;
