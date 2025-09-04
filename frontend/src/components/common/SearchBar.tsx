import React, { useState, useEffect, useRef } from 'react';
import { SearchIcon, XIcon } from './Icons';

interface SearchBarProps {
  placeholder?: string;
  onSearch?: (query: string) => void;
  className?: string;
}

const SearchBar: React.FC<SearchBarProps> = ({
  placeholder = 'Search...',
  onSearch,
  className = '',
}) => {
  const [query, setQuery] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const searchTimeout = useRef<NodeJS.Timeout>();

  // Handle search with debounce
  useEffect(() => {
    if (onSearch) {
      if (searchTimeout.current) {
        clearTimeout(searchTimeout.current);
      }
      
      searchTimeout.current = setTimeout(() => {
        onSearch(query);
      }, 300);

      return () => {
        if (searchTimeout.current) {
          clearTimeout(searchTimeout.current);
        }
      };
    }
  }, [query, onSearch]);

  const handleClear = () => {
    setQuery('');
    inputRef.current?.focus();
  };

  return (
    <div 
      className={`relative rounded-md shadow-sm ${className} ${
        isFocused ? 'ring-2 ring-blue-500 ring-opacity-50' : ''
      }`}
    >
      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <SearchIcon className="h-4 w-4 text-gray-400" />
      </div>
      
      <input
        ref={inputRef}
        type="text"
        className="block w-full pl-10 pr-10 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent sm:text-sm"
        placeholder={placeholder}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        onKeyDown={(e) => {
          if (e.key === 'Escape') {
            e.currentTarget.blur();
          }
        }}
      />
      
      {query && (
        <div className="absolute inset-y-0 right-0 flex items-center pr-3">
          <button
            type="button"
            className="text-gray-400 hover:text-gray-500 dark:hover:text-gray-300 focus:outline-none"
            onClick={handleClear}
          >
            <XIcon className="h-4 w-4" />
            <span className="sr-only">Clear search</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default SearchBar;
