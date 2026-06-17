import type { MetadataRoute } from "next";

// force-dynamic: skip build-time pre-render (backend not running during docker build).
// Fetch-level revalidate below handles caching so the backend is hit at most once per day.
export const dynamic = "force-dynamic";

const baseUrl = "https://exirequran.ir";

// Server-side only: use internal Docker network URL, not the browser-facing public URL.
const apiBase =
  process.env.INTERNAL_API_URL ||
  (process.env.NEXT_PUBLIC_API_URL ?? "") + "/api/v1";

async function fetchBlogSlugs(): Promise<
  { slug: string; published_at: string | null; created_at: string }[]
> {
  const url = `${apiBase}/blog/?count=1000&page=1`;
  try {
    const res = await fetch(url, { next: { revalidate: 86400 } });
    if (!res.ok) {
      console.error(`[sitemap] blog fetch failed: ${res.status} ${res.statusText} — ${url}`);
      return [];
    }
    const data = await res.json();
    console.log(`[sitemap] blog: fetched ${data.posts?.length ?? 0} posts`);
    return data.posts ?? [];
  } catch (err) {
    console.error(`[sitemap] blog fetch threw:`, err, `— url: ${url}`);
    return [];
  }
}

async function fetchCourseIds(): Promise<{ id: string }[]> {
  const url = `${apiBase}/courses/?count=1000&page=1`;
  try {
    const res = await fetch(url, { next: { revalidate: 86400 } });
    if (!res.ok) {
      console.error(`[sitemap] courses fetch failed: ${res.status} ${res.statusText} — ${url}`);
      return [];
    }
    const data = await res.json();
    console.log(`[sitemap] courses: fetched ${data.courses?.length ?? 0} courses`);
    return data.courses ?? [];
  } catch (err) {
    console.error(`[sitemap] courses fetch threw:`, err, `— url: ${url}`);
    return [];
  }
}

const staticPages: MetadataRoute.Sitemap = [
  {
    url: `${baseUrl}/`,
    changeFrequency: "daily",
    priority: 1.0,
  },
  {
    url: `${baseUrl}/courses`,
    changeFrequency: "daily",
    priority: 0.9,
  },
  {
    url: `${baseUrl}/blog`,
    changeFrequency: "daily",
    priority: 0.9,
  },
  {
    url: `${baseUrl}/gallery`,
    changeFrequency: "weekly",
    priority: 0.8,
  },
  {
    url: `${baseUrl}/subscriptions`,
    changeFrequency: "monthly",
    priority: 0.8,
  },
  {
    url: `${baseUrl}/about-us`,
    changeFrequency: "monthly",
    priority: 0.6,
  },
  {
    url: `${baseUrl}/work-with-us`,
    changeFrequency: "monthly",
    priority: 0.5,
  },
  {
    url: `${baseUrl}/class-request`,
    changeFrequency: "monthly",
    priority: 0.5,
  },
];

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const [posts, courses] = await Promise.all([
    fetchBlogSlugs(),
    fetchCourseIds(),
  ]);

  const blogEntries: MetadataRoute.Sitemap = posts.map((post) => ({
    url: `${baseUrl}/blog/${post.slug}`,
    lastModified: post.published_at ?? post.created_at,
    changeFrequency: "weekly",
    priority: 0.7,
  }));

  const courseEntries: MetadataRoute.Sitemap = courses.map((course) => ({
    url: `${baseUrl}/courses/${course.id}`,
    changeFrequency: "monthly",
    priority: 0.8,
  }));

  return [...staticPages, ...blogEntries, ...courseEntries];
}
