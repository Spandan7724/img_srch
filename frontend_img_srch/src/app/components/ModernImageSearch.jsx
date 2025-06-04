"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import SearchControls from './SearchControls';
import SelectedFolders from './SelectedFolders';
import ResultCard from './ResultCard';
import ImageModal from './ImageModal';
import { useImageSearch } from '@/hooks/useImageSearch';
import { useFolderSelection } from '@/hooks/useFolderSelection';
import { useOpenFile } from '@/hooks/useOpenFile';

const ImageSearch = () => {
  const [selectedImage, setSelectedImage] = useState(null);
  const [copiedPath, setCopiedPath] = useState(null);
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [showFolderBadges, setShowFolderBadges] = useState(true);

  const {
    query,
    setQuery,
    results,
    isLoading,
    error,
    handleSearch,
    loadedImages,
    handleImageLoad,
  } = useImageSearch();

  const { openInExplorer, openInViewer } = useOpenFile();
  const {
    folders,
    folderInputRef,
    handleSelectFolders,
    handleFolderChange,
  } = useFolderSelection(handleSearch);

  const clickTimeout = useRef(null);

  const handleSingleDoubleClick = (e, result) => {
    e.stopPropagation();

    if (clickTimeout.current) {
      clearTimeout(clickTimeout.current);
      clickTimeout.current = null;
      openInViewer(result.path);
    } else {
      clickTimeout.current = setTimeout(() => {
        setSelectedImage(result);
        clickTimeout.current = null;
      }, 250);
    }
  };

  const handleCopyPath = (path) => {
    navigator.clipboard.writeText(path);
    setCopiedPath(path);
    setTimeout(() => setCopiedPath(null), 2000);
  };

  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.key === 'Escape' && selectedImage) {
        setSelectedImage(null);
      }
      if (e.key === 'Enter' && document.activeElement === document.querySelector('input')) {
        handleSearch();
      }
    };
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [selectedImage, handleSearch]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-black to-gray-900 text-white">
      <div
        className="fixed inset-0 pointer-events-none opacity-[0.015] z-0"
        style={{
          backgroundImage: "url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMzAwIj48ZmlsdGVyIGlkPSJhIiB4PSIwIiB5PSIwIj48ZmVUdXJidWxlbmNlIGJhc2VGcmVxdWVuY3k9Ii43NSIgc3RpdGNoVGlsZXM9InN0aXRjaCIgdHlwZT0iZnJhY3RhbE5vaXNlIi8+PGZlQ29sb3JNYXRyaXggdHlwZT0ic2F0dXJhdGUiIHZhbHVlcz0iMCIvPjwvZmlsdGVyPjxwYXRoIGQ9Ik0wIDBoMzAwdjMwMEgweiIgZmlsdGVyPSJ1cmwoI2EpIiBvcGFjaXR5PSIuMDUiLz48L3N2Zz4=')",
          backgroundSize: '200px 200px',
        }}
      />

      {selectedImage && (
        <ImageModal
          image={selectedImage}
          onClose={() => setSelectedImage(null)}
          onCopyPath={() => handleCopyPath(selectedImage.path)}
          openInExplorer={() => openInExplorer(selectedImage.path)}
          openInViewer={() => openInViewer(selectedImage.path)}
        />
      )}

      <div className="max-w-6xl mx-auto px-6 py-12 relative z-10">
        <div className="mb-12 mt-8">
          <h1 className="text-4xl font-bold mb-2 text-center bg-gradient-to-r from-blue-400 via-cyan-200 to-indigo-200 bg-clip-text text-transparent drop-shadow-sm">
            Visual Search Explorer
          </h1>
          <p className="text-center text-gray-400 max-w-2xl mx-auto mb-10">
            Search your image library using natural language descriptions
          </p>

          <SearchControls
            query={query}
            setQuery={setQuery}
            onSearch={handleSearch}
            isLoading={isLoading}
            folders={folders}
            onSelectFolders={handleSelectFolders}
            folderInputRef={folderInputRef}
            onFolderChange={handleFolderChange}
            isSearchFocused={isSearchFocused}
            setIsSearchFocused={setIsSearchFocused}
          />
        </div>

        {error && (
          <Alert className="mb-6 bg-red-900/30 backdrop-blur-sm border-red-500 text-red-200 max-w-3xl mx-auto">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {folders.length > 0 && showFolderBadges && (
          <SelectedFolders folders={folders} onHide={() => setShowFolderBadges(false)} />
        )}

        <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 ${results.length > 0 ? 'mb-10' : ''}`}>
          {results.map((result, index) => (
            <ResultCard
              key={index}
              result={result}
              index={index}
              loaded={loadedImages[index]}
              onLoad={() => handleImageLoad(index)}
              onClick={(e) => handleSingleDoubleClick(e, result)}
              onCopyPath={(e) => {
                e.stopPropagation();
                handleCopyPath(result.path);
              }}
              openInExplorer={(e) => {
                e.stopPropagation();
                openInExplorer(result.path);
              }}
            />
          ))}
        </div>

        {results.length === 0 && !isLoading && !error && (
          <div className="text-center text-gray-400 mt-16 bg-gray-900/30 backdrop-blur-sm rounded-xl p-8 max-w-xl mx-auto">
            <div className="relative mx-auto w-16 h-16 mb-4">
              <Search className="w-16 h-16 mx-auto opacity-30" />
              <div className="absolute inset-0 bg-gradient-to-tr from-blue-500 to-purple-500 opacity-10 rounded-full blur-xl" />
            </div>
            <p className="text-lg">Enter a description to start searching...</p>
            <p className="text-sm text-gray-500 mt-2">Example: &quot;sunset over mountains&quot; or &quot;car in urban setting&quot;</p>
          </div>
        )}

        {isLoading && results.length === 0 && (
          <div className="text-center text-gray-400 mt-16 bg-gray-900/30 backdrop-blur-sm rounded-xl p-8 max-w-xl mx-auto">
            <div className="relative mx-auto w-16 h-16 mb-4">
              <Loader2 className="w-16 h-16 mx-auto animate-spin opacity-30" />
              <div className="absolute inset-0 bg-gradient-to-tr from-blue-500 to-purple-500 opacity-10 rounded-full blur-xl" />
            </div>
            <p className="text-lg">Searching through images...</p>
            <p className="text-sm text-gray-500 mt-2">This may take a moment depending on your library size</p>
          </div>
        )}

        <div className="text-center text-gray-600 mt-12 text-sm"></div>
      </div>
    </div>
  );
};

export default ImageSearch;
