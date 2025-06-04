"use client";
import React from 'react';
import { Button } from '@/components/ui/button';
import { FolderOpen } from 'lucide-react';

const FolderBadges = ({ folders, show, onHide }) => {
  if (folders.length === 0 || !show) return null;
  return (
    <div className="max-w-3xl mx-auto mb-8 bg-gray-900/40 backdrop-blur-sm p-4 rounded-lg border border-gray-800">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-md font-medium text-white">Selected Folders:</h2>
        <Button
          variant="ghost"
          size="sm"
          className="text-xs text-gray-400 hover:text-white"
          onClick={onHide}
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
  );
};

export default FolderBadges;
