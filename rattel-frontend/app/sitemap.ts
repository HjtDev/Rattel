import type { MetadataRoute } from "next";

const baseUrl = "https://exirequran.ir";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();

  return [
    {
      url: `${baseUrl}/`,
      lastModified: now,
      changeFrequency: "daily",
      priority: 1,
    },
    {
      url: `${baseUrl}/courses`,
      lastModified: now,
      changeFrequency: "daily",
      priority: 0.9,
    },
  ];
}
