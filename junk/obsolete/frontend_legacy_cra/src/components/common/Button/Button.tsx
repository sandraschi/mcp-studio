import React, { ButtonHTMLAttributes, forwardRef } from 'react';
import { classNames } from '../../../utils/classNames';

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost' | 'link';
type ButtonSize = 'xs' | 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
  loading?: boolean;
  as?: React.ElementType;
  href?: string;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      className = '',
      variant = 'primary',
      size = 'md',
      leftIcon,
      rightIcon,
      fullWidth = false,
      loading = false,
      disabled = false,
      as: Component = 'button',
      ...props
    },
    ref
  ) => {
    const baseStyles = 'inline-flex items-center justify-center font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors duration-150';
    
    const variantStyles = {
      primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500 disabled:bg-blue-400 dark:bg-blue-700 dark:hover:bg-blue-600',
      secondary: 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus:ring-blue-500 disabled:bg-gray-100 dark:bg-gray-700 dark:text-white dark:border-gray-600 dark:hover:bg-gray-600',
      danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500 disabled:bg-red-400 dark:bg-red-700 dark:hover:bg-red-600',
      ghost: 'text-gray-700 hover:bg-gray-100 focus:ring-blue-500 disabled:text-gray-400 dark:text-gray-200 dark:hover:bg-gray-700',
      link: 'text-blue-600 hover:text-blue-800 focus:ring-blue-500 underline p-0 h-auto',
    };

    const sizeStyles = {
      xs: 'px-2.5 py-1.5 text-xs',
      sm: 'px-3 py-2 text-sm',
      md: 'px-4 py-2 text-sm',
      lg: 'px-6 py-3 text-base',
    };

    const iconSize = {
      xs: 'h-3 w-3',
      sm: 'h-3.5 w-3.5',
      md: 'h-4 w-4',
      lg: 'h-5 w-5',
    };

    const isDisabled = disabled || loading;

    return (
      <Component
        ref={ref}
        className={classNames(
          baseStyles,
          variantStyles[variant],
          sizeStyles[size],
          fullWidth ? 'w-full justify-center' : '',
          isDisabled ? 'opacity-70 cursor-not-allowed' : '',
          className
        )}
        disabled={isDisabled}
        {...props}
      >
        {loading && (
          <svg
            className={classNames(
              'animate-spin -ml-1 mr-2',
              iconSize[size]
            )}
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {!loading && leftIcon && (
          <span className={classNames('mr-2', iconSize[size])}>
            {leftIcon}
          </span>
        )}
        {children}
        {rightIcon && (
          <span className={classNames('ml-2', iconSize[size])}>
            {rightIcon}
          </span>
        )}
      </Component>
    );
  }
);

Button.displayName = 'Button';

export default Button;
