"use client";
import React from 'react';
import { CheckCircle, Loader2, AlertCircle, X, FolderOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from "@/components/ui/progress";

const IndexingStatusBanner = ({ status, onDismiss }) => {
  if (!status.visible) return null;

  const getStatusIcon = () => {
    switch (status.type) {
      case 'indexing_started':
      case 'indexing_progress':
        return <Loader2 className="h-5 w-5 animate-spin text-blue-400" />;
      case 'indexing_completed':
        return <CheckCircle className="h-5 w-5 text-green-400" />;
      case 'indexing_error':
        return <AlertCircle className="h-5 w-5 text-red-400" />;
      default:
        return <FolderOpen className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusColor = () => {
    switch (status.type) {
      case 'indexing_started':
      case 'indexing_progress':
        return 'bg-blue-900/30 border-blue-500/30';
      case 'indexing_completed':
        return 'bg-green-900/30 border-green-500/30';
      case 'indexing_error':
        return 'bg-red-900/30 border-red-500/30';
      default:
        return 'bg-gray-900/30 border-gray-500/30';
    }
  };

  const getStatusTitle = () => {
    switch (status.type) {
      case 'indexing_started':
        return 'Indexing Started';
      case 'indexing_progress':
        return 'Indexing in Progress';
      case 'indexing_completed':
        return 'Indexing Complete';
      case 'indexing_error':
        return 'Indexing Error';
      default:
        return 'Indexing Status';
    }
  };

  const getFolderName = (folderPath) => {
    if (!folderPath) return '';
    const parts = folderPath.split(/[\\/]/);
    return parts[parts.length - 1] || folderPath;
  };

  // Function to calculate gradient color for percentage text
  const getPercentageColor = (percentage) => {
    const progress = Math.max(0, Math.min(100, percentage || 0));
    
    // Red to Yellow to Green transition
    let r, g, b;
    
    if (progress <= 50) {
      // Red to Yellow (0% to 50%)
      const ratio = progress / 50;
      r = 255;
      g = Math.round(255 * ratio);
      b = 0;
    } else {
      // Yellow to Green (50% to 100%)
      const ratio = (progress - 50) / 50;
      r = Math.round(255 * (1 - ratio));
      g = 255;
      b = 0;
    }
    
    return `rgb(${r}, ${g}, ${b})`;
  };

  const percentage = Math.max(0, Math.min(100, status.percentage || 0));
  const percentageColor = getPercentageColor(percentage);

  return (
    <div className={`fixed top-0 left-0 right-0 z-40 border-b backdrop-blur-sm ${getStatusColor()} animate-slideDown`}>
      <div className="max-w-6xl mx-auto px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3 flex-1">
            {getStatusIcon()}
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-1">
                <h3 className="font-semibold text-white text-sm">{getStatusTitle()}</h3>
                {status.folder && (
                  <span className="text-sm text-gray-300 truncate">
                    • {getFolderName(status.folder)}
                  </span>
                )}
              </div>
              
              {status.type === 'indexing_progress' && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-300 truncate mr-4">
                      {status.current_file ? `Processing: ${status.current_file}` : 'Preparing...'}
                    </span>
                    <span className="text-gray-300 whitespace-nowrap">
                      {status.processed || 0} / {status.total || 0} images
                      {status.percentage !== undefined && (
                        <span 
                          className="ml-2 font-mono font-medium"
                          style={{ 
                            color: percentageColor,
                            transition: 'color 1.2s cubic-bezier(0.4, 0, 0.2, 1)'
                          }}
                        >
                          ({percentage.toFixed(1)}%)
                        </span>
                      )}
                    </span>
                  </div>
                  
                  <Progress 
                    value={percentage} 
                    className="h-3 bg-gray-700/30"
                    indicatorClassName="bg-white transition-all duration-1200 ease-out"
                  />
                </div>
              )}
              
              {status.type === 'indexing_completed' && (
                <p className="text-sm text-green-300">
                  {status.message || `Successfully indexed ${status.total_indexed || 0} images. You can now search!`}
                </p>
              )}
              
              {status.type === 'indexing_error' && (
                <p className="text-sm text-red-300">
                  {status.error || 'An error occurred during indexing.'}
                </p>
              )}
              
              {status.type === 'indexing_started' && (
                <p className="text-sm text-blue-300">
                  Starting to index images in the selected folder...
                </p>
              )}
            </div>
          </div>
          
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 text-gray-400 hover:text-white hover:bg-white/10 ml-4 flex-shrink-0"
            onClick={onDismiss}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default IndexingStatusBanner; 