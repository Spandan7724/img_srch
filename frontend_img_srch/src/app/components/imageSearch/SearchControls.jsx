"use client";
import React from 'react';
import { FolderOpen, Search, Loader2, X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

const SearchControls = ({
  query,
  setQuery,
  onSearch,
  isLoading,
  folderInputRef,
  onFolderChange,
  onSelectFolders,
  isSearchFocused,
  setIsSearchFocused,
  folders,
}) => {
  return (
    <>
      {/* Hidden input for folder selection */}
      <input
        type="file"
        ref={folderInputRef}
        className="hidden"
        webkitdirectory="true"
        multiple
        onChange={onFolderChange}
      />
      <div className="flex justify-center items-center max-w-3xl mx-auto gap-4 relative">
        {/* "Select Folders" button */}
        <Button
          variant="outline"
          className={`flex items-center gap-2 transition-all duration-300 border-gray-700 ${folders.length > 0 ? 'bg-blue-900/20 border-blue-700/30 text-blue-200' : 'bg-transparent text-white hover:bg-white'}`}
          onClick={onSelectFolders}
        >
          <FolderOpen className="h-4 w-4" />
          {folders.length > 0 ? 'Change Folders' : 'Select Folders'}
        </Button>
        {/* Search bar */}
        <div className="relative flex-1">
          <div className={`absolute inset-0 rounded-lg ${isSearchFocused ? 'ring-2 ring-blue-500/50' : ''} transition-all duration-300`}></div>
          <Input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Describe what you're looking for..."
            className="bg-gray-900/80 border-gray-700 text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent h-12 text-lg rounded-lg pl-4 pr-12 transition-all duration-200 backdrop-blur-sm"
            onKeyPress={(e) => e.key === 'Enter' && onSearch()}
            onFocus={() => setIsSearchFocused(true)}
            onBlur={() => setIsSearchFocused(false)}
          />
          {query && (
            <button
              className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-200 transition-colors"
              onClick={() => setQuery('')}
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        {/* "Search" button */}
        <Button
          onClick={onSearch}
          disabled={isLoading || !query.trim()}
          className={`bg-gradient-to-b from-black to-gray-900 text-white border border-gray-800 rounded-lg h-12 flex items-center gap-2 px-5 transition-all duration-200 hover:text-cyan-300 hover:shadow-[0_0_10px_rgba(34,211,238,0.4)] ${!query.trim() ? 'opacity-70' : ''}`}
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Search className="h-4 w-4" />
          )}
          {isLoading ? 'Searching...' : 'Search'}
        </Button>
      </div>
    </>
  );
};

export default SearchControls;
