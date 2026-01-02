import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useToaster } from '../../hooks';
import { Button, Input, Label, Card } from '../../components/ui';
import { 
  UserIcon, 
  EnvelopeIcon, 
  LockClosedIcon, 
  ArrowPathIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';

export const Register: React.FC = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [errors, setErrors] = useState<{
    name?: string;
    email?: string;
    password?: string;
    confirmPassword?: string;
    general?: string;
  }>({});
  const [isLoading, setIsLoading] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState({
    hasMinLength: false,
    hasUppercase: false,
    hasNumber: false,
    hasSpecialChar: false,
  });
  const [touched, setTouched] = useState({
    name: false,
    email: false,
    password: false,
    confirmPassword: false,
  });

  const { register } = useAuth();
  const navigate = useNavigate();
  const { success, error } = useToaster();

  const validate = (field?: keyof typeof formData) => {
    const newErrors: typeof errors = {};
    let isValid = true;

    // Only validate all fields if no specific field is provided
    if (!field || field === 'name') {
      if (!formData.name.trim()) {
        newErrors.name = 'Name is required';
        isValid = false;
      } else if (formData.name.length < 2) {
        newErrors.name = 'Name must be at least 2 characters';
        isValid = false;
      }
    }

    if (!field || field === 'email') {
      if (!formData.email.trim()) {
        newErrors.email = 'Email is required';
        isValid = false;
      } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
        newErrors.email = 'Email is invalid';
        isValid = false;
      }
    }

    if (!field || field === 'password') {
      if (!formData.password) {
        newErrors.password = 'Password is required';
        isValid = false;
      } else {
        const hasMinLength = formData.password.length >= 8;
        const hasUppercase = /[A-Z]/.test(formData.password);
        const hasNumber = /[0-9]/.test(formData.password);
        const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(formData.password);

        setPasswordStrength({
          hasMinLength,
          hasUppercase,
          hasNumber,
          hasSpecialChar,
        });

        if (!hasMinLength || !hasUppercase || !hasNumber || !hasSpecialChar) {
          newErrors.password = 'Password does not meet requirements';
          isValid = false;
        }
      }
    }

    if (!field || field === 'confirmPassword') {
      if (formData.password !== formData.confirmPassword) {
        newErrors.confirmPassword = 'Passwords do not match';
        isValid = false;
      }
    }

    // Only update errors for the field being validated
    if (field) {
      setErrors(prev => ({
        ...prev,
        [field]: newErrors[field as keyof typeof newErrors],
      }));
    } else {
      setErrors(newErrors);
    }

    return isValid;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));

    // Validate the field being changed
    if (touched[name as keyof typeof touched]) {
      validate(name as keyof typeof formData);
    }
  };

  const handleBlur = (field: keyof typeof formData) => {
    setTouched(prev => ({
      ...prev,
      [field]: true,
    }));
    validate(field);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Mark all fields as touched
    const newTouched = Object.keys(touched).reduce((acc, key) => ({
      ...acc,
      [key]: true,
    }), {} as typeof touched);
    setTouched(newTouched);

    // Validate all fields
    const isValid = validate();
    
    if (!isValid) return;

    try {
      setIsLoading(true);
      await register({
        name: formData.name,
        email: formData.email,
        password: formData.password,
      });
      
      success('Account created successfully! Welcome to MCP Studio.');
      navigate('/');
    } catch (err) {
      console.error('Registration error:', err);
      setErrors({
        general: err instanceof Error ? err.message : 'Failed to create account. Please try again.'
      });
      error('Failed to create account');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900 dark:text-white">
            Create your account
          </h2>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            Or{' '}
            <Link 
              to="/login" 
              className="font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300"
            >
              sign in to your existing account
            </Link>
          </p>
        </div>

        <Card className="mt-8">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {errors.general && (
              <div className="rounded-md bg-red-50 dark:bg-red-900/30 p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <XCircleIcon className="h-5 w-5 text-red-400" />
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                      {errors.general}
                    </h3>
                  </div>
                </div>
              </div>
            )}
            
            <div>
              <Label htmlFor="name">Full Name</Label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <UserIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
                </div>
                <Input
                  id="name"
                  name="name"
                  type="text"
                  autoComplete="name"
                  required
                  value={formData.name}
                  onChange={handleChange}
                  onBlur={() => handleBlur('name')}
                  className={`pl-10 ${errors.name ? 'border-red-300' : ''}`}
                  placeholder="John Doe"
                />
              </div>
              {errors.name && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.name}</p>}
            </div>

            <div>
              <Label htmlFor="email">Email address</Label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <EnvelopeIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
                </div>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  onBlur={() => handleBlur('email')}
                  className={`pl-10 ${errors.email ? 'border-red-300' : ''}`}
                  placeholder="you@example.com"
                />
              </div>
              {errors.email && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.email}</p>}
            </div>

            <div>
              <Label htmlFor="password">Password</Label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <LockClosedIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
                </div>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={formData.password}
                  onChange={handleChange}
                  onBlur={() => handleBlur('password')}
                  className={`pl-10 ${errors.password ? 'border-red-300' : ''}`}
                  placeholder="••••••••"
                />
              </div>
              
              <div className="mt-2 space-y-1">
                <p className="text-xs text-gray-500 dark:text-gray-400">Password must contain:</p>
                <ul className="space-y-1">
                  <li className={`flex items-center text-xs ${passwordStrength.hasMinLength ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'}`}>
                    {passwordStrength.hasMinLength ? (
                      <CheckCircleIcon className="h-4 w-4 mr-1" />
                    ) : (
                      <XCircleIcon className="h-4 w-4 mr-1" />
                    )}
                    At least 8 characters
                  </li>
                  <li className={`flex items-center text-xs ${passwordStrength.hasUppercase ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'}`}>
                    {passwordStrength.hasUppercase ? (
                      <CheckCircleIcon className="h-4 w-4 mr-1" />
                    ) : (
                      <XCircleIcon className="h-4 w-4 mr-1" />
                    )}
                    At least one uppercase letter
                  </li>
                  <li className={`flex items-center text-xs ${passwordStrength.hasNumber ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'}`}>
                    {passwordStrength.hasNumber ? (
                      <CheckCircleIcon className="h-4 w-4 mr-1" />
                    ) : (
                      <XCircleIcon className="h-4 w-4 mr-1" />
                    )}
                    At least one number
                  </li>
                  <li className={`flex items-center text-xs ${passwordStrength.hasSpecialChar ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'}`}>
                    {passwordStrength.hasSpecialChar ? (
                      <CheckCircleIcon className="h-4 w-4 mr-1" />
                    ) : (
                      <XCircleIcon className="h-4 w-4 mr-1" />
                    )}
                    At least one special character
                  </li>
                </ul>
              </div>
              {errors.password && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.password}</p>}
            </div>

            <div>
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <LockClosedIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
                </div>
                <Input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  onBlur={() => handleBlur('confirmPassword')}
                  className={`pl-10 ${errors.confirmPassword ? 'border-red-300' : ''}`}
                  placeholder="••••••••"
                />
              </div>
              {errors.confirmPassword && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.confirmPassword}</p>}
            </div>

            <div className="flex items-start">
              <div className="flex items-center h-5">
                <input
                  id="terms"
                  name="terms"
                  type="checkbox"
                  className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                  required
                />
              </div>
              <div className="ml-3 text-sm">
                <label htmlFor="terms" className="font-medium text-gray-700 dark:text-gray-300">
                  I agree to the{' '}
                  <a href="#" className="text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300">
                    Terms of Service
                  </a>{' '}
                  and{' '}
                  <a href="#" className="text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300">
                    Privacy Policy
                  </a>
                </label>
              </div>
            </div>

            <div>
              <Button
                type="submit"
                className="w-full flex justify-center"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <ArrowPathIcon className="animate-spin -ml-1 mr-2 h-4 w-4" />
                    Creating account...
                  </>
                ) : (
                  'Create account'
                )}
              </Button>
            </div>
          </form>

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300 dark:border-gray-600"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-400">
                  Or sign up with
                </span>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-2 gap-3">
              <div>
                <a
                  href="#"
                  className="w-full inline-flex justify-center py-2 px-4 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-800 text-sm font-medium text-gray-500 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  <span className="sr-only">Sign up with GitHub</span>
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                    <path
                      fillRule="evenodd"
                      d="M10 0C4.477 0 0 4.484 0 10.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.156-1.11-1.462-1.11-1.462-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.026A9.564 9.564 0 0110 4.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.203 2.398.1 2.651.64.699 1.028 1.595 1.028 2.688 0 3.842-2.339 4.687-4.566 4.933.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C17.14 18.204 20 14.45 20 10.017 20 4.484 15.522 0 10 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                </a>
              </div>

              <div>
                <a
                  href="#"
                  className="w-full inline-flex justify-center py-2 px-4 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-800 text-sm font-medium text-gray-500 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  <span className="sr-only">Sign up with Google</span>
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12.545,10.239v3.821h5.445c-0.712,2.315-2.647,3.972-5.445,3.972c-3.332,0-6.033-2.701-6.033-6.032s2.701-6.032,6.033-6.032c1.498,0,2.866,0.549,3.921,1.453l2.814-2.814C17.503,2.988,14.991,2,12.166,2C6.626,2,2.167,6.459,2.167,12s4.459,10,10,10c8.396,0,10.249-7.85,9.426-11.748L12.545,10.239z"/>
                  </svg>
                </a>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Register;
