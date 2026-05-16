import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "احراز هویت",
  description: "ورود و ثبت نام در اکسیر قرآن با کد تایید یک بار مصرف.",
  robots: {
    index: false,
    follow: false,
    nocache: true,
  },
};

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return children;
}
