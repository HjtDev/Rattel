"use client";

import { useEffect, useState } from "react";
import { api } from "../api";

interface Link {
    name: string;
    logo: string | null;
    url: string;
}

interface ColumnLink {
    link: Link;
    label: string | null;
    order: number;
}

interface FooterColumn {
    title: string;
    order: number;
    column_links: ColumnLink[];
}

interface SocialMediaLink {
    social_link: {
        platform: string;
        url: string;
    }
    order: number;
}

interface FooterData {
    logo: string;
    description: string;
    rights: string;
    contact_address: string;
    contact_phone: string;
    contact_email: string;
    contact_hours: string;
    columns: FooterColumn[];
    social_media_items: SocialMediaLink[];
}

const FOOTER_CACHE_KEY = "rattel.footer.cache.v1";
const FOOTER_TTL_MS = 1000 * 60 * 5;

let footerMemoryCache: { data: FooterData; updatedAt: number } | null = null;
let footerInFlightPromise: Promise<FooterData> | null = null;
let footerReloadCheckDone = false;

function clearFooterCacheOnReload() {
    if (typeof window === "undefined") return;
    if (footerReloadCheckDone) return;

    const navigationEntry = performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming | undefined;
    const legacyNavigation = performance.navigation;
    const isReload =
        navigationEntry?.type === "reload" ||
        (!!legacyNavigation && legacyNavigation.type === 1);

    if (isReload) {
        footerMemoryCache = null;
        localStorage.removeItem(FOOTER_CACHE_KEY);
    }

    footerReloadCheckDone = true;
}

function readFooterStorageCache(): { data: FooterData; updatedAt: number } | null {
    if (typeof window === "undefined") return null;

    try {
        const raw = localStorage.getItem(FOOTER_CACHE_KEY);
        if (!raw) return null;

        const parsed = JSON.parse(raw) as { data: FooterData; updatedAt: number };
        if (!parsed?.data || typeof parsed?.updatedAt !== "number") return null;

        return parsed;
    } catch {
        return null;
    }
}

function writeFooterStorageCache(data: FooterData, updatedAt: number) {
    if (typeof window === "undefined") return;

    try {
        localStorage.setItem(FOOTER_CACHE_KEY, JSON.stringify({ data, updatedAt }));
    } catch {
        // Ignore storage errors (quota/private mode).
    }
}

async function fetchFooterData(): Promise<FooterData> {
    if (footerInFlightPromise) return footerInFlightPromise;

    footerInFlightPromise = api
        .get("/site/footer/")
        .then((response) => {
            if (!response.data.success || !response.data.footer) {
                throw new Error("Failed to load footer");
            }

            const data = response.data.footer as FooterData;
            const updatedAt = Date.now();

            footerMemoryCache = { data, updatedAt };
            writeFooterStorageCache(data, updatedAt);
            return data;
        })
        .finally(() => {
            footerInFlightPromise = null;
        });

    return footerInFlightPromise;
}

export function useFooter() {
    clearFooterCacheOnReload();

    const initialCache = footerMemoryCache ?? readFooterStorageCache();

    if (!footerMemoryCache && initialCache) {
        footerMemoryCache = initialCache;
    }

    const [footerData, setFooterData] = useState<FooterData | null>(initialCache?.data ?? null);
    const [isLoadingFooter, setIsLoadingFooter] = useState(!initialCache);
    const [footerError, setFooterError] = useState<string | null>(null);

    useEffect(() => {
        let isMounted = true;
        const cache = footerMemoryCache;
        const hasFreshCache = !!cache && Date.now() - cache.updatedAt < FOOTER_TTL_MS;

        if (cache && isMounted) {
            setFooterData(cache.data);
            setIsLoadingFooter(false);
        }

        if (hasFreshCache) {
            return () => {
                isMounted = false;
            };
        }

        fetchFooterData()
            .then((data) => {
                if (!isMounted) return;
                setFooterData(data);
                setFooterError(null);
            })
            .catch((err: { message?: string }) => {
                if (!isMounted) return;
                setFooterError(err?.message || "Failed to load footer");
            })
            .finally(() => {
                if (!isMounted) return;
                setIsLoadingFooter(false);
            });

        return () => {
            isMounted = false;
        };
    }, []);

    return { footerData, isLoadingFooter, footerError };
}
