import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "نماد های اعتماد",
  description:
    "نماد های اعتماد سایت اکسیر قرآن",
  alternates: {
    canonical: "/trust",
  },
  openGraph: {
    title: "نماد های اعتماد | ExireQuran",
    description:
      "فهرست کامل دوره های آموزش قرآن، حفظ، مسابقات و مسیر یادگیری مرحله به مرحله.",
    url: "https://exirequran.ir/trust",
  },
};

export default function CoursesLayout({ children }: { children: React.ReactNode }) {
  return children;
}
