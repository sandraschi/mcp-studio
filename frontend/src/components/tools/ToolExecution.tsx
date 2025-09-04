import React, { useState, useRef, useEffect } from 'react';
import { Tool, ToolExecutionEvent } from '../../types';
import { classNames } from '../../utils/classNames';

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

  // Initialize parameters with default values
  useEffect(() => {
    const initialParams: Record<string, any> = {};
    tool.parameters?.forEach(param => {
      if (param.default !== undefined) {
        initialParams[param.name] = param.default;
      }
    });
    setParameters(initialParams);
    setJsonInput(JSON.stringify(initialParams, null, 2));
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

  const handleExecute = async () => {
    if (!tool) return;
    
    let paramsToUse = { ...parameters };
    const startTime = Date.now();
    
    // If in JSON mode, parse the JSON input
    if (activeTab === 'json') {
      try {
        paramsToUse = JSON.parse(jsonInput);
      } catch (e) {
        alert('Invalid JSON input');
        return;
      }
    }
    
    setIsExecuting(true);
    setExecutionResult(null);
    
    try {
      const result = await onExecute(tool.id, paramsToUse);
      const executionTime = Date.now() - startTime;
      
      setExecutionResult({
        ...result,
        toolId: tool.id,
        parameters: paramsToUse,
        executionTime,
        // For backward compatibility
        data: result.output
      });
      
      // Scroll to result
      setTimeout(() => {
        resultRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (error) {
      console.error('Execution failed:', error);
      const executionTime = Date.now() - startTime;
      
      setExecutionResult({
        success: false,
        error: error instanceof Error ? error.message : 'Execution failed',
        details: error instanceof Error ? error.stack : undefined,
        toolId: tool.id,
        parameters: paramsToUse,
        executionTime
      });
    } finally {
      setIsExecuting(false);
    }
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
          <h3 className="text-lg font-medium leading-6 text-gray-900 dark:text-white">
            {executionResult.success ? 'Execution Result' : 'Execution Failed'}
          </h3>
          <div className="flex items-center space-x-4">
            {executionTime && (
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {executionTime}
              </span>
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
          <h3 className="text-lg font-medium leading-6 text-gray-900 dark:text-white">
            {tool.name}
          </h3>
          {tool.description && (
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {tool.description}
            </p>
          )}
          
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
      
      {renderExecutionResult()}
    </div>
  );
};
