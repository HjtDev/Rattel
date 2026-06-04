import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "خرید اشتراک",
  robots: {
    index: true,
    follow: true,
  },
};

export default function AboutUsLayout({ children }: { children: React.ReactNode }) {
  return children;
}
