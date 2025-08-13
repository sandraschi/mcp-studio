import React, { useState, useEffect } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XIcon } from '@heroicons/react/outline';

interface Parameter {
  name: string;
  type: string;
  description?: string;
  required?: boolean;
  default?: any;
}

interface PromptTemplate {
  id?: string;
  name: string;
  description?: string;
  template: string;
  parameters: Parameter[];
  metadata?: Record<string, any>;
}

interface PromptTemplateEditorProps {
  isOpen: boolean;
  onClose: () => void;
  template?: PromptTemplate | null;
  onSave: (template: PromptTemplate) => Promise<void>;
  isSaving: boolean;
}

export const PromptTemplateEditor: React.FC<PromptTemplateEditorProps> = ({
  isOpen,
  onClose,
  template,
  onSave,
  isSaving,
}) => {
  const [formData, setFormData] = useState<Omit<PromptTemplate, 'id'>>({
    name: '',
    description: '',
    template: '',
    parameters: [],
    metadata: {},
  });
  const [newParam, setNewParam] = useState<Omit<Parameter, 'name'>>({
    type: 'string',
    description: '',
    required: false,
  });
  const [paramName, setParamName] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Initialize form with template data when it changes
  useEffect(() => {
    if (template) {
      setFormData({
        name: template.name,
        description: template.description || '',
        template: template.template,
        parameters: [...template.parameters],
        metadata: { ...(template.metadata || {}) },
      });
    } else {
      setFormData({
        name: '',
        description: '',
        template: '',
        parameters: [],
        metadata: {},
      });
    }
    setParamName('');
    setNewParam({
      type: 'string',
      description: '',
      required: false,
    });
    setErrors({});
  }, [template, isOpen]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    
    // Clear error when field is edited
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const handleAddParameter = () => {
    if (!paramName.trim()) {
      setErrors(prev => ({
        ...prev,
        paramName: 'Parameter name is required',
      }));
      return;
    }

    // Check if parameter already exists
    if (formData.parameters.some(p => p.name === paramName)) {
      setErrors(prev => ({
        ...prev,
        paramName: 'Parameter with this name already exists',
      }));
      return;
    }

    setFormData(prev => ({
      ...prev,
      parameters: [
        ...prev.parameters,
        {
          name: paramName.trim(),
          ...newParam,
        },
      ],
    }));

    // Reset parameter form
    setParamName('');
    setNewParam({
      type: 'string',
      description: '',
      required: false,
    });
    setErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors.paramName;
      return newErrors;
    });
  };

  const removeParameter = (paramName: string) => {
    setFormData(prev => ({
      ...prev,
      parameters: prev.parameters.filter(p => p.name !== paramName),
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate form
    const newErrors: Record<string, string> = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }
    
    if (!formData.template.trim()) {
      newErrors.template = 'Template is required';
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    try {
      await onSave({
        ...formData,
        ...(template?.id && { id: template.id }),
      });
      onClose();
    } catch (error) {
      console.error('Error saving template:', error);
      setErrors({
        form: 'Failed to save template. Please try again.',
      });
    }
  };

  return (
    <Transition.Root show={isOpen} as={React.Fragment}>
      <Dialog
        as="div"
        className="fixed inset-0 z-10 overflow-y-auto"
        onClose={onClose}
      >
        <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
          <Transition.Child
            as={React.Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <Dialog.Overlay className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
          </Transition.Child>

          {/* This element is to trick the browser into centering the modal contents. */}
          <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">
            &#8203;
          </span>
          
          <Transition.Child
            as={React.Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            enterTo="opacity-100 translate-y-0 sm:scale-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100 translate-y-0 sm:scale-100"
            leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
          >
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full sm:p-6">
              <div className="hidden sm:block absolute top-0 right-0 pt-4 pr-4">
                <button
                  type="button"
                  className="bg-white rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  onClick={onClose}
                >
                  <span className="sr-only">Close</span>
                  <XIcon className="h-6 w-6" aria-hidden="true" />
                </button>
              </div>
              
              <div className="sm:flex sm:items-start">
                <div className="mt-3 text-center sm:mt-0 sm:text-left w-full">
                  <Dialog.Title as="h3" className="text-lg leading-6 font-medium text-gray-900">
                    {template?.id ? 'Edit Prompt Template' : 'Create New Prompt Template'}
                  </Dialog.Title>
                  
                  {errors.form && (
                    <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-md">
                      {errors.form}
                    </div>
                  )}
                  
                  <form onSubmit={handleSubmit} className="mt-6 space-y-6">
                    <div>
                      <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                        Template Name *
                      </label>
                      <div className="mt-1">
                        <input
                          type="text"
                          name="name"
                          id="name"
                          className={`shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border ${
                            errors.name ? 'border-red-300' : 'border-gray-300'
                          } rounded-md`}
                          value={formData.name}
                          onChange={handleInputChange}
                        />
                        {errors.name && (
                          <p className="mt-1 text-sm text-red-600">{errors.name}</p>
                        )}
                      </div>
                    </div>
                    
                    <div>
                      <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                        Description
                      </label>
                      <div className="mt-1">
                        <input
                          type="text"
                          name="description"
                          id="description"
                          className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border border-gray-300 rounded-md"
                          value={formData.description}
                          onChange={handleInputChange}
                        />
                      </div>
                    </div>
                    
                    <div>
                      <label htmlFor="template" className="block text-sm font-medium text-gray-700">
                        Template *
                      </label>
                      <div className="mt-1">
                        <textarea
                          id="template"
                          name="template"
                          rows={8}
                          className={`shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border ${
                            errors.template ? 'border-red-300' : 'border-gray-300'
                          } rounded-md`}
                          value={formData.template}
                          onChange={handleInputChange}
                          placeholder="Enter your prompt template here. Use {{parameter}} for variables."
                        />
                        {errors.template && (
                          <p className="mt-1 text-sm text-red-600">{errors.template}</p>
                        )}
                        <p className="mt-2 text-sm text-gray-500">
                          Use <code className="bg-gray-100 px-1 rounded">{'{{parameter}}'}</code> to insert parameters.
                        </p>
                      </div>
                    </div>
                    
                    <div>
                      <div className="flex justify-between items-center">
                        <h4 className="text-sm font-medium text-gray-700">Parameters</h4>
                      </div>
                      
                      {formData.parameters.length > 0 ? (
                        <div className="mt-2 overflow-hidden border border-gray-200 rounded-md">
                          <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                              <tr>
                                <th scope="col" className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Name
                                </th>
                                <th scope="col" className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Type
                                </th>
                                <th scope="col" className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Required
                                </th>
                                <th scope="col" className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Description
                                </th>
                                <th scope="col" className="relative px-4 py-2">
                                  <span className="sr-only">Actions</span>
                                </th>
                              </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                              {formData.parameters.map((param) => (
                                <tr key={param.name}>
                                  <td className="px-4 py-2 whitespace-nowrap text-sm font-medium text-gray-900">
                                    {param.name}
                                  </td>
                                  <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">
                                    {param.type}
                                  </td>
                                  <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">
                                    {param.required ? 'Yes' : 'No'}
                                  </td>
                                  <td className="px-4 py-2 text-sm text-gray-500">
                                    {param.description || '-'}
                                  </td>
                                  <td className="px-4 py-2 whitespace-nowrap text-right text-sm font-medium">
                                    <button
                                      type="button"
                                      className="text-red-600 hover:text-red-900"
                                      onClick={() => removeParameter(param.name)}
                                    >
                                      Remove
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <div className="mt-2 text-center py-4 text-sm text-gray-500 border-2 border-gray-300 border-dashed rounded-md">
                          No parameters added yet.
                        </div>
                      )}
                      
                      <div className="mt-4 border-t border-gray-200 pt-4">
                        <h5 className="text-sm font-medium text-gray-700 mb-3">Add New Parameter</h5>
                        
                        <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
                          <div className="md:col-span-3">
                            <label htmlFor="paramName" className="block text-xs font-medium text-gray-700">
                              Name *
                            </label>
                            <input
                              type="text"
                              id="paramName"
                              className={`mt-1 block w-full rounded-md ${
                                errors.paramName ? 'border-red-300' : 'border-gray-300'
                              } shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm`}
                              value={paramName}
                              onChange={(e) => setParamName(e.target.value)}
                              placeholder="param_name"
                            />
                            {errors.paramName && (
                              <p className="mt-1 text-xs text-red-600">{errors.paramName}</p>
                            )}
                          </div>
                          
                          <div className="md:col-span-2">
                            <label htmlFor="paramType" className="block text-xs font-medium text-gray-700">
                              Type
                            </label>
                            <select
                              id="paramType"
                              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                              value={newParam.type}
                              onChange={(e) =>
                                setNewParam((prev) => ({
                                  ...prev,
                                  type: e.target.value,
                                }))
                              }
                            >
                              <option value="string">String</option>
                              <option value="number">Number</option>
                              <option value="boolean">Boolean</option>
                              <option value="array">Array</option>
                              <option value="object">Object</option>
                            </select>
                          </div>
                          
                          <div className="md:col-span-5">
                            <label htmlFor="paramDescription" className="block text-xs font-medium text-gray-700">
                              Description
                            </label>
                            <input
                              type="text"
                              id="paramDescription"
                              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                              value={newParam.description || ''}
                              onChange={(e) =>
                                setNewParam((prev) => ({
                                  ...prev,
                                  description: e.target.value,
                                }))
                              }
                              placeholder="Parameter description"
                            />
                          </div>
                          
                          <div className="md:col-span-2 flex items-end">
                            <div className="flex items-center h-10">
                              <div className="flex items-center">
                                <input
                                  id="paramRequired"
                                  type="checkbox"
                                  className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                  checked={newParam.required || false}
                                  onChange={(e) =>
                                    setNewParam((prev) => ({
                                      ...prev,
                                      required: e.target.checked,
                                    }))
                                  }
                                />
                                <label htmlFor="paramRequired" className="ml-2 block text-sm text-gray-700">
                                  Required
                                </label>
                              </div>
                              
                              <button
                                type="button"
                                onClick={handleAddParameter}
                                className="ml-4 inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                              >
                                Add
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="mt-8 flex justify-end space-x-3">
                      <button
                        type="button"
                        className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                        onClick={onClose}
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={isSaving}
                        className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isSaving ? 'Saving...' : 'Save Template'}
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            </div>
          </Transition.Child>
        </div>
      </Dialog>
    </Transition.Root>
  );
};
