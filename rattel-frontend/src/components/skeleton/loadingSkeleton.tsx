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
        // Convert width to responsive value if it's too large
        let responsiveWidth = width;
        if (typeof width === 'number' && width > 0) {
            // If width is larger than 90% of typical mobile viewport (360px * 0.9 = 324px)
            responsiveWidth = width > 324 ? `min(${width}px, 90vw)` : `${width}px`;
        } else if (typeof width === 'string' && width.endsWith('px')) {
            const numericWidth = parseInt(width);
            if (numericWidth > 324) {
                responsiveWidth = `min(${width}, 90vw)`;
            }
        }

        return (
            <>
                {Array.from({ length: count }).map((_, index) => (
                    <div
                        key={index}
                        className="skeleton-box mx-1"
                        style={{
                            width: responsiveWidth,
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
