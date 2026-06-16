import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "پنل مدیریت کلاس",
    robots: { index: false, follow: false },
};

export default function AdminClassLayout({ children }: { children: React.ReactNode }) {
    return children;
}
