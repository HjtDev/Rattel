import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "دوره های قرآن",
  description:
    "مشاهده، جستجو و فیلتر دوره های آموزش جامع قرآن شامل حفظ، تجوید، روخوانی و مسابقات قرآنی در اکسیر قرآن.",
  alternates: {
    canonical: "/courses",
  },
  openGraph: {
    title: "دوره های قرآن | ExireQuran",
    description:
      "فهرست کامل دوره های آموزش قرآن، حفظ، مسابقات و مسیر یادگیری مرحله به مرحله.",
    url: "https://exirequran.ir/courses",
  },
};

export default function CoursesLayout({ children }: { children: React.ReactNode }) {
  return children;
}
