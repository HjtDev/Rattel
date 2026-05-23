"use client";

import { useEffect, useState } from "react";
import { api } from "../api";
import type { BlogPostCard } from "./useBlogs";

export function useSavedBlogs() {
  const [savedBlogs, setSavedBlogs] = useState<BlogPostCard[] | null>(null);
  const [isLoadingSavedBlogs, setIsLoadingSavedBlogs] = useState(false);
  const [savedBlogsError, setSavedBlogsError] = useState<string | null>(null);

  const fetchSavedBlogs = async () => {
    setIsLoadingSavedBlogs(true);
    setSavedBlogsError(null);

    try {
      const response = await api.get("/blog/saved-posts/");
      if (response.data.success) {
        setSavedBlogs(response.data.posts);
      } else {
        setSavedBlogsError("Failed to load saved blog posts");
      }
    } catch (err: any) {
      setSavedBlogsError(err.message || "Failed to load saved blog posts");
    } finally {
      setIsLoadingSavedBlogs(false);
    }
  };

  useEffect(() => {
    fetchSavedBlogs();
  }, []);

  return {
    savedBlogs,
    isLoadingSavedBlogs,
    savedBlogsError,
    refetchSavedBlogs: fetchSavedBlogs,
  };
}

export async function toggleSaveBlog(postId: string): Promise<{ success: boolean; is_saved: boolean; message: string }> {
  try {
    const response = await api.post(`/blog/${postId}/toggle-save/`);
    return {
      success: response.data.success,
      is_saved: response.data.is_saved,
      message: response.data.message,
    };
  } catch (err: any) {
    return {
      success: false,
      is_saved: false,
      message: err.response?.data?.message || "خطا در ذخیره پست",
    };
  }
}
