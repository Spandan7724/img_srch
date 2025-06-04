"use client";

import { useState } from 'react';
import { searchImages } from '@/lib/api';

export const useImageSearch = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [loadedImages, setLoadedImages] = useState({});

  const handleSearch = async () => {
    if (!query.trim()) return;
    setIsLoading(true);
    setError(null);
    setResults([]);
    setLoadedImages({});
    try {
      const data = await searchImages(query);
      setResults(data);
    } catch (err) {
      setError('Failed to fetch results. Please try again.');
      console.error('Search error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleImageLoad = (id) =>
    setLoadedImages((prev) => ({
      ...prev,
      [id]: true,
    }));

  return {
    query,
    setQuery,
    results,
    isLoading,
    error,
    handleSearch,
    loadedImages,
    handleImageLoad,
  };
};
