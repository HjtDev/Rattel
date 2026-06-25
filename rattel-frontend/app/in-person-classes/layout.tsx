import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "کلاس‌های حضوری",
  description:
    "مشاهده و ثبت‌نام در کلاس‌های حضوری آموزش قرآن در اکسیر قرآن؛ دوره‌های حفظ، تجوید و روخوانی با اساتید برجسته.",
  alternates: {
    canonical: "/in-person-classes",
  },
  openGraph: {
    title: "کلاس‌های حضوری قرآن | ExireQuran",
    description:
      "فهرست کلاس‌های حضوری قرآن شامل حفظ، تجوید و روخوانی و ثبت‌نام آنلاین در اکسیر قرآن.",
    url: "https://exirequran.ir/in-person-classes",
  },
};

export default function InPersonClassesLayout({ children }: { children: React.ReactNode }) {
  return children;
}
