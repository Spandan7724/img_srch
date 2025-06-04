"use client";

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Copy, FolderOpen, ChevronRight } from 'lucide-react';

const getScoreColor = (score) => {
  const scorePercent = score * 100;
  if (scorePercent >= 90) return 'text-emerald-400';
  if (scorePercent >= 80) return 'text-green-400';
  if (scorePercent >= 70) return 'text-lime-400';
  if (scorePercent >= 60) return 'text-yellow-400';
  if (scorePercent >= 50) return 'text-amber-400';
  return 'text-orange-400';
};

const ResultCard = ({
  result,
  index,
  loaded,
  onLoad,
  onClick,
  onCopyPath,
  openInExplorer,
}) => (
  <Card
    className="bg-gray-900/80 backdrop-blur-sm border-gray-800 overflow-hidden transform hover:scale-[1.02] hover:shadow-xl hover:shadow-blue-900/20 transition-all duration-300 cursor-pointer group rounded-xl"
    onClick={onClick}
  >
    <CardContent className="p-0">
      <div className="relative">
        {!loaded && (
          <div className="w-full h-52 bg-gradient-to-br from-gray-800 to-gray-900 animate-pulse" />
        )}

        <img
          src={result.full_url}
          alt={`Search result ${index + 1}`}
          className={`w-full h-52 object-cover transition-all duration-500 ${loaded ? 'opacity-100' : 'opacity-0'}`}
          onLoad={onLoad}
        />

        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />

        <div className="absolute inset-0 bg-blue-900/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

        <div className="absolute top-3 right-3 bg-black/70 backdrop-blur-sm rounded-full px-2 py-1 text-sm">
          <span className="font-medium">Match: </span>
          <span className={getScoreColor(result.score)}>
            {(result.score * 100).toFixed(1)}%
          </span>
        </div>

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
            {result.path.split(/[\\/]/).pop()}
          </p>
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0.5 text-gray-400 hover:text-white rounded-full"
              onClick={onCopyPath}
            >
              <Copy className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0.5 text-gray-400 hover:text-white rounded-full"
              onClick={openInExplorer}
            >
              <FolderOpen className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
);

export default ResultCard;
