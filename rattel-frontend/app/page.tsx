import HomePage from "@/src/components/home/HomePage";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "خانه",
  description:
    "اکسیر قرآن؛ سامانه آموزش جامع قرآن با دوره های حفظ، روخوانی، تجوید، مسابقات قرآنی و مسیر پیشرفت آموزشی.",
  alternates: {
    canonical: "/",
  },
};

export default function Home() {
    return (
        <HomePage />
    );
}
