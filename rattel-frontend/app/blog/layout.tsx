import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "پست های وبلاگ",
  description:
    "مشاهده، جستجو و فیلتر پست های آموزش جامع قرآن شامل حفظ، تجوید، روخوانی و مسابقات قرآنی در اکسیر قرآن.",
  alternates: {
    canonical: "/blog",
  },
  openGraph: {
    title: "پست ها | ExireQuran",
    description:
      "فهرست کامل پست های آموزش قرآن، حفظ، مسابقات و مسیر یادگیری مرحله به مرحله.",
    url: "https://exirequran.ir/blog",
  },
};

export default function CoursesLayout({ children }: { children: React.ReactNode }) {
  return children;
}
