"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Search, Loader2, FolderOpen, Copy, X, Maximize2, ChevronRight } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from "@/hooks/use-toast";

const getImageUrl = (path) => {
  if (!path) return ''; // Handle cases where path is undefined
  const filename = encodeURIComponent(path.split(/[\\/]/).pop());  // Extract filename and encode special chars
  return `http://localhost:8000/images/${filename}`;  // Ensure proper URL encoding
};

const ImageSearch = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null);
  const [copiedPath, setCopiedPath] = useState(null);
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [loadedImages, setLoadedImages] = useState({});

  // Single/double click timer
  const clickTimeout = useRef(null);

  // Folder selection states
  const folderInputRef = useRef(null);
  const [folders, setFolders] = useState([]);
  const [showFolderBadges, setShowFolderBadges] = useState(true);

  const { toast } = useToast();

  // -------------------------------
  //  Single vs. double-click logic
  // -------------------------------
  const handleSingleDoubleClick = (e, result) => {
    e.stopPropagation();

    if (clickTimeout.current) {
      // Double-click
      clearTimeout(clickTimeout.current);
      clickTimeout.current = null;
      openInViewer(result.path);
    } else {
      // Single-click
      clickTimeout.current = setTimeout(() => {
        setSelectedImage(result);
        clickTimeout.current = null;
      }, 250);
    }
  };

  // -------------------------------
  //  Folder selection logic
  // -------------------------------
  const handleSelectFolders = () => {
    if (folderInputRef.current) {
      folderInputRef.current.value = null;
      folderInputRef.current.click();
    }
  };

  const handleFolderChange = async (e) => {
    const fileList = [...e.target.files];
    if (fileList.length === 0) return;

    const folderNames = new Set();
    fileList.forEach((file) => {
      const relativePath = file.webkitRelativePath || file.name;
      const topLevelFolder = relativePath.split('/')[0];  
      folderNames.add(topLevelFolder);
    });

    const uniqueFolderNames = Array.from(folderNames);
    console.log("Sending folder names:", uniqueFolderNames);
    setFolders(uniqueFolderNames);

    try {
      toast({
        description: "Updating folder selections...",
        duration: 2000,
      });
      
      // Send selected folder names to the backend
      const folderResponse = await fetch('http://localhost:8000/folders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ folders: uniqueFolderNames }),
      });

      if (!folderResponse.ok) {
        const errorData = await folderResponse.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to update folders on server');
      }

      // Request backend to update the image directory being served
      const updateResponse = await fetch('http://localhost:8000/update-images/', { method: 'POST' });

      if (!updateResponse.ok) {
        throw new Error('Failed to update image directory on backend');
      }

      toast({
        description: "Folders updated successfully! Indexing images...",
        duration: 3000,
      });

      // Clear previous search results and wait for indexing to complete before reloading results
      setResults([]);
      setTimeout(() => {
        if (query.trim()) handleSearch();
      }, 1000);

    } catch (err) {
      console.error('Error updating folders:', err);
      toast({
        variant: "destructive",
        title: "Error updating folders",
        description: err.message || "Failed to update folders. Please try again.",
        duration: 3000,
      });
    }
  };

  // -------------------------------
  //  Searching logic
  // -------------------------------
  const handleSearch = async () => {
    if (!query.trim()) return;
    setIsLoading(true);
    setError(null);
    setResults([]);
    setLoadedImages({});

    try {
      const response = await fetch('http://localhost:8000/search/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query }),
      });
      if (!response.ok) {
        throw new Error('Search failed');
      }
      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError('Failed to fetch results. Please try again.');
      console.error('Search error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleImageLoad = (resultId) => {
    setLoadedImages(prev => ({
      ...prev,
      [resultId]: true
    }));
  };

  const handleCopyPath = (path) => {
    navigator.clipboard.writeText(path);
    setCopiedPath(path);
    toast({
      description: "Path copied to clipboard!",
      duration: 2000,
    });
    setTimeout(() => setCopiedPath(null), 2000);
  };

  const openInExplorer = async (path) => {
    try {
      console.log('Attempting to open path:', path);
      const response = await fetch('http://localhost:8000/open-file/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: path }),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to open file in explorer');
      }
      
      const data = await response.json();
      if (data.status === 'success') {
        toast({ description: "Opening file location...", duration: 2000 });
      } else {
        throw new Error('Unexpected response from server');
      }
    } catch (err) {
      console.error('Open file error details:', err.message);
      toast({
        variant: "destructive",
        title: "Error opening file",
        description: err.message || "Failed to open file location. Please try again.",
        duration: 3000,
      });
    }
  };

  const openInViewer = async (path) => {
    try {
      console.log('Attempting to open image file:', path);
      const response = await fetch('http://localhost:8000/open-image/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: path }),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to open image');
      }
      
      const data = await response.json();
      if (data.status === 'success') {
        toast({ description: "Opening image with default viewer...", duration: 2000 });
      } else {
        throw new Error('Unexpected response from server');
      }
    } catch (err) {
      console.error('Open image error details:', err.message);
      toast({
        variant: "destructive",
        title: "Error opening image",
        description: err.message || "Failed to open image file. Please try again.",
        duration: 3000,
      });
    }
  };

  // -------------------------------
  //  Keyboard shortcuts
  // -------------------------------
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
  }, [selectedImage]);

  // Calculate dynamic score color based on the match percentage
  const getScoreColor = (score) => {
    const scorePercent = score * 100;
    if (scorePercent >= 90) return 'text-emerald-400';
    if (scorePercent >= 80) return 'text-green-400';
    if (scorePercent >= 70) return 'text-lime-400';
    if (scorePercent >= 60) return 'text-yellow-400';
    if (scorePercent >= 50) return 'text-amber-400';
    return 'text-orange-400';
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-black to-gray-900 text-white">
      {/* Background noise texture */}
      <div 
        className="fixed inset-0 pointer-events-none opacity-[0.015] z-0" 
        style={{ 
          backgroundImage: "url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMzAwIj48ZmlsdGVyIGlkPSJhIiB4PSIwIiB5PSIwIj48ZmVUdXJidWxlbmNlIGJhc2VGcmVxdWVuY3k9Ii43NSIgc3RpdGNoVGlsZXM9InN0aXRjaCIgdHlwZT0iZnJhY3RhbE5vaXNlIi8+PGZlQ29sb3JNYXRyaXggdHlwZT0ic2F0dXJhdGUiIHZhbHVlcz0iMCIvPjwvZmlsdGVyPjxwYXRoIGQ9Ik0wIDBoMzAwdjMwMEgweiIgZmlsdGVyPSJ1cmwoI2EpIiBvcGFjaXR5PSIuMDUiLz48L3N2Zz4=')",
          backgroundSize: "200px 200px"
        }}
      />

      {/* Modal for enlarged image view */}
      {selectedImage && (
        <div
          className="fixed inset-0 bg-black/95 backdrop-blur-sm z-50 flex items-center justify-center"
          onClick={() => setSelectedImage(null)}
        >
          <div
            className="max-w-5xl w-full max-h-[90vh] p-4 relative"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            <button 
              className="absolute top-0 right-0 -mt-10 -mr-10 bg-white/10 backdrop-blur-sm p-2 rounded-full hover:bg-white/20 transition-all"
              onClick={() => setSelectedImage(null)}
            >
              <X className="h-5 w-5" />
            </button>
            
            {/* Image container with animation */}
            <div className="relative rounded-lg overflow-hidden shadow-2xl ring-1 ring-white/10 animate-fadeIn">
              <img
                src={selectedImage.full_url}
                alt="Selected result"
                className="max-w-full max-h-[75vh] object-contain rounded-lg w-full"
                onDoubleClick={(e) => {
                  e.stopPropagation();
                  openInViewer(selectedImage.path);
                }}
              />
              
              {/* Image overlay with controls */}
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 to-transparent p-4">
                <div className="flex items-center justify-between">
                  <p className="text-xl font-semibold">
                    Similarity Score: 
                    <span className={`ml-2 ${getScoreColor(selectedImage.score)}`}>
                      {(selectedImage.score * 100).toFixed(2)}%
                    </span>
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    className="bg-white/10 border-white/20 hover:bg-white/20"
                    onClick={(e) => {
                      e.stopPropagation();
                      openInViewer(selectedImage.path);
                    }}
                  >
                    <Maximize2 className="h-4 w-4 mr-2" />
                    Open in Viewer
                  </Button>
                </div>
                
                <div className="flex items-center gap-2 bg-black/50 backdrop-blur-sm rounded-lg p-3 mt-3">
                  <p className="text-gray-300 text-sm font-mono">{selectedImage.path}</p>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 rounded-full text-gray-400 hover:text-white hover:bg-white/10"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCopyPath(selectedImage.path);
                      }}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 rounded-full text-gray-400 hover:text-white hover:bg-white/10"
                      onClick={(e) => {
                        e.stopPropagation();
                        openInExplorer(selectedImage.path);
                      }}
                    >
                      <FolderOpen className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                <p className="text-sm text-gray-400 mt-2 text-center italic">
                  Double-click image to open in default viewer
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-6xl mx-auto px-6 py-12 relative z-10">
        <div className="mb-12 mt-8">
          <h1 className="text-4xl font-bold mb-2 text-center bg-gradient-to-r from-blue-400 via-cyan-200 to-indigo-200 bg-clip-text text-transparent drop-shadow-sm">
            Visual Search Explorer
          </h1>
          <p className="text-center text-gray-400 max-w-2xl mx-auto mb-10">
            Search your image library using natural language descriptions
          </p>

          {/* Hidden input for folder selection */}
          <input
            type="file"
            ref={folderInputRef}
            className="hidden"
            webkitdirectory="true"
            multiple
            onChange={handleFolderChange}
          />

          {/* Search interface */}
          <div className="flex justify-center items-center max-w-3xl mx-auto gap-4 relative">
            {/* "Select Folders" button */}
            <Button
              variant="outline"
              className={`flex items-center gap-2 transition-all duration-300 border-gray-700
                ${folders.length > 0 ? 'bg-blue-900/20 border-blue-700/30 text-blue-200' : 'bg-transparent text-white hover:bg-white'}`}
              onClick={handleSelectFolders}
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
                className="bg-gray-900/80 border-gray-700 text-white placeholder-gray-400 
                          focus:ring-2 focus:ring-blue-500 focus:border-transparent
                          h-12 text-lg rounded-lg pl-4 pr-12 transition-all duration-200 backdrop-blur-sm"
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
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
              onClick={handleSearch}
              disabled={isLoading || !query.trim()}
              className={`bg-gradient-to-b from-black to-gray-900 text-white 
                        border border-gray-800 rounded-lg h-12 flex items-center gap-2 px-5 
                        transition-all duration-200
                        hover:text-cyan-300 hover:shadow-[0_0_10px_rgba(34,211,238,0.4)] 
                        ${!query.trim() ? 'opacity-70' : ''}`}
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Search className="h-4 w-4" />
              )}
              {isLoading ? 'Searching...' : 'Search'}
            </Button>
          </div>
        </div>

        {/* If there is an error */}
        {error && (
          <Alert className="mb-6 bg-red-900/30 backdrop-blur-sm border-red-500 text-red-200 max-w-3xl mx-auto">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Display selected folders */}
        {folders.length > 0 && showFolderBadges && (
          <div className="max-w-3xl mx-auto mb-8 bg-gray-900/40 backdrop-blur-sm p-4 rounded-lg border border-gray-800">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-md font-medium text-white">Selected Folders:</h2>
              <Button 
                variant="ghost" 
                size="sm" 
                className="text-xs text-gray-400 hover:text-white"
                onClick={() => setShowFolderBadges(false)}
              >
                Hide
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              {folders.map((folder, index) => (
                <div key={index} className="flex items-center bg-blue-900/20 text-blue-200 text-sm px-2 py-1 rounded border border-blue-700/20">
                  <FolderOpen className="h-3 w-3 text-blue-400 mr-1" />
                  <span>{folder}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Results grid */}
        <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 ${results.length > 0 ? 'mb-10' : ''}`}>
          {results.map((result, index) => (
            <Card
              key={index}
              className="bg-gray-900/80 backdrop-blur-sm border-gray-800 overflow-hidden 
                       transform hover:scale-[1.02] hover:shadow-xl hover:shadow-blue-900/20
                       transition-all duration-300 cursor-pointer group rounded-xl"
              onClick={(e) => handleSingleDoubleClick(e, result)}
            >
              <CardContent className="p-0">
                <div className="relative">
                  {/* Image skeleton during loading */}
                  {!loadedImages[index] && (
                    <div className="w-full h-52 bg-gradient-to-br from-gray-800 to-gray-900 animate-pulse" />
                  )}
                  
                  <img
                    src={result.full_url}
                    alt={`Search result ${index + 1}`}
                    className={`w-full h-52 object-cover transition-all duration-500 ${loadedImages[index] ? 'opacity-100' : 'opacity-0'}`}
                    onLoad={() => handleImageLoad(index)}
                  />
                  
                  {/* Gradient overlay */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
                  
                  {/* Hover overlay */}
                  <div className="absolute inset-0 bg-blue-900/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  
                  {/* Score badge */}
                  <div className="absolute top-3 right-3 bg-black/70 backdrop-blur-sm rounded-full px-2 py-1 text-sm">
                    <span className="font-medium">Match: </span>
                    <span className={getScoreColor(result.score)}>
                      {(result.score * 100).toFixed(1)}%
                    </span>
                  </div>
                  
                  {/* View button */}
                  <div className="absolute bottom-3 right-3">
                    <Button
                      variant="outline"
                      size="sm"
                      className="bg-black/50 border-white/20 hover:bg-white/10 text-white opacity-0 group-hover:opacity-100 transition-all shadow-md"
                    >
                      View Details
                      <ChevronRight className="h-3 w-3 ml-1" />
                    </Button>
                  </div>
                </div>
                
                <div className="p-4">
                  <div className="flex items-center gap-2 bg-gray-800/50 rounded-lg p-2 group">
                    <p className="text-gray-300 text-sm font-mono truncate flex-1">
                      {result.path.split(/[\\/]/).pop()} {/* Just the filename */}
                    </p>
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0.5 text-gray-400 hover:text-white rounded-full"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCopyPath(result.path);
                        }}
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0.5 text-gray-400 hover:text-white rounded-full"
                        onClick={(e) => {
                          e.stopPropagation();
                          openInExplorer(result.path);
                        }}
                      >
                        <FolderOpen className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* No results message */}
        {results.length === 0 && !isLoading && !error && (
          <div className="text-center text-gray-400 mt-16 bg-gray-900/30 backdrop-blur-sm rounded-xl p-8 max-w-xl mx-auto">
            <div className="relative mx-auto w-16 h-16 mb-4">
              <Search className="w-16 h-16 mx-auto opacity-30" />
              <div className="absolute inset-0 bg-gradient-to-tr from-blue-500 to-purple-500 opacity-10 rounded-full blur-xl" />
            </div>
            <p className="text-lg">Enter a description to start searching...</p>
            <p className="text-sm text-gray-500 mt-2">Example: "sunset over mountains" or "car in urban setting"</p>
          </div>
        )}

        {/* Loading spinner */}
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
        
        {/* Footer */}
        <div className="text-center text-gray-600 mt-12 text-sm">
        </div>
      </div>
    </div>
  );
};

export default ImageSearch;