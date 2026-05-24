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

/**
 * Converts backend course difficulty value to a user-friendly label
 * @param difficulty - Course Difficulty value
 * @returns Course Difficulty Label
 */
export const getDifficultyLabel = (difficulty: string) => {
    const labels: Record<string, string> = {
        beginner: "مقدماتی",
        intermediate: "متوسطه",
        advanced: "پیشرفته"
    };
    return labels[difficulty] || difficulty;
};

/**
 * Converts backend course category value to a user-friendly label
 * @param category - Course Category value
 * @returns Course Category Label
 */
export const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
        telavat: "تلاوت",
        tahfiz: "تحفیظ",
        tadabbor: "تدبر"
    };
    return labels[category] || category;
};

/**
 * Share current page with Web Share API on supported devices.
 * Falls back to copying the current URL to clipboard on desktop.
 */
export async function shareCurrentPage(params: { title?: string; text?: string } = {}): Promise<"shared" | "copied" | "failed"> {
    if (typeof window === "undefined") return "failed";

    const url = window.location.href;
    const { title, text } = params;

    if (navigator.share) {
        try {
            await navigator.share({ title, text, url });
            return "shared";
        } catch {
            return "failed";
        }
    }

    try {
        await navigator.clipboard.writeText(url);
        return "copied";
    } catch {
        return "failed";
    }
}
