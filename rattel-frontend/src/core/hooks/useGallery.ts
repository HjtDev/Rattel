"use client";

import { useEffect, useState } from "react";
import { api } from "../api";

export interface GalleryListItem {
  id: string;
  title: string;
  thumbnail: string | null;
}

export interface GalleryListResponse {
  items: GalleryListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number | null;
  has_next: boolean | null;
  has_previous: boolean | null;
}

export function useGallery(page = 1, count = 12) {
  const [galleryData, setGalleryData] = useState<GalleryListResponse | null>(null);
  const [isLoadingGallery, setIsLoadingGallery] = useState(true);
  const [galleryError, setGalleryError] = useState<string | null>(null);

  useEffect(() => {
    setIsLoadingGallery(true);
    setGalleryError(null);

    api
      .get(`/gallery/?page=${page}&count=${count}`)
      .then((response) => {
        if (response.data.success) {
          setGalleryData({
            items: response.data.items,
            total: response.data.total,
            page: response.data.page,
            page_size: response.data.page_size,
            total_pages: response.data.total_pages,
            has_next: response.data.has_next,
            has_previous: response.data.has_previous,
          });
        } else {
          setGalleryData({
            items: [],
            total: 0,
            page,
            page_size: count,
            total_pages: 0,
            has_next: false,
            has_previous: false,
          });
          setGalleryError("Failed to load gallery items");
        }
      })
      .catch((error) => {
        setGalleryData({
          items: [],
          total: 0,
          page,
          page_size: count,
          total_pages: 0,
          has_next: false,
          has_previous: false,
        });
        setGalleryError(error.message || "Failed to load gallery items");
      })
      .finally(() => {
        setIsLoadingGallery(false);
      });
  }, [page, count]);

  return { galleryData, isLoadingGallery, galleryError, setGalleryData };
}
