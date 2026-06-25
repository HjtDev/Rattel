import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: [
          "/dashboard",
          "/dashboard/*",
          "/auth/login",
          "/auth/register",
          "/auth/verify",
          "/cart",
          "/payment",
          "/payment/*",
          "/quiz/admin",
          "/quiz/admin/*",
        ],
      },
    ],
    sitemap: "https://exirequran.ir/sitemap.xml",
    host: "https://exirequran.ir",
  };
}
