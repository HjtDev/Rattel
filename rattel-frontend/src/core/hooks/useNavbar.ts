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
    items: Col1Items;
}

interface NavbarMegaMenuCol2 extends NavbarMegaMenuCol1 {
    items: Col2Items;
}

interface NavbarMegaMenuCol3 extends NavbarMegaMenuCol2 {
    items: Col3Items;
}

interface NavbarMegaMenuBanner {
    image: string,
    title: string,
    link: string
}

interface NavbarData {
    navbar_logo: string;
    navbar_links: NavbarLink[];
    col1: NavbarMegaMenuCol1[];
    col2: NavbarMegaMenuCol2[];
    col3: NavbarMegaMenuCol3[];
    banner: NavbarMegaMenuBanner;
    notification: string;
}

export function useNavbar() {
    const [navbarData, setNavbarData] = useState<NavbarData | null>(null);
    const [isLoadingNavbar, setIsLoadingNavbar] = useState(true);
    const [navbarError, setNavbarError] = useState<string | null>(null);

    useEffect(() => {
        api
            .get("/site/navbar/")
            .then((response) => {
                if (response.data.success) {
                    setNavbarData(response.data.navbar);
                } else {
                    setNavbarError("Failed to load navbar");
                }
            })
            .catch((err) => {
                setNavbarError(err.message || "Failed to load navbar");
            })
            .finally(() => {
                setIsLoadingNavbar(false);
            });
    }, []);

    return {navbarData, isLoadingNavbar, navbarError};
}
