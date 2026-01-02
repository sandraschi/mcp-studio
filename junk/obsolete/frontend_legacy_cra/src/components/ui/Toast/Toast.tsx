import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import { cn } from '../../../lib/utils';
import { Toast as ToastType, ToastVariant } from './use-toast';

interface ToastProps extends React.HTMLAttributes<HTMLDivElement> {
  toast: ToastType;
  onDismiss: (id: string) => void;
  className?: string;
}

const variantStyles: Record<ToastVariant, string> = {
  default: 'bg-white border-gray-200',
  destructive: 'bg-red-50 border-red-200',
  success: 'bg-green-50 border-green-200',
};

export const Toast: React.FC<ToastProps> = ({ 
  toast, 
  onDismiss, 
  className,
  ...props 
}) => {
  useEffect(() => {
    if (toast.duration) {
      const timer = setTimeout(() => {
        onDismiss(toast.id);
      }, toast.duration);
      
      return () => clearTimeout(timer);
    }
  }, [toast, onDismiss]);

  return (
    <div
      className={cn(
        'relative w-full flex items-center justify-between p-4 mb-2 rounded-md border shadow-sm',
        variantStyles[toast.variant || 'default'],
        className
      )}
      {...props}
    >
      <div className="flex-1">
        {toast.title && (
          <h3 className="text-sm font-medium text-gray-900">
            {toast.title}
          </h3>
        )}
        {toast.description && (
          <p className="mt-1 text-sm text-gray-500">
            {toast.description}
          </p>
        )}
      </div>
      <button
        type="button"
        onClick={() => onDismiss(toast.id)}
        className="ml-4 p-1 text-gray-400 hover:text-gray-500 focus:outline-none"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
};
