import React, { useState, useRef, useEffect } from 'react';
import classNames from 'classnames';

interface TooltipProps {
  content: React.ReactNode;
  position?: 'top' | 'right' | 'bottom' | 'left';
  children: React.ReactElement;
  className?: string;
  delay?: number;
}

export const Tooltip: React.FC<TooltipProps> = ({
  content,
  position = 'top',
  children,
  className = '',
  delay = 300,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [coords, setCoords] = useState({ x: 0, y: 0 });
  const tooltipRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<number | null>(null);

  const showTooltip = (e: React.MouseEvent) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    setCoords({
      x: rect.left + window.scrollX,
      y: rect.top + window.scrollY,
    });
    
    timeoutRef.current = window.setTimeout(() => {
      setIsVisible(true);
    }, delay);
  };

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setIsVisible(false);
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
  };

  const arrowClasses = {
    top: 'top-full left-1/2 -translate-x-1/2 border-t-gray-800 dark:border-t-gray-700 border-x-transparent border-b-0',
    right: 'right-full top-1/2 -translate-y-1/2 border-r-gray-800 dark:border-r-gray-700 border-t-transparent border-b-transparent border-l-0',
    bottom: 'bottom-full left-1/2 -translate-x-1/2 border-b-gray-800 dark:border-b-gray-700 border-x-transparent border-t-0',
    left: 'left-full top-1/2 -translate-y-1/2 border-l-gray-800 dark:border-l-gray-700 border-t-transparent border-b-transparent border-r-0',
  };

  return (
    <div className="relative inline-block">
      {React.cloneElement(children, {
        onMouseEnter: (e: React.MouseEvent) => {
          showTooltip(e);
          children.props.onMouseEnter?.(e);
        },
        onMouseLeave: (e: React.MouseEvent) => {
          hideTooltip();
          children.props.onMouseLeave?.(e);
        },
        onFocus: (e: React.FocusEvent) => {
          showTooltip(e as unknown as React.MouseEvent);
          children.props.onFocus?.(e);
        },
        onBlur: (e: React.FocusEvent) => {
          hideTooltip();
          children.props.onBlur?.(e);
        },
      })}
      
      {isVisible && (
        <div
          ref={tooltipRef}
          className={classNames(
            'absolute z-50 px-3 py-1.5 text-sm text-white bg-gray-800 dark:bg-gray-700 rounded shadow-lg whitespace-nowrap',
            positionClasses[position],
            className
          )}
          role="tooltip"
        >
          {content}
          <div
            className={classNames(
              'absolute w-0 h-0 border-4',
              arrowClasses[position]
            )}
          />
        </div>
      )}
    </div>
  );
};
