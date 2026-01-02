import React, { useEffect, useRef } from 'react';
import { XIcon } from '../Icons';
import { Button } from '../Button';
import { classNames } from '../../../utils/classNames';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | '6xl' | '7xl';
  showCloseButton?: boolean;
  closeOnClickOutside?: boolean;
  closeOnEscape?: boolean;
  initialFocusRef?: React.RefObject<HTMLElement>;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
  showCloseButton = true,
  closeOnClickOutside = true,
  closeOnEscape = true,
  initialFocusRef,
}) => {
  const modalRef = useRef<HTMLDivElement>(null);

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        isOpen &&
        closeOnClickOutside &&
        modalRef.current &&
        !modalRef.current.contains(event.target as Node)
      ) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose, closeOnClickOutside]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (isOpen && closeOnEscape && event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose, closeOnEscape]);

  // Set initial focus
  useEffect(() => {
    if (isOpen && initialFocusRef?.current) {
      initialFocusRef.current.focus();
    }
  }, [isOpen, initialFocusRef]);

  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
    '3xl': 'max-w-3xl',
    '4xl': 'max-w-4xl',
    '5xl': 'max-w-5xl',
    '6xl': 'max-w-6xl',
    '7xl': 'max-w-7xl',
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      <div className="flex min-h-screen items-end justify-center px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div 
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" 
          aria-hidden="true"
          onClick={closeOnClickOutside ? onClose : undefined}
        ></div>

        {/* Modal panel */}
        <span className="hidden sm:inline-block sm:h-screen sm:align-middle" aria-hidden="true">
          &#8203;
        </span>
        
        <div
          ref={modalRef}
          className={classNames(
            'inline-block transform overflow-hidden rounded-lg bg-white dark:bg-gray-800 text-left align-bottom shadow-xl transition-all sm:my-8 sm:w-full sm:align-middle',
            sizeClasses[size],
            'relative'
          )}
        >
          {/* Header */}
          <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <h3 
                className="text-lg font-medium leading-6 text-gray-900 dark:text-white" 
                id="modal-title"
              >
                {title}
              </h3>
              
              {showCloseButton && (
                <div className="ml-3 flex h-7 items-center">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={onClose}
                    className="text-gray-400 hover:text-gray-500 dark:text-gray-400 dark:hover:text-gray-300"
                    aria-label="Close"
                  >
                    <XIcon className="h-5 w-5" />
                  </Button>
                </div>
              )}
            </div>
          </div>

          {/* Content */}
          <div className="px-4 py-5 sm:p-6">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Modal;
