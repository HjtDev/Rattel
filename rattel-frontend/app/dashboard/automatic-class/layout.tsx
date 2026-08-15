import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "سامانه حفظ مجازی",
    robots: { index: false, follow: false },
};

export default function AutomaticClassLayout({ children }: { children: React.ReactNode }) {
    return children;
}
