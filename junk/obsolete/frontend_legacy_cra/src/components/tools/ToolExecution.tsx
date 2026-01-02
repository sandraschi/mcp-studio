import React, { useState, useRef, useEffect } from 'react';
import { Tool, ToolExecutionEvent } from '../../types';
import { classNames } from '../../utils/classNames';
import { api } from '../../services/api';
import './docstring-styles.css';

// Simple button component
const Button = ({ 
  children, 
  onClick, 
  disabled = false, 
  variant = 'primary',
  className = ''
}: {
  children: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
  variant?: 'primary' | 'secondary' | 'danger';
  className?: string;
}) => {
  const baseStyles = 'px-4 py-2 rounded-md font-medium focus:outline-none focus:ring-2 focus:ring-offset-2';
  const variantStyles = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
  };

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`${baseStyles} ${variantStyles[variant]} ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}
    >
      {children}
    </button>
  );
};

// Simple icons
const PlayIcon = ({ className = '' }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
  </svg>
);

const StopIcon = ({ className = '' }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clipRule="evenodd" />
  </svg>
);

const CopyIcon = ({ className = '' }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
    <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z" />
    <path d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z" />
  </svg>
);

const CheckIcon = ({ className = '' }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
  </svg>
);

const RefreshIcon = ({ className = '' }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
    <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
  </svg>
);

const HistoryIcon = ({ className = '' }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
  </svg>
);

const ConnectionStatusIcon = ({ status, className = '' }: { status: string; className?: string }) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'connected':
        return <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>;
      case 'disconnected':
        return <div className="w-2 h-2 bg-red-500 rounded-full"></div>;
      case 'error':
        return <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>;
      default:
        return <div className="w-2 h-2 bg-gray-400 rounded-full"></div>;
    }
  };

  return (
    <div className={`flex items-center space-x-1 ${className}`}>
      {getStatusIcon()}
      <span className="text-xs text-gray-500 dark:text-gray-400 capitalize">
        {status}
      </span>
    </div>
  );
};

const ProgressBar = ({ progress, message, className = '' }: {
  progress: number;
  message: string;
  className?: string;
}) => (
  <div className={`space-y-2 ${className}`}>
    <div className="flex items-center justify-between text-sm">
      <span className="text-gray-600 dark:text-gray-400">{message}</span>
      <span className="text-gray-500 dark:text-gray-500">{Math.round(progress)}%</span>
    </div>
    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
      <div
        className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
        style={{ width: `${progress}%` }}
      />
    </div>
  </div>
);

// Simple tabs component
const Tabs = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
  <div className={className}>{children}</div>
);

const TabList = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
  <div className={`flex border-b border-gray-200 ${className}`}>{children}</div>
);

const Tab = ({ 
  children, 
  isActive, 
  onClick,
  className = ''
}: { 
  children: React.ReactNode; 
  isActive: boolean; 
  onClick: () => void;
  className?: string;
}) => (
  <button
    type="button"
    onClick={onClick}
    className={`px-4 py-2 text-sm font-medium ${isActive 
      ? 'border-b-2 border-blue-500 text-blue-600' 
      : 'text-gray-500 hover:text-gray-700'} ${className}`}
  >
    {children}
  </button>
);

const TabPanel = ({ 
  children, 
  isActive,
  className = ''
}: { 
  children: React.ReactNode; 
  isActive: boolean;
  className?: string;
}) => (
  <div className={`${isActive ? 'block' : 'hidden'} p-4 ${className}`}>
    {children}
  </div>
);

// Simple JSON formatter
const formatJson = (json: any, indent: number = 2): string => {
  try {
    return JSON.stringify(json, null, indent);
  } catch (e) {
    return String(json);
  }
};

interface ToolExecutionResult {
  success: boolean;
  output?: any;
  error?: string;
  details?: string;
  toolId: string;
  parameters: Record<string, any>;
  executionTime?: number;
  data?: any; // For backward compatibility
}

interface ToolExecutionProps {
  tool: Tool | null;
  serverId: string;
  onExecute: (toolId: string, parameters: Record<string, any>) => Promise<ToolExecutionResult>;
  className?: string;
}

export const ToolExecution: React.FC<ToolExecutionProps> = ({
  tool,
  serverId,
  onExecute,
  className = '',
}) => {
  // Handle case where tool is null
  if (!tool) {
    return (
      <div className="p-4 text-center text-gray-500 dark:text-gray-400">
        <p>No tool selected or tool not found.</p>
      </div>
    );
  }

  const [parameters, setParameters] = useState<Record<string, any>>({});
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<ToolExecutionResult | null>(null);
  const [activeTab, setActiveTab] = useState<'form' | 'json'>('form');
  const [formattedDocstring, setFormattedDocstring] = useState<{
    html?: string;
    markdown?: string;
    parsed?: Record<string, any>;
  } | null>(null);
  const [isLoadingDocstring, setIsLoadingDocstring] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'unknown' | 'connected' | 'disconnected' | 'error'>('unknown');
  const [retryCount, setRetryCount] = useState(0);
  const [isRetrying, setIsRetrying] = useState(false);
  const [executionProgress, setExecutionProgress] = useState<{
    show: boolean;
    message: string;
    progress: number;
  }>({ show: false, message: '', progress: 0 });
  const [executionHistory, setExecutionHistory] = useState<ToolExecutionResult[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  // Update JSON input when parameters change
  useEffect(() => {
    if (activeTab === 'json' && tool?.parameters) {
      setJsonInput(JSON.stringify(parameters, null, 2));
    }
  }, [activeTab, parameters, tool?.parameters]);
  const [jsonInput, setJsonInput] = useState('{}');
  const [copied, setCopied] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);
  const resultRef = useRef<HTMLDivElement>(null);

  // Load execution history from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(`tool-execution-history-${tool?.id}`);
    if (stored) {
      try {
        const history = JSON.parse(stored);
        setExecutionHistory(history.slice(0, 10)); // Keep only last 10 executions
      } catch (error) {
        console.warn('Failed to load execution history:', error);
      }
    }
  }, [tool?.id]);

  // Save execution history to localStorage
  const saveToHistory = (result: ToolExecutionResult) => {
    const newHistory = [result, ...executionHistory].slice(0, 10);
    setExecutionHistory(newHistory);
    localStorage.setItem(`tool-execution-history-${tool?.id}`, JSON.stringify(newHistory));
  };

  // Clear execution history
  const clearHistory = () => {
    setExecutionHistory([]);
    localStorage.removeItem(`tool-execution-history-${tool?.id}`);
  };

  // Initialize parameters with default values and fetch formatted docstring
  useEffect(() => {
    const initialParams: Record<string, any> = {};
    tool.parameters?.forEach(param => {
      if (param.default !== undefined) {
        initialParams[param.name] = param.default;
      }
    });
    setParameters(initialParams);
    setJsonInput(JSON.stringify(initialParams, null, 2));

    // Fetch formatted docstring if available
    if (tool.description) {
      setIsLoadingDocstring(true);
      api.formatDocstring(tool.description, 'html')
        .then((response) => {
          if (response.data) {
            setFormattedDocstring({
              html: response.data.formatted,
              parsed: response.data.parsed,
            });
          }
        })
        .catch((error) => {
          console.warn('Failed to format docstring:', error);
        })
        .finally(() => {
          setIsLoadingDocstring(false);
        });
    }

    // Check initial connection status
    checkConnection();
  }, [tool]);

  const handleParameterChange = (name: string, value: any) => {
    setParameters(prev => ({
      ...prev,
      [name]: value,
    }));

    // Update JSON input when form changes
    if (activeTab === 'form') {
      const newParams = { ...parameters, [name]: value };
      setJsonInput(JSON.stringify(newParams, null, 2));
    }
  };

  const handleJsonChange = (value: string) => {
    setJsonInput(value);
    
    // Try to update form fields when JSON changes
    try {
      const parsed = JSON.parse(value);
      setParameters(parsed);
    } catch (e) {
      // Invalid JSON, don't update parameters
    }
  };

  const handleFormatJson = () => {
    try {
      const parsed = JSON.parse(jsonInput);
      setJsonInput(JSON.stringify(parsed, null, 2));
    } catch (e) {
      alert('Invalid JSON');
    }
  };

  const checkConnection = async () => {
    try {
      setConnectionStatus('unknown');
      // Try to execute a simple tool or check server health
      // For now, we'll assume connection is good if we get here
      setConnectionStatus('connected');
    } catch (error) {
      setConnectionStatus('error');
    }
  };

  const handleExecute = async (isRetry = false) => {
    if (!tool) return;

    let paramsToUse = { ...parameters };
    const startTime = Date.now();

    // If in JSON mode, parse the JSON input
    if (activeTab === 'json') {
      try {
        paramsToUse = JSON.parse(jsonInput);
      } catch (e) {
        setExecutionResult({
          success: false,
          error: 'Invalid JSON input: Please check your JSON syntax',
          toolId: tool.id,
          parameters: paramsToUse,
          executionTime: 0
        });
        return;
      }
    }

    setIsExecuting(true);
    setExecutionResult(null);
    setExecutionProgress({ show: false, message: '', progress: 0 });

    if (!isRetry) {
      setRetryCount(0);
    }

    // Show progress indicator after 2 seconds for long-running operations
    const progressTimeout = setTimeout(() => {
      setExecutionProgress({
        show: true,
        message: 'Executing tool...',
        progress: 0
      });

      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setExecutionProgress(prev => ({
          ...prev,
          progress: Math.min(prev.progress + Math.random() * 10, 90)
        }));
      }, 500);

      // Clean up interval when execution completes
      const cleanup = () => {
        clearInterval(progressInterval);
        setExecutionProgress({ show: false, message: '', progress: 0 });
      };

      // Store cleanup function for later use
      (window as any).progressCleanup = cleanup;
    }, 2000);

    try {
      const result = await onExecute(tool.id, paramsToUse);
      const executionTime = Date.now() - startTime;

      // Clean up progress indicators
      clearTimeout(progressTimeout);
      if ((window as any).progressCleanup) {
        (window as any).progressCleanup();
      }

      const executionResultData = {
        ...result,
        toolId: tool.id,
        parameters: paramsToUse,
        executionTime,
        // For backward compatibility
        data: result.output
      };

      setExecutionResult(executionResultData);
      saveToHistory(executionResultData);

      setConnectionStatus('connected');
      setRetryCount(0);

      // Scroll to result
      setTimeout(() => {
        resultRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (error) {
      console.error('Execution failed:', error);
      const executionTime = Date.now() - startTime;

      // Clean up progress indicators
      clearTimeout(progressTimeout);
      if ((window as any).progressCleanup) {
        (window as any).progressCleanup();
      }

      let errorMessage = 'Execution failed';
      let errorDetails = undefined;
      let connectionLost = false;

      if (error instanceof Error) {
        errorMessage = error.message;

        // Check for common connection issues
        if (error.message.includes('timeout') || error.message.includes('network')) {
          errorMessage = 'Connection timeout - The server may be busy or unreachable';
          connectionLost = true;
        } else if (error.message.includes('404')) {
          errorMessage = 'Tool not found - The tool may have been removed or renamed';
        } else if (error.message.includes('500')) {
          errorMessage = 'Server error - There was an internal server issue';
        } else if (error.message.includes('403')) {
          errorMessage = 'Access denied - You may not have permission to execute this tool';
        }

        errorDetails = error.stack;
      }

      if (connectionLost) {
        setConnectionStatus('disconnected');
      }

      setExecutionResult({
        success: false,
        error: errorMessage,
        details: errorDetails,
        toolId: tool.id,
        parameters: paramsToUse,
        executionTime
      });
    } finally {
      setIsExecuting(false);
      setIsRetrying(false);
    }
  };

  const handleRetry = async () => {
    if (isExecuting || !executionResult || executionResult.success) return;

    setIsRetrying(true);
    setRetryCount(prev => prev + 1);

    // Add a small delay before retry
    await new Promise(resolve => setTimeout(resolve, 1000));

    await handleExecute(true);
  };

  const handleCopy = () => {
    if (!executionResult) return;
    
    const resultString = JSON.stringify(
      executionResult.success 
        ? executionResult.output 
        : { error: executionResult.error, details: executionResult.details },
      null, 
      2
    );
    
    navigator.clipboard.writeText(resultString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const renderParameterInput = (param: any) => {
    const { name, type, description, required, enum: enumValues } = param;
    const value = parameters[name] ?? '';
    
    const commonProps = {
      id: `${tool.id}-${name}`,
      name,
      value: value || '',
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        handleParameterChange(name, e.target.value);
      },
      required,
      className: 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
    };

    switch (type) {
      case 'string':
        if (enumValues?.length) {
          return (
            <select
              {...commonProps}
              className={classNames(
                'mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md',
                'dark:bg-gray-700 dark:border-gray-600 dark:text-white'
              )}
            >
              {!value && <option value="">Select an option</option>}
              {enumValues.map((val: string) => (
                <option key={val} value={val}>
                  {val}
                </option>
              ))}
            </select>
          );
        }
        return param.multiline ? (
          <textarea
            {...commonProps}
            rows={4}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          />
        ) : (
          <input
            type="text"
            {...commonProps}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          />
        );
      
      case 'number':
        return (
          <input
            type="number"
            {...commonProps}
            step={param.step || 'any'}
            min={param.minimum}
            max={param.maximum}
          />
        );
        
      case 'boolean':
        return (
          <div className="flex items-center h-10">
            <input
              type="checkbox"
              id={commonProps.id}
              name={commonProps.name}
              checked={!!value}
              onChange={(e) => handleParameterChange(name, e.target.checked)}
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600"
            />
          </div>
        );
        
      case 'object':
      case 'array':
        return (
          <textarea
            {...commonProps}
            rows={4}
            value={JSON.stringify(value || (type === 'array' ? [] : {}), null, 2)}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                handleParameterChange(name, parsed);
              } catch (e) {
                // Invalid JSON, don't update
              }
            }}
            className="font-mono text-sm mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          />
        );
        
      default:
        return (
          <input
            type="text"
            {...commonProps}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          />
        );
    }
  };

  const tabs = [
    { id: 'form', name: 'Form' },
    { id: 'json', name: 'JSON' },
  ] as const;

  const renderExecutionResult = () => {
    if (!executionResult) return null;
    
    const result = executionResult.output || executionResult.data;
    const executionTime = executionResult.executionTime ? `in ${executionResult.executionTime}ms` : '';
    
    return (
      <div ref={resultRef} className="bg-white dark:bg-gray-800 shadow sm:rounded-lg overflow-hidden mt-4">
        <div className="px-4 py-5 sm:px-6 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <h3 className="text-lg font-medium leading-6 text-gray-900 dark:text-white">
              {executionResult.success ? 'Execution Result' : 'Execution Failed'}
            </h3>
            {!executionResult.success && retryCount > 0 && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
                Retry #{retryCount}
              </span>
            )}
          </div>
          <div className="flex items-center space-x-4">
            {executionTime && (
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {executionTime}
              </span>
            )}
            {!executionResult.success && (
              <Button
                variant="secondary"
                onClick={handleRetry}
                disabled={isRetrying || isExecuting}
                className="flex items-center space-x-2"
              >
                {isRetrying ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-gray-500"></div>
                    <span>Retrying...</span>
                  </>
                ) : (
                  <>
                    <RefreshIcon className="h-4 w-4" />
                    <span>Retry</span>
                  </>
                )}
              </Button>
            )}
            <Button
              variant="secondary"
              onClick={handleCopy}
              className="flex items-center space-x-2"
            >
              {copied ? (
                <>
                  <CheckIcon className="h-4 w-4" />
                  <span>Copied!</span>
                </>
              ) : (
                <>
                  <CopyIcon className="h-4 w-4" />
                  <span>Copy</span>
                </>
              )}
            </Button>
          </div>
        </div>
        <div className="px-4 py-5 sm:p-6 overflow-x-auto">
          {executionResult.success ? (
            <pre className="text-sm text-gray-900 dark:text-gray-100">
              <code>{formatJson(result)}</code>
            </pre>
          ) : (
            <div className="text-red-600 dark:text-red-400">
              <p className="font-medium">{executionResult.error}</p>
              {executionResult.details && (
                <pre className="mt-2 text-xs text-red-500 dark:text-red-300 overflow-auto">
                  {executionResult.details}
                </pre>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className={classNames('space-y-6', className)}>
      <div className="bg-white dark:bg-gray-800 shadow sm:rounded-lg overflow-hidden">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h3 className="text-lg font-medium leading-6 text-gray-900 dark:text-white">
                {tool.name}
              </h3>
              {isLoadingDocstring ? (
                <div className="mt-2 animate-pulse">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mt-1"></div>
                </div>
              ) : formattedDocstring?.html ? (
                <div
                  className="mt-2 prose prose-sm dark:prose-invert max-w-none docstring-formatted"
                  dangerouslySetInnerHTML={{ __html: formattedDocstring.html }}
                />
              ) : tool.description ? (
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  {tool.description}
                </p>
              ) : null}
            </div>
            <div className="ml-4 flex-shrink-0 flex items-center space-x-3">
              <ConnectionStatusIcon status={connectionStatus} />
              {executionHistory.length > 0 && (
                <button
                  onClick={() => setShowHistory(!showHistory)}
                  className={`p-1 rounded-md text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors ${
                    showHistory ? 'bg-gray-100 dark:bg-gray-700' : ''
                  }`}
                  title="Toggle execution history"
                >
                  <HistoryIcon className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>
          
          <Tabs>
            <TabList>
              {tabs.map((tab) => (
                <Tab 
                  key={tab.id} 
                  isActive={activeTab === tab.id}
                  onClick={() => setActiveTab(tab.id)}
                >
                  {tab.name}
                </Tab>
              ))}
            </TabList>
            
            <TabPanel isActive={activeTab === 'form'} className="mt-4">
              {tool.parameters && tool.parameters.length > 0 ? (
                <form onSubmit={(e) => { e.preventDefault(); handleExecute(); }}>
                  <div className="space-y-4">
                    {tool.parameters.map((param) => (
                      <div key={param.name} className="space-y-1">
                        <label
                          htmlFor={`${tool.id}-${param.name}`}
                          className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                        >
                          {param.name}
                          {param.required && (
                            <span className="text-red-500 ml-1">*</span>
                          )}
                        </label>
                        {param.description && (
                          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                            {param.description}
                          </p>
                        )}
                        {renderParameterInput(param)}
                      </div>
                    ))}
                  </div>
                  
                  <div className="mt-6 flex space-x-3">
                    <Button
                      onClick={handleExecute}
                      variant="primary"
                      disabled={isExecuting}
                      className="flex items-center space-x-2"
                    >
                      {isExecuting ? (
                        <>
                          <StopIcon className="h-4 w-4" />
                          <span>Executing...</span>
                        </>
                      ) : (
                        <>
                          <PlayIcon className="h-4 w-4" />
                          <span>Execute</span>
                        </>
                      )}
                    </Button>
                  </div>
                </form>
              ) : (
                <div className="text-gray-500 dark:text-gray-400">
                  No parameters required for this tool.
                </div>
              )}
            </TabPanel>
            
            <TabPanel isActive={activeTab === 'json'} className="mt-4">
              <div className="space-y-4">
                <div className="relative">
                  <textarea
                    className="w-full h-64 font-mono text-sm border border-gray-300 dark:border-gray-600 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                    value={jsonInput}
                    onChange={(e) => setJsonInput(e.target.value)}
                    placeholder="Enter JSON parameters..."
                    disabled={isExecuting}
                  />
                </div>
                
                <div className="flex space-x-3">
                  <Button
                    onClick={handleExecute}
                    variant="primary"
                    disabled={isExecuting}
                    className="flex items-center space-x-2"
                  >
                    {isExecuting ? (
                      <>
                        <StopIcon className="h-4 w-4" />
                        <span>Executing...</span>
                      </>
                    ) : (
                      <>
                        <PlayIcon className="h-4 w-4" />
                        <span>Execute</span>
                      </>
                    )}
                  </Button>
                  
                  <Button
                    variant="secondary"
                    onClick={handleFormatJson}
                    className="flex items-center space-x-2"
                  >
                    <CopyIcon className="h-4 w-4" />
                    <span>Format JSON</span>
                  </Button>
                </div>
              </div>
            </TabPanel>
          </Tabs>
        </div>
      </div>

      {/* Progress Indicator */}
      {executionProgress.show && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4 mx-4 sm:mx-6 mb-4">
          <ProgressBar
            progress={executionProgress.progress}
            message={executionProgress.message}
            className="w-full"
          />
        </div>
      )}

      {renderExecutionResult()}

      {/* Execution History */}
      {showHistory && executionHistory.length > 0 && (
        <div className="bg-white dark:bg-gray-800 shadow sm:rounded-lg overflow-hidden mt-4">
          <div className="px-4 py-5 sm:px-6 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
            <h3 className="text-lg font-medium leading-6 text-gray-900 dark:text-white">
              Execution History ({executionHistory.length})
            </h3>
            <Button
              variant="secondary"
              onClick={clearHistory}
              className="text-xs"
            >
              Clear History
            </Button>
          </div>
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {executionHistory.map((historyItem, index) => (
              <div key={index} className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${
                      historyItem.success ? 'bg-green-500' : 'bg-red-500'
                    }`} />
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      Execution #{executionHistory.length - index}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2 text-xs text-gray-500 dark:text-gray-400">
                    {historyItem.executionTime && (
                      <span>{historyItem.executionTime}ms</span>
                    )}
                    <span>{new Date().toLocaleTimeString()}</span>
                  </div>
                </div>
                {historyItem.success ? (
                  <div className="text-sm text-gray-700 dark:text-gray-300">
                    <div className="bg-gray-50 dark:bg-gray-700 p-2 rounded text-xs font-mono overflow-x-auto">
                      {formatJson(historyItem.output || historyItem.data)}
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-red-600 dark:text-red-400">
                    <p className="font-medium">{historyItem.error}</p>
                    {historyItem.details && (
                      <pre className="mt-1 text-xs text-red-500 dark:text-red-300 overflow-x-auto">
                        {historyItem.details}
                      </pre>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
