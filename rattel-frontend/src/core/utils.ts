/**
 * Converts a relative media path to an absolute URL
 * @param path - Relative path from backend (e.g., /media/image.jpg)
 * @returns Absolute URL (e.g., http://localhost:8000/media/image.jpg)
 */
export function getMediaUrl(path: string | null | undefined): string {
    if (!path) return '';
    
    // If already absolute URL, return as-is
    if (path.startsWith('http://') || path.startsWith('https://')) {
        return path;
    }
    
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    // Ensure path starts with /
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    
    return `${baseUrl}${normalizedPath}`;
}
