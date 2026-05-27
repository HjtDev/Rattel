import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "جزئیات پست",
  description: "جزئیات کامل پست در اکسیر قرآن.",
  robots: {
    index: true,
    follow: true,
  },
};

export default function CourseDetailLayout({ children }: { children: React.ReactNode }) {
  return children;
}
