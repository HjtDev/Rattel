"use client";

import {useEffect, useState} from "react";
import {api} from "../api";

interface NavbarLink {
    name: string;
    logo: string | null;
    url: string;
}

interface Col1Items {
    link: NavbarLink;
    label: string;
    order: number;
}

interface Col2Items extends Col1Items {
    description: string;
}

interface Col3Items extends Col2Items {
    icon: string;
}

interface NavbarMegaMenuCol1 {
    title: string;
    items: Col1Items[];
}

interface NavbarMegaMenuCol2 extends NavbarMegaMenuCol1 {
    items: Col2Items[];
}

interface NavbarMegaMenuCol3 extends NavbarMegaMenuCol2 {
    items: Col3Items[];
}

interface NavbarMegaMenuBanner {
    image: string,
    title: string,
    link: string
}

interface NavbarData {
    navbar_logo: string;
    navbar_links: NavbarLink[];
    col1: NavbarMegaMenuCol1;
    col2: NavbarMegaMenuCol2;
    col3: NavbarMegaMenuCol3;
    banner: NavbarMegaMenuBanner;
    notification: string;
}

const NAVBAR_CACHE_KEY = "rattel.navbar.cache.v1";
const NAVBAR_TTL_MS = 1000 * 60 * 5;

let navbarMemoryCache: { data: NavbarData; updatedAt: number } | null = null;
let navbarInFlightPromise: Promise<NavbarData> | null = null;
let navbarReloadCheckDone = false;

function clearNavbarCacheOnReload() {
    if (typeof window === "undefined") return;
    if (navbarReloadCheckDone) return;

    const navigationEntry = performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming | undefined;
    const legacyNavigation = performance.navigation;
    const isReload =
        navigationEntry?.type === "reload" ||
        (!!legacyNavigation && legacyNavigation.type === 1);

    if (isReload) {
        navbarMemoryCache = null;
        localStorage.removeItem(NAVBAR_CACHE_KEY);
    }

    navbarReloadCheckDone = true;
}

function readNavbarStorageCache(): { data: NavbarData; updatedAt: number } | null {
    if (typeof window === "undefined") return null;

    try {
        const raw = localStorage.getItem(NAVBAR_CACHE_KEY);
        if (!raw) return null;

        const parsed = JSON.parse(raw) as { data: NavbarData; updatedAt: number };
        if (!parsed?.data || typeof parsed?.updatedAt !== "number") return null;

        return parsed;
    } catch {
        return null;
    }
}

function writeNavbarStorageCache(data: NavbarData, updatedAt: number) {
    if (typeof window === "undefined") return;

    try {
        localStorage.setItem(NAVBAR_CACHE_KEY, JSON.stringify({ data, updatedAt }));
    } catch {
        // Ignore storage errors (quota/private mode).
    }
}

async function fetchNavbarData(): Promise<NavbarData> {
    if (navbarInFlightPromise) return navbarInFlightPromise;

    navbarInFlightPromise = api
        .get("/site/navbar/")
        .then((response) => {
            if (!response.data.success || !response.data.navbar) {
                throw new Error("Failed to load navbar");
            }

            const data = response.data.navbar as NavbarData;
            const updatedAt = Date.now();

            navbarMemoryCache = { data, updatedAt };
            writeNavbarStorageCache(data, updatedAt);
            return data;
        })
        .finally(() => {
            navbarInFlightPromise = null;
        });

    return navbarInFlightPromise;
}

export function useNavbar() {
    clearNavbarCacheOnReload();
    const [navbarData, setNavbarData] = useState<NavbarData | null>(null);
    const [isLoadingNavbar, setIsLoadingNavbar] = useState(true);
    const [navbarError, setNavbarError] = useState<string | null>(null);

    useEffect(() => {
        let isMounted = true;
        const cache = navbarMemoryCache ?? readNavbarStorageCache();

        if (!navbarMemoryCache && cache) {
            navbarMemoryCache = cache;
        }

        const hasFreshCache = !!cache && Date.now() - cache.updatedAt < NAVBAR_TTL_MS;

        if (cache && isMounted) {
            setNavbarData(cache.data);
            setIsLoadingNavbar(false);
        }

        if (hasFreshCache) {
            return () => {
                isMounted = false;
            };
        }

        fetchNavbarData()
            .then((data) => {
                if (!isMounted) return;
                setNavbarData(data);
                setNavbarError(null);
            })
            .catch((err: { message?: string }) => {
                if (!isMounted) return;
                setNavbarError(err?.message || "Failed to load navbar");
            })
            .finally(() => {
                if (!isMounted) return;
                setIsLoadingNavbar(false);
            });

        return () => {
            isMounted = false;
        };
    }, []);

    return {navbarData, isLoadingNavbar, navbarError};
}
