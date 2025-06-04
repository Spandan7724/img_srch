"use client";

import { openFile, openImage } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

export const useOpenFile = () => {
  const { toast } = useToast();

  const openInExplorer = async (path) => {
    try {
      const data = await openFile(path);
      if (data.status === 'success') {
        toast({ description: 'Opening file location...', duration: 2000 });
      } else {
        throw new Error('Unexpected response from server');
      }
    } catch (err) {
      console.error('Open file error details:', err.message);
      toast({
        variant: 'destructive',
        title: 'Error opening file',
        description: err.message || 'Failed to open file location. Please try again.',
        duration: 3000,
      });
    }
  };

  const openInViewer = async (path) => {
    try {
      const data = await openImage(path);
      if (data.status === 'success') {
        toast({ description: 'Opening image with default viewer...', duration: 2000 });
      } else {
        throw new Error('Unexpected response from server');
      }
    } catch (err) {
      console.error('Open image error details:', err.message);
      toast({
        variant: 'destructive',
        title: 'Error opening image',
        description: err.message || 'Failed to open image file. Please try again.',
        duration: 3000,
      });
    }
  };

  return { openInExplorer, openInViewer };
};
