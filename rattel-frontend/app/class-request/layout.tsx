import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "درخواست کلاس خودکار حفظ قرآن",
    description: "با ثبت درخواست، استاد با شما تماس می‌گیرد و یک برنامه حفظ شخصی‌سازی شده برای شما تنظیم می‌کند.",
    robots: { index: true, follow: true },
};

export default function ClassRequestLayout({ children }: { children: React.ReactNode }) {
    return children;
}
