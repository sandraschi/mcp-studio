import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeftIcon,
  PlayIcon,
  CodeBracketIcon,
  DocumentTextIcon,
  InformationCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { useServers, useToaster } from '../hooks';
import { Button, Card, Tabs, Tab, Badge, Input, Label, Textarea, Select } from '../components/ui';

export const ToolExecution: React.FC = () => {
  const { serverId, toolName } = useParams<{ serverId: string; toolName: string }>();
  const navigate = useNavigate();
  const { getServer, executeTool } = useServers();
  const { success, error } = useToaster();
  const [activeTab, setActiveTab] = useState('form');
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [formValues, setFormValues] = useState<Record<string, any>>({});
  const [rawInput, setRawInput] = useState('{}');
  const [validationError, setValidationError] = useState<string | null>(null);

  const server = getServer(serverId || '');
  const tool = server?.tools?.find(t => t.name === toolName);

  // Initialize form values based on tool parameters
  useEffect(() => {
    if (tool?.parameters) {
      const initialValues: Record<string, any> = {};
      tool.parameters.forEach(param => {
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
      setRawInput(JSON.stringify(initialValues, null, 2));
    }
  }, [tool]);

  const handleFormChange = (name: string, value: any) => {
    setFormValues(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleRawInputChange = (value: string) => {
    setRawInput(value);
    try {
      const parsed = JSON.parse(value);
      setFormValues(parsed);
      setValidationError(null);
    } catch (err) {
      setValidationError('Invalid JSON');
    }
  };

  const handleExecute = async () => {
    if (!serverId || !toolName) return;
    
    try {
      setIsExecuting(true);
      setExecutionResult(null);
      
      // Parse parameters based on current tab
      let params = {};
      if (activeTab === 'form') {
        params = { ...formValues };
      } else {
        try {
          params = JSON.parse(rawInput);
        } catch (err) {
          setValidationError('Invalid JSON in raw input');
          return;
        }
      }

      // Execute the tool
      const result = await executeTool(serverId, toolName, params);
      setExecutionResult(result);
      success('Tool executed successfully');
    } catch (err) {
      console.error('Error executing tool:', err);
      error(`Failed to execute tool: ${err.message || 'Unknown error'}`);
    } finally {
      setIsExecuting(false);
    }
  };

  if (!server || !tool) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <InformationCircleIcon className="h-12 w-12 text-yellow-500 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          {!server ? 'Server not found' : 'Tool not found'}
        </h3>
        <p className="text-gray-500 dark:text-gray-400 mb-6">
          {!server ? 'The requested server could not be found.' : 'The requested tool is not available on this server.'}
        </p>
        <Button onClick={() => navigate('/')}>
          <ArrowLeftIcon className="h-4 w-4 mr-2" />
          Back to Dashboard
        </Button>
      </div>
    );
  }

  const renderParameterInput = (param: any) => {
    const { name, type, description, required, enum: enumValues } = param;
    const value = formValues[name] ?? '';
    const id = `param-${name}`;

    const commonProps = {
      id,
      name,
      value: value || '',
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => 
        handleFormChange(name, e.target.value),
      required,
      className: 'mt-1 block w-full',
    };

    switch (type) {
      case 'boolean':
        return (
          <div className="flex items-center">
            <input
              type="checkbox"
              id={id}
              name={name}
              checked={!!value}
              onChange={(e) => handleFormChange(name, e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor={id} className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
              {name}
            </label>
          </div>
        );
      case 'number':
        return <Input type="number" {...commonProps} />;
      case 'string':
        if (enumValues && enumValues.length > 0) {
          return (
            <Select {...commonProps}>
              {!required && <option value="">-- Select an option --</option>}
              {enumValues.map((val: string) => (
                <option key={val} value={val}>
                  {val}
                </option>
              ))}
            </Select>
          );
        }
        return <Input type="text" {...commonProps} />;
      case 'text':
        return <Textarea {...commonProps} rows={4} />;
      case 'array':
      case 'object':
        return (
          <Textarea
            {...commonProps}
            rows={4}
            value={JSON.stringify(value, null, 2)}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                handleFormChange(name, parsed);
              } catch (err) {
                // Keep the invalid JSON for editing
                handleFormChange(name, e.target.value);
              }
            }}
            className="font-mono text-sm"
          />
        );
      default:
        return <Input type="text" {...commonProps} />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="mr-4">
          <ArrowLeftIcon className="h-5 w-5" />
        </Button>
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            {tool.name}
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {server.name} • {tool.description || 'No description available'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card>
            <Tabs value={activeTab} onChange={setActiveTab}>
              <Tab value="form" icon={<DocumentTextIcon className="h-5 w-5" />}>
                Form
              </Tab>
              <Tab value="raw" icon={<CodeBracketIcon className="h-5 w-5" />}>
                Raw JSON
              </Tab>
            </Tabs>

            <div className="mt-6">
              {activeTab === 'form' ? (
                <div className="space-y-6">
                  {tool.parameters && tool.parameters.length > 0 ? (
                    tool.parameters.map((param) => (
                      <div key={param.name}>
                        <Label htmlFor={`param-${param.name}`}>
                          {param.name}
                          {param.required && <span className="text-red-500 ml-1">*</span>}
                        </Label>
                        <div className="mt-1">
                          {renderParameterInput(param)}
                        </div>
                        {param.description && (
                          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                            {param.description}
                          </p>
                        )}
                        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                          Type: {param.type}
                          {param.default !== undefined && ` • Default: ${JSON.stringify(param.default)}`}
                        </p>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8">
                      <InformationCircleIcon className="mx-auto h-12 w-12 text-gray-400" />
                      <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No parameters required</h3>
                      <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                        This tool doesn't require any parameters to execute.
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  <Label>Parameters (JSON)</Label>
                  <Textarea
                    value={rawInput}
                    onChange={(e) => handleRawInputChange(e.target.value)}
                    className="font-mono text-sm h-64"
                    placeholder="Enter JSON parameters..."
                  />
                  {validationError && (
                    <p className="mt-1 text-sm text-red-600 dark:text-red-400">{validationError}</p>
                  )}
                </div>
              )}

              <div className="mt-6 flex justify-end">
                <Button 
                  onClick={handleExecute}
                  disabled={isExecuting || (activeTab === 'raw' && validationError !== null)}
                  className="w-full sm:w-auto"
                >
                  {isExecuting ? (
                    <>
                      <ArrowPathIcon className="animate-spin -ml-1 mr-2 h-4 w-4" />
                      Executing...
                    </>
                  ) : (
                    <>
                      <PlayIcon className="-ml-1 mr-2 h-4 w-4" />
                      Execute
                    </>
                  )}
                </Button>
              </div>
            </div>
          </Card>
        </div>

        <div>
          <Card>
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">Execution Result</h3>
              {executionResult && (
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => {
                    try {
                      navigator.clipboard.writeText(JSON.stringify(executionResult, null, 2));
                      success('Result copied to clipboard');
                    } catch (err) {
                      console.error('Failed to copy:', err);
                      error('Failed to copy result');
                    }
                  }}
                >
                  Copy
                </Button>
              )}
            </div>
            
            <div className="mt-4">
              {executionResult === null ? (
                <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                  <CodeBracketIcon className="mx-auto h-12 w-12" />
                  <p className="mt-2">No execution results yet.</p>
                  <p className="text-sm">Execute the tool to see the results here.</p>
                </div>
              ) : (
                <pre className="bg-gray-50 dark:bg-gray-800 p-4 rounded-md overflow-auto max-h-96 text-xs">
                  {typeof executionResult === 'string' 
                    ? executionResult 
                    : JSON.stringify(executionResult, null, 2)}
                </pre>
              )}
            </div>
          </Card>

          {/* Tool documentation */}
          <Card className="mt-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Documentation</h3>
            <div className="prose dark:prose-invert max-w-none">
              <h4 className="text-base font-medium">{tool.name}</h4>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                {tool.description || 'No description available.'}
              </p>

              {tool.parameters && tool.parameters.length > 0 && (
                <div className="mt-4">
                  <h5 className="text-sm font-medium mb-2">Parameters</h5>
                  <div className="overflow-hidden border border-gray-200 dark:border-gray-700 rounded-lg">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                      <thead className="bg-gray-50 dark:bg-gray-800">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            Name
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            Type
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            Required
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            Default
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                        {tool.parameters.map((param) => (
                          <tr key={param.name}>
                            <td className="px-4 py-2 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                              {param.name}
                              {param.description && (
                                <p className="text-xs text-gray-500 dark:text-gray-400">{param.description}</p>
                              )}
                            </td>
                            <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                              {param.type}
                            </td>
                            <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                              {param.required ? 'Yes' : 'No'}
                            </td>
                            <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                              {param.default !== undefined ? 
                                (typeof param.default === 'string' 
                                  ? `"${param.default}"` 
                                  : JSON.stringify(param.default)) 
                                : '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
