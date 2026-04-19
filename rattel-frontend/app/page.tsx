import Image from "next/image";
import Navbar from "@/src/components/layout/Navbar";
import Footer from "@/src/components/layout/Footer";
import Landing from "@/src/components/home/Landing";
import Statistics from "@/src/components/home/Statistics";
import PopularCourses from "@/src/components/home/PopularCourses";
import TrendingCourses from "@/src/components/home/TrendingCourses";
import UsersExperience from "@/src/components/home/UsersExperience";
import Advertisement from "@/src/components/home/Advertisement";

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        <Landing />
        <Statistics />
        <PopularCourses />
        <Advertisement />
        <TrendingCourses />
        <UsersExperience />
      </main>
      <Footer />
    </>
  );
}
