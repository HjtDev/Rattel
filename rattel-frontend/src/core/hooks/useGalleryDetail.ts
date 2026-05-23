"use client";

import { useEffect, useState } from "react";
import { api } from "../api";

export interface GalleryContentItem {
  id: number;
  content_type: "image" | "video" | "audio" | "embed";
  file: string | null;
  embed_code: string;
  order: number;
  created_at: string;
  updated_at: string;
}

export interface GalleryDetail {
  id: string;
  title: string;
  thumbnail: string | null;
  content: GalleryContentItem[];
  created_at: string;
  updated_at: string;
}

export function useGalleryDetail(galleryId: string | null) {
  const [galleryDetail, setGalleryDetail] = useState<GalleryDetail | null>(null);
  const [isLoadingGalleryDetail, setIsLoadingGalleryDetail] = useState(false);
  const [galleryDetailError, setGalleryDetailError] = useState<string | null>(null);

  useEffect(() => {
    if (!galleryId) {
      setGalleryDetail(null);
      return;
    }

    setIsLoadingGalleryDetail(true);
    setGalleryDetailError(null);

    api
      .get(`/gallery/${galleryId}/`)
      .then((response) => {
        if (response.data.success) {
          setGalleryDetail(response.data.item);
        } else {
          setGalleryDetailError("Failed to load gallery details");
        }
      })
      .catch((error) => {
        setGalleryDetailError(error.message || "Failed to load gallery details");
      })
      .finally(() => {
        setIsLoadingGalleryDetail(false);
      });
  }, [galleryId]);

  return { galleryDetail, setGalleryDetail, isLoadingGalleryDetail, galleryDetailError };
}
