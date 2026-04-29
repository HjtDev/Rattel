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

/**
 * Checks if a link should be marked as active based on the current pathname
 * @param href - The link href to check
 * @param pathname - Current pathname from usePathname()
 * @returns true if the link should be active
 */
export function isLinkActive(href: string, pathname: string): boolean {
    // Exact match for root paths
    if (href === '/' || href === '/dashboard') {
        return pathname === href;
    }
    
    // For other paths, check if pathname starts with href
    // This handles nested routes like /dashboard/personal-information
    return pathname.startsWith(href);
}
