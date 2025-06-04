"use client";

import { useRef, useState } from 'react';
import { sendFolders } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

export const useFolderSelection = (onIndexed) => {
  const folderInputRef = useRef(null);
  const [folders, setFolders] = useState([]);
  const { toast } = useToast();

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
    setFolders(uniqueFolderNames);

    try {
      toast({ description: 'Updating folder selections...', duration: 2000 });
      await sendFolders(uniqueFolderNames);
      toast({ description: 'Folders updated successfully! Indexing images...', duration: 3000 });
      if (onIndexed) onIndexed();
    } catch (err) {
      console.error('Error updating folders:', err);
      toast({
        variant: 'destructive',
        title: 'Error updating folders',
        description: err.message || 'Failed to update folders. Please try again.',
        duration: 3000,
      });
    }
  };

  return { folders, folderInputRef, handleSelectFolders, handleFolderChange };
};
