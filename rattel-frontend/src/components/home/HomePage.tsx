"use client";

import { useMainPage } from "@/src/core/hooks/useMainPage";
import Landing from "./Landing";
import Statistics from "./Statistics";
import PopularCourses from "./PopularCourses";
import TrendingCourses from "./TrendingCourses";
import UsersExperience from "./UsersExperience";
import Advertisement from "./Advertisement";
import DualChoice from "./DualChoice";
import TopTeachers from "./TopTeachers";
import ImagedLinks from "./ImagedLinks";
import CourseDemo from "./CourseDemo";
import InformationBoxes from "./InformationBoxes";
import FAQ from "./FAQ";

export default function HomePage() {
    const {
        landingData,
        statsData,
        advertisementData,
        dualChoicesData,
        userExperienceData,
        topTeachersData,
        imagedLinksData,
        coursesDemoData,
        informationBoxesData,
        isLoadingMainPage,
        error
    } = useMainPage();

    if (error) {
        return (
            <main>
                <div style={{ padding: '2rem', textAlign: 'center' }}>
                    <p>خطا در بارگذاری اطلاعات: {error}</p>
                </div>
            </main>
        );
    }

    return (
        <main>
            <Landing data={landingData} isLoading={isLoadingMainPage} />
            <Statistics data={statsData} isLoading={isLoadingMainPage} />
            <PopularCourses />
            <DualChoice data={dualChoicesData} isLoading={isLoadingMainPage} />
            <Advertisement data={advertisementData} isLoading={isLoadingMainPage} />
            <TrendingCourses />
            <UsersExperience data={userExperienceData} isLoading={isLoadingMainPage} />
            <TopTeachers />
            <ImagedLinks data={imagedLinksData} isLoading={isLoadingMainPage} />
            <CourseDemo />
            <InformationBoxes data={informationBoxesData} isLoading={isLoadingMainPage} />
            <FAQ />
        </main>
    );
}
