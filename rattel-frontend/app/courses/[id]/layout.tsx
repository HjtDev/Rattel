import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "جزئیات دوره",
  description: "جزئیات کامل دوره، سرفصل ها، مدرس، قیمت و مسیر پیشرفت یادگیری در اکسیر قرآن.",
  robots: {
    index: true,
    follow: true,
  },
};

export default function CourseDetailLayout({ children }: { children: React.ReactNode }) {
  return children;
}
