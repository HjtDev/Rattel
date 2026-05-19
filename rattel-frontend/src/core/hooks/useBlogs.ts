"use client";

import { useEffect, useState } from "react";
import { api } from "../api";

export interface BlogUser {
  name: string;
  profile_picture: string | null;
}

export interface BlogCategory {
  id?: number;
  name: string;
  slug: string;
}

export interface BlogTag {
  id?: number;
  name: string;
  slug: string;
}

export interface BlogPostCard {
  id: string;
  title: string;
  slug: string;
  short_description: string;
  thumbnail: string | null;
  view_count: number;
  author: BlogUser;
  ttr: number;
  category: BlogCategory | null;
  tags: BlogTag[];
  is_saved: boolean;
  published_at: string | null;
  created_at: string;
}

export interface BlogsResponse {
  posts: BlogPostCard[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number | null;
  has_next: boolean | null;
  has_previous: boolean | null;
}

export type BlogSortOption = "newest" | "oldest" | "most_views" | "least_views" | "most_read";

export interface BlogListParams {
  page?: number;
  count?: number;
  sort?: BlogSortOption;
  category?: string;
  tag?: string;
  author?: string;
  search?: string;
}

export function useBlogs(params: BlogListParams = {}) {
  const [blogsData, setBlogsData] = useState<BlogsResponse | null>(null);
  const [isLoadingBlogs, setIsLoadingBlogs] = useState(true);
  const [blogsError, setBlogsError] = useState<string | null>(null);

  const {
    page = 1,
    count = 12,
    sort,
    category,
    tag,
    author,
    search,
  } = params;

  useEffect(() => {
    setIsLoadingBlogs(true);
    setBlogsError(null);

    const query = new URLSearchParams();
    query.set("page", String(page));
    query.set("count", String(count));
    if (sort) query.set("sort", sort);
    if (category) query.set("category", category);
    if (tag) query.set("tag", tag);
    if (author) query.set("author", author);
    if (search) query.set("search", search);

    api
      .get(`/blog/?${query.toString()}`)
      .then((response) => {
        if (response.data.success) {
          setBlogsData({
            posts: response.data.posts,
            total: response.data.total,
            page: response.data.page,
            page_size: response.data.page_size,
            total_pages: response.data.total_pages,
            has_next: response.data.has_next,
            has_previous: response.data.has_previous,
          });
        } else {
          setBlogsData({
            posts: [],
            total: 0,
            page,
            page_size: count,
            total_pages: 0,
            has_next: false,
            has_previous: false,
          });
          setBlogsError("Failed to load blog posts");
        }
      })
      .catch((err) => {
        setBlogsData({
          posts: [],
          total: 0,
          page,
          page_size: count,
          total_pages: 0,
          has_next: false,
          has_previous: false,
        });
        setBlogsError(err.message || "Failed to load blog posts");
      })
      .finally(() => {
        setIsLoadingBlogs(false);
      });
  }, [page, count, sort, category, tag, author, search]);

  return { blogsData, isLoadingBlogs, blogsError };
}

export function useBlogMeta() {
  const [categories, setCategories] = useState<BlogCategory[]>([]);
  const [tags, setTags] = useState<BlogTag[]>([]);

  useEffect(() => {
    api
      .get("/blog/meta/")
      .then((response) => {
        if (response.data.success) {
          setCategories(response.data.categories || []);
          setTags(response.data.tags || []);
        }
      })
      .catch(() => undefined);
  }, []);

  return { categories, tags };
}
