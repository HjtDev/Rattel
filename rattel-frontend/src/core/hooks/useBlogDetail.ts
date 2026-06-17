"use client";

import { useEffect, useState } from "react";
import { api } from "../api";
import type { BlogCategory, BlogTag, BlogUser } from "./useBlogs";

export interface BlogComment {
  id: number;
  user: BlogUser;
  created_at: string;
  content: string;
  reply_to: number | null;
  replies: BlogComment[];
}

export interface BlogDetail {
  id: string;
  title: string;
  slug: string;
  short_description: string;
  description: string;
  conclusion: string;
  thumbnail: string | null;
  view_count: number;
  author: BlogUser;
  ttr: number;
  category: BlogCategory | null;
  tags: BlogTag[];
  is_saved: boolean;
  time_since: string;
  comments: BlogComment[];
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export function useBlogDetail(postSlug: string | null) {
  const [blogDetail, setBlogDetail] = useState<BlogDetail | null>(null);
  const [isLoadingBlogDetail, setIsLoadingBlogDetail] = useState(false);
  const [blogDetailError, setBlogDetailError] = useState<string | null>(null);

  useEffect(() => {
    if (!postSlug) return;

    setIsLoadingBlogDetail(true);
    setBlogDetailError(null);

    api
      .get(`/blog/${postSlug}/`)
      .then((response) => {
        if (response.data.success) {
          setBlogDetail(response.data.post);
        } else {
          setBlogDetailError("Failed to load blog details");
        }
      })
      .catch((err) => {
        setBlogDetailError(err.message || "Failed to load blog details");
      })
      .finally(() => {
        setIsLoadingBlogDetail(false);
      });
  }, [postSlug]);

  return { blogDetail, setBlogDetail, isLoadingBlogDetail, blogDetailError };
}

export async function sendBlogViewCount(postSlug: string): Promise<boolean> {
  try {
    const response = await api.get(`/blog/${postSlug}/view-count/?t=${Date.now()}`);
    return !!response.data?.success;
  } catch {
    return false;
  }
}
