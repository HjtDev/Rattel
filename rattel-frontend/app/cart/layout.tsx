import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "سبد خرید",
  description:
    "سبد خرید کاربر شامل دوره ها و خدمات برای تسویه حساب",
  alternates: {
    canonical: "/cart",
  },
  openGraph: {
    title: "سبد خرید | ExireQuran",
    description:
      "سبد خرید کاربر شامل دوره ها و خدمات برای تسویه حساب",
    url: "https://exirequran.ir/cart",
  },
  robots: {
    index: false,
    follow: false,
    nocache: true,
    googleBot: {
      index: false,
      follow: false,
      noimageindex: true,
      "max-snippet": -1,
    },
  },
};

export default function CoursesLayout({ children }: { children: React.ReactNode }) {
  return children;
}
