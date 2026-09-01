import type {MetadataRoute} from "next";

export default function robots(): MetadataRoute.Robots {
    const disallowedPaths = [
        "/dashboard",
        "/auth/login",
        "/auth/register",
        "/auth/verify",
        "/cart",
        "/payment",
        "/quiz/admin",
    ];

    return {
        rules: [
            {
                userAgent: "*",
                allow: "/",
                disallow: disallowedPaths,
            },
            {
                // Explicit permissions for major AI Search Agents and LLM Crawlers
                userAgent: [
                    "GPTBot",
                    "ChatGPT-User",
                    "PerplexityBot",
                    "ClaudeBot",
                    "AnthropicAI",
                    "Google-Extended",
                    "Cohere-ai",
                ],
                allow: "/",
                disallow: disallowedPaths,
            },
        ],
        sitemap: "https://exirequran.ir/sitemap.xml",
    };
}
