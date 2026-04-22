import Image from "next/image";
import Navbar from "@/src/components/layout/Navbar";
import Footer from "@/src/components/layout/Footer";
import Landing from "@/src/components/home/Landing";
import Statistics from "@/src/components/home/Statistics";
import PopularCourses from "@/src/components/home/PopularCourses";
import TrendingCourses from "@/src/components/home/TrendingCourses";
import UsersExperience from "@/src/components/home/UsersExperience";
import Advertisement from "@/src/components/home/Advertisement";
import DualChoice from "@/src/components/home/DualChoice";
import TopTeachers from "@/src/components/home/TopTeachers";
import ImagedLinks from "@/src/components/home/ImagedLinks";
import CourseDemo from "@/src/components/home/CourseDemo";
import InformationBoxes from "@/src/components/home/InformationBoxes";
import FAQ from "@/src/components/home/FAQ";

export default function Home() {
    return (
        <>
            <Navbar/>
            <main>
                <Landing/>
                <Statistics/>
                <PopularCourses/>
                <DualChoice />
                <Advertisement/>
                <TrendingCourses/>
                <UsersExperience/>
                <TopTeachers />
                <ImagedLinks />
                <CourseDemo />
                <InformationBoxes />
                <FAQ />
            </main>
            <Footer/>
        </>
    );
}
