"use client";
import React from 'react';
import { Button } from '@/components/ui/button';
import { Copy, FolderOpen, Maximize2, X } from 'lucide-react';

const ImageModal = ({ image, onClose, onCopy, onOpenExplorer, onOpenViewer, getScoreColor }) => {
  if (!image) return null;
  return (
    <div
      className="fixed inset-0 bg-black/95 backdrop-blur-sm z-50 flex items-center justify-center"
      onClick={onClose}
    >
      <div
        className="max-w-5xl w-full max-h-[90vh] p-4 relative"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          className="absolute top-0 right-0 -mt-10 -mr-10 bg-white/10 backdrop-blur-sm p-2 rounded-full hover:bg-white/20 transition-all"
          onClick={onClose}
        >
          <X className="h-5 w-5" />
        </button>
        <div className="relative rounded-lg overflow-hidden shadow-2xl ring-1 ring-white/10 animate-fadeIn">
          <img
            src={image.full_url}
            alt="Selected result"
            className="max-w-full max-h-[75vh] object-contain rounded-lg w-full"
            onDoubleClick={(e) => {
              e.stopPropagation();
              onOpenViewer(image.path);
            }}
          />
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 to-transparent p-4">
            <div className="flex items-center justify-between">
              <p className="text-xl font-semibold">
                Similarity Score:
                <span className={`ml-2 ${getScoreColor(image.score)}`}>
                  {(image.score * 100).toFixed(2)}%
                </span>
              </p>
              <Button
                variant="outline"
                size="sm"
                className="bg-white/10 border-white/20 hover:bg-white/20"
                onClick={(e) => {
                  e.stopPropagation();
                  onOpenViewer(image.path);
                }}
              >
                <Maximize2 className="h-4 w-4 mr-2" />
                Open in Viewer
              </Button>
            </div>
            <div className="flex items-center gap-2 bg-black/50 backdrop-blur-sm rounded-lg p-3 mt-3">
              <p className="text-gray-300 text-sm font-mono">{image.path}</p>
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 p-0 rounded-full text-gray-400 hover:text-white hover:bg-white/10"
                  onClick={(e) => {
                    e.stopPropagation();
                    onCopy(image.path);
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
                    onOpenExplorer(image.path);
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
  );
};

export default ImageModal;
