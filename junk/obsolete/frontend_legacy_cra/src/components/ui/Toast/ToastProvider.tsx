import React, { createContext, useCallback, useState } from 'react';
import { Toast } from './Toast';
import { Toast as ToastType, useToast as useToastHook } from './use-toast';

interface ToastContextType {
  toasts: ToastType[];
  toast: (options: Omit<ToastType, 'id'>) => void;
  removeToast: (id: string) => void;
}

export const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { toasts, toast, removeToast } = useToastHook();

  return (
    <ToastContext.Provider value={{ toasts, toast, removeToast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 w-80 space-y-2">
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            toast={toast}
            onDismiss={removeToast}
          />
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = React.useContext(ToastContext);
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};
