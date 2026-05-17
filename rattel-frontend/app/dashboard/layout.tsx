import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "پنل کاربری",
  description: "پنل کاربری اکسیر قرآن برای مدیریت حساب، دوره ها، تراکنش ها و تیکت ها.",
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

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return children;
}
