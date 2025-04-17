// src/app/components/ModernImageSearch.jsx
// This component is a modern image search interface that allows users to search for images


"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Search, Loader2, FolderOpen, Copy } from 'lucide-react';
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

  // Single/double click timer
  const clickTimeout = useRef(null);

  // Folder selection states
  const folderInputRef = useRef(null);  // We'll use this to programmatically open a folder dialog
  const [folders, setFolders] = useState([]);

  const { toast } = useToast();

  // -------------------------------
  //  Single vs. double-click logic
  // -------------------------------
  const handleSingleDoubleClick = (e, result) => {
    e.stopPropagation(); // Prevent event from bubbling up

    if (clickTimeout.current) {
      // Double-click
      clearTimeout(clickTimeout.current);
      clickTimeout.current = null;
      console.log("Double-click detected on card!");
      openInViewer(result.path);
    } else {
      // Single-click
      clickTimeout.current = setTimeout(() => {
        console.log("Single-click detected on card!");
        setSelectedImage(result);
        clickTimeout.current = null;
      }, 250); // Standard double-click time
    }
  };

  // -------------------------------
  //  Folder selection logic
  // -------------------------------
  const handleSelectFolders = () => {
    if (folderInputRef.current) {
      folderInputRef.current.value = null; // Reset so onChange always fires
      folderInputRef.current.click();       // Open the native folder selection dialog
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

  try {
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

    console.log('Folders successfully updated');

    // Request backend to update the image directory being served
    const updateResponse = await fetch('http://localhost:8000/update-images/', { method: 'POST' });

    if (!updateResponse.ok) {
      throw new Error('Failed to update image directory on backend');
    }

    console.log('Image directory updated successfully');

    // Clear previous search results and wait for indexing to complete before reloading results
    setResults([]);
    setTimeout(() => handleSearch(), 1000);  // Allow time for images to be indexed

  } catch (err) {
    console.error('Error updating folders:', err);
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
      console.log('Response status:', response.status);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to open file in explorer');
      }
      const data = await response.json();
      console.log('Response data:', data);
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
      console.log('Response status:', response.status);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to open image');
      }
      const data = await response.json();
      console.log('Response data:', data);
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

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Modal for enlarged image view */}
      {selectedImage && (
        <div
          className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center"
          onClick={() => setSelectedImage(null)}
        >
          <div
            className="max-w-4xl max-h-[90vh] p-4"
            onClick={(e) => e.stopPropagation()}
          >
            <img
              src={selectedImage.full_url}
              alt="Selected result"
              className="max-w-full max-h-[80vh] object-contain rounded-lg shadow-2xl"
              onDoubleClick={(e) => {
                e.stopPropagation();
                console.log("Double-click in modal!");
                openInViewer(selectedImage.path);
              }}
            />
            <div className="mt-4 text-center space-y-2">
              <p className="text-xl font-semibold">
                Similarity Score: {(selectedImage.score * 100).toFixed(2)}%
              </p>
              <div className="flex items-center justify-center gap-2 bg-gray-800/50 rounded-lg p-2">
                <p className="text-gray-300 text-sm font-mono">{selectedImage.path}</p>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-gray-400 hover:text-white"
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
                  className="text-gray-400 hover:text-white"
                  onClick={(e) => {
                    e.stopPropagation();
                    openInExplorer(selectedImage.path);
                  }}
                >
                  <FolderOpen className="h-4 w-4" />
                </Button>
              </div>
              <p className="text-sm text-gray-400">
                Double-click image to open in default viewer
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-6xl mx-auto p-6">
        <div className="mb-12 mt-8">
          <h1 className="text-4xl font-bold mb-8 text-center bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
            Visual Search Explorer
          </h1>

          {/* Hidden input for folder selection */}
          <input
            type="file"
            ref={folderInputRef}
            className="hidden"
            webkitdirectory="true"
            multiple
            onChange={handleFolderChange}
          />

          <div className="relative max-w-2xl mx-auto flex items-center gap-2">
            {/* "Select Folders" button */}
            <Button
              variant="ghost"
              className="flex items-center gap-1 text-white hover:text-gray-200"
              onClick={handleSelectFolders}
            >
              <FolderOpen className="h-4 w-4" />
              Select Folders
            </Button>

            {/* Search bar */}
            <Input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Describe what you're looking for..."
              className="w-full bg-gray-900 border-gray-700 text-white placeholder-gray-400 
                         focus:ring-2 focus:ring-blue-500 focus:border-transparent
                         h-12 text-lg rounded-lg"
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />

            {/* "Search" button */}
            <Button
              onClick={handleSearch}
              disabled={isLoading}
              className="bg-gradient-to-r from-blue-500 to-purple-500 
                         hover:from-blue-600 hover:to-purple-600 text-white 
                         rounded-md h-8 flex items-center gap-2 px-4 transition-all duration-200"
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
          <Alert className="mb-6 bg-red-900/50 border-red-500 text-red-200">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Display selected folders */}
        {folders.length > 0 && (
          <div className="max-w-2xl mx-auto mb-6 bg-black p-4 rounded-md">
            <h2 className="text-md font-semibold mb-2 text-white text-center">Selected Folders:</h2>
            <ul className="space-y-1 text-gray-300 text-center">
              {folders.map((folder, index) => (
                <li key={index} className="flex items-center justify-center gap-2">
                  <FolderOpen className="h-4 w-4 text-gray-400" />
                  <span>{folder}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Results grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {results.map((result, index) => (
            <Card
              key={index}
              className="bg-gray-900 border-gray-800 overflow-hidden transform hover:scale-105 
                         transition-all duration-200 cursor-pointer group"
              onClick={(e) => handleSingleDoubleClick(e, result)}
            >
              <CardContent className="p-4">
                <div className="relative">
                  <img
                    src={result.full_url}
                    alt={`Search result ${index + 1}`}
                    className="w-full h-48 object-cover rounded-lg mb-3"
                  />
                  <div
                    className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent 
                               opacity-0 group-hover:opacity-100 transition-opacity duration-200
                               flex items-end p-4"
                  >
                    <p className="text-white font-medium">
                      Single-click to enlarge, double-click to open in viewer
                    </p>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <p className="font-medium text-blue-400">Match Score</p>
                    <p className="text-white">
                      {(result.score * 100).toFixed(2)}%
                    </p>
                  </div>
                  <div className="flex items-center gap-2 bg-gray-800/50 rounded p-2 group">
                    <p className="text-gray-400 text-sm font-mono truncate flex-1">
                      {result.path}
                    </p>
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0.5 text-gray-400 hover:text-white"
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
                        className="h-6 w-6 p-0.5 text-gray-400 hover:text-white"
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
          <div className="text-center text-gray-400 mt-12">
            <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="text-lg">Enter a description to start searching...</p>
          </div>
        )}

        {/* Loading spinner */}
        {isLoading && results.length === 0 && (
          <div className="text-center text-gray-400 mt-12">
            <Loader2 className="h-12 w-12 mx-auto mb-4 animate-spin" />
            <p className="text-lg">Searching through images...</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ImageSearch;