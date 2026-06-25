import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "آزمون‌های قرآنی",
  description:
    "شرکت در آزمون‌های تعاملی قرآن در اکسیر قرآن؛ مسابقه، سنجش میزان حفظ، تجوید و دانش قرآنی با تابلوی امتیازات.",
  alternates: {
    canonical: "/quiz",
  },
  openGraph: {
    title: "آزمون‌های قرآنی | ExireQuran",
    description:
      "فهرست آزمون‌های قرآنی، سنجش دانش حفظ و تجوید و مشاهده جدول برترین‌ها در اکسیر قرآن.",
    url: "https://exirequran.ir/quiz",
  },
};

export default function QuizLayout({ children }: { children: React.ReactNode }) {
  return children;
}
