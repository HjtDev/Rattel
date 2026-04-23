import React from 'react';
import './skeleton.css';

interface LoadingSkeletonProps {
  width?: string | number;
  height?: string | number;
  isLoading: boolean;
  Content: () => React.ReactNode;
  count?: number;
}

export default function LoadingSkeleton({ 
  width = '100%', 
  height = '20px', 
  isLoading, 
  Content,
  count = 1 
}: LoadingSkeletonProps) {
    if (isLoading) {
        return (
            <>
                {Array.from({ length: count }).map((_, index) => (
                    <div
                        key={index}
                        className="skeleton-box"
                        style={{
                            width: typeof width === 'number' ? `${width}px` : width,
                            height: typeof height === 'number' ? `${height}px` : height,
                        }}
                    />
                ))}
            </>
        );
    } else {
        return <Content />
    }
}
