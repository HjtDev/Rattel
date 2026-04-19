import Image from "next/image";
import Navbar from "@/src/components/layout/Navbar";
import Footer from "@/src/components/layout/Footer";
import Hero from "@/src/components/home/Hero";
import FeaturedCourses from "@/src/components/home/FeaturedCourses";
import Categories from "@/src/components/home/Categories";
import Teachers from "@/src/components/home/Teachers";
import Testimonials from "@/src/components/home/Testimonials";
import CallToAction from "@/src/components/home/CallToAction";

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <FeaturedCourses />
        <Categories />
        <Teachers />
        <Testimonials />
        <CallToAction />
      </main>
      <Footer />
    </>
  );
}
