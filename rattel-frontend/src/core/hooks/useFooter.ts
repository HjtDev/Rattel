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

export function useFooter() {
    const [footerData, setFooterData] = useState<FooterData | null>(null);
    const [isLoadingFooter, setIsLoadingFooter] = useState(true);
    const [footerError, setFooterError] = useState<string | null>(null);

    useEffect(() => {
        api
            .get("/site/footer/")
            .then((response) => {
                if (response.data.success) {
                    setFooterData(response.data.footer);
                } else {
                    setFooterError("Failed to load footer");
                }
            })
            .catch((err) => {
                setFooterError(err.message || "Failed to load footer");
            })
            .finally(() => {
                setIsLoadingFooter(false);
            });
    }, []);

    return { footerData, isLoadingFooter, footerError };
}
