"use client";

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { FolderOpen, Copy, ChevronRight, Loader2, Search } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from "@/hooks/use-toast";
import { useWebSocket } from "@/hooks/use-websocket";
import SearchControls from './imageSearch/SearchControls';
import FolderBadges from './imageSearch/FolderBadges';
import ImageModal from './imageSearch/ImageModal';
import IndexingStatusBanner from './imageSearch/IndexingStatusBanner';

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

  // Indexing status state
  const [indexingStatus, setIndexingStatus] = useState({
    visible: false,
    type: null,
    folder: null,
    current_file: null,
    processed: 0,
    total: 0,
    percentage: 0,
    total_indexed: 0,
    message: null,
    error: null,
    timestamp: null
  });

  const { toast } = useToast();

  // WebSocket message handler
  const handleWebSocketMessage = useCallback((data) => {
    console.log('WebSocket message received:', data);
    
    setIndexingStatus(prev => ({
      ...prev,
      visible: true,
      type: data.type,
      folder: data.folder || prev.folder,
      current_file: data.current_file || prev.current_file,
      processed: data.processed ?? prev.processed,
      total: data.total ?? prev.total,
      percentage: data.percentage ?? prev.percentage,
      total_indexed: data.total_indexed ?? prev.total_indexed,
      message: data.message || prev.message,
      error: data.error || prev.error,
      timestamp: data.timestamp || prev.timestamp
    }));

    // Auto-dismiss success messages after 10 seconds
    if (data.type === 'indexing_completed') {
      setTimeout(() => {
        setIndexingStatus(prev => ({ ...prev, visible: false }));
      }, 10000);
    }
  }, []);

  // WebSocket connection
  const { isConnected, connectionError } = useWebSocket(
    'ws://localhost:8000/ws',
    handleWebSocketMessage
  );

  // Dismiss status banner
  const dismissIndexingStatus = useCallback(() => {
    setIndexingStatus(prev => ({ ...prev, visible: false }));
  }, []);

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

      // No need for toast here since WebSocket will show real-time progress
      // Clear previous search results
      setResults([]);

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
  const handleSearch = useCallback(async () => {
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
  }, [query]);

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
  }, [selectedImage, handleSearch]);

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
      {/* Indexing Status Banner */}
      <IndexingStatusBanner 
        status={indexingStatus} 
        onDismiss={dismissIndexingStatus} 
      />
      
      {/* Background noise texture */}
      <div 
        className="fixed inset-0 pointer-events-none opacity-[0.015] z-0" 
        style={{ 
          backgroundImage: "url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMzAwIj48ZmlsdGVyIGlkPSJhIiB4PSIwIiB5PSIwIj48ZmVUdXJidWxlbmNlIGJhc2VGcmVxdWVuY3k9Ii43NSIgc3RpdGNoVGlsZXM9InN0aXRjaCIgdHlwZT0iZnJhY3RhbE5vaXNlIi8+PGZlQ29sb3JNYXRyaXggdHlwZT0ic2F0dXJhdGUiIHZhbHVlcz0iMCIvPjwvZmlsdGVyPjxwYXRoIGQ9Ik0wIDBoMzAwdjMwMEgweiIgZmlsdGVyPSJ1cmwoI2EpIiBvcGFjaXR5PSIuMDUiLz48L3N2Zz4=')",
          backgroundSize: "200px 200px"
        }}
      />

      <ImageModal
        image={selectedImage}
        onClose={() => setSelectedImage(null)}
        onCopy={handleCopyPath}
        onOpenExplorer={openInExplorer}
        onOpenViewer={openInViewer}
        getScoreColor={getScoreColor}
      />

      <div className={`max-w-6xl mx-auto px-6 py-12 relative z-10 ${indexingStatus.visible ? 'pt-20' : ''}`}>
        <div className="mb-12 mt-8">
          <h1 className="text-4xl font-bold mb-2 text-center bg-gradient-to-r from-blue-400 via-cyan-200 to-indigo-200 bg-clip-text text-transparent drop-shadow-sm">
            Visual Search Explorer
          </h1>
          <p className="text-center text-gray-400 max-w-2xl mx-auto mb-10">
            Search your image library using natural language descriptions
          </p>

          {/* Connection status indicator */}
          {!isConnected && (
            <div className="text-center mb-4">
              <span className="text-xs text-yellow-400 bg-yellow-900/20 px-2 py-1 rounded">
                ⚠️ Live updates disconnected - features may be limited
              </span>
            </div>
          )}

          <SearchControls
            query={query}
            setQuery={setQuery}
            onSearch={handleSearch}
            isLoading={isLoading}
            folderInputRef={folderInputRef}
            onFolderChange={handleFolderChange}
            onSelectFolders={handleSelectFolders}
            isSearchFocused={isSearchFocused}
            setIsSearchFocused={setIsSearchFocused}
            folders={folders}
          />
        </div>

        {/* If there is an error */}
        {error && (
          <Alert className="mb-6 bg-red-900/30 backdrop-blur-sm border-red-500 text-red-200 max-w-3xl mx-auto">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <FolderBadges
          folders={folders}
          show={showFolderBadges}
          onHide={() => setShowFolderBadges(false)}
        />

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
            <p className="text-sm text-gray-500 mt-2">Example: &quot;sunset over mountains&quot; or &quot;car in urban setting&quot;</p>
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