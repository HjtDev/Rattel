import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "تولیدات رسانه ای",
  robots: {
    index: true,
    follow: true,
  },
};

export default function CoursesLayout({ children }: { children: React.ReactNode }) {
  return children;
}
