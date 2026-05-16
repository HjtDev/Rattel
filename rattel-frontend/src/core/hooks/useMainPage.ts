"use client";

import { useEffect, useState } from "react";
import { api } from "../api";

interface Link {
    name: string;
    logo: string | null;
    url: string;
}

interface User {
    name: string;
    profile_picture: string | null;
}

interface LandingSection {
    title: string;
    brushed_title: string;
    description: string;
    link: Link | null;
    video: string;
    image: string;
    message_title: string;
    message_description: string;
}

interface StatsSection {
    stat1_title: string;
    stat1_description: string;
    stat1_link: Link | null;
    stat2_title: string;
    stat2_description: string;
    stat2_link: Link | null;
    stat3_title: string;
    stat3_description: string;
    stat3_link: Link | null;
    stat4_title: string;
    stat4_description: string;
    stat4_link: Link | null;
}

interface AdvertisementSection {
    title: string;
    description: string;
    link: Link;
}

interface DualChoicesSection {
    choice1_title: string;
    choice1_description: string;
    choice1_image: string;
    choice1_link: Link;
    choice2_title: string;
    choice2_description: string;
    choice2_image: string;
    choice2_link: Link;
}

interface UserExperienceSection {
    title: string;
    description: string;
    top_users: boolean | {
        title: string;
        list: User[]
    };
    comment1_text: string;
    comment1_user: User;
    comment1_rate: number;
    comment2_text: string;
    comment2_user: User;
    comment2_rate: number;
}

interface TopTeachersSection {
    title: string;
    description: string;
    list: any[];
}

interface ImagedLinksSection {
    links: any[];
}

interface CoursesDemoSection {
    video: string;
}

interface InformationBox {
    title: string;
    description: string;
    image: string;
    order: number;
}

interface InformationBoxesSection {
    boxes: InformationBox[];
}

interface MainPageData {
    landing: LandingSection;
    stats: StatsSection;
    advertisement: AdvertisementSection;
    dual_choices: DualChoicesSection;
    user_experience: UserExperienceSection;
    top_teachers: TopTeachersSection;
    imaged_links: ImagedLinksSection;
    courses_demo: CoursesDemoSection;
    information_boxes: InformationBoxesSection;
}

type SectionType = 
    | 'full_page'
    | 'landing'
    | 'stats'
    | 'advertisement'
    | 'dual_choices'
    | 'user_experience'
    | 'top_teachers'
    | 'imaged_links'
    | 'courses_demo'
    | 'information_boxes';

export function useMainPage(section: SectionType = 'full_page') {
    const [mainPageData, setMainPageData] = useState<MainPageData | null>(null);
    const [landingData, setLandingData] = useState<LandingSection | null>(null);
    const [statsData, setStatsData] = useState<StatsSection | null>(null);
    const [advertisementData, setAdvertisementData] = useState<AdvertisementSection | null>(null);
    const [dualChoicesData, setDualChoicesData] = useState<DualChoicesSection | null>(null);
    const [userExperienceData, setUserExperienceData] = useState<UserExperienceSection | null>(null);
    const [topTeachersData, setTopTeachersData] = useState<TopTeachersSection | null>(null);
    const [imagedLinksData, setImagedLinksData] = useState<ImagedLinksSection | null>(null);
    const [coursesDemoData, setCoursesDemoData] = useState<CoursesDemoSection | null>(null);
    const [informationBoxesData, setInformationBoxesData] = useState<InformationBoxesSection | null>(null);
    
    const [isLoadingMainPage, setIsLoadingMainPage] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        setIsLoadingMainPage(true);
        setError(null);

        api
            .get(`/site/mainpage/?section=${section}`)
            .then((response) => {
                if (response.data.success) {
                    const data = response.data.mainpage;
                    
                    if (section === 'full_page') {
                        setMainPageData(data);
                        setLandingData(data.landing);
                        setStatsData(data.stats);
                        setAdvertisementData(data.advertisement);
                        setDualChoicesData(data.dual_choices);
                        setUserExperienceData(data.user_experience);
                        setTopTeachersData(data.top_teachers);
                        setImagedLinksData(data.imaged_links);
                        setCoursesDemoData(data.courses_demo);
                        setInformationBoxesData(data.information_boxes);
                    } else {
                        // For specific sections, set only that section's data
                        switch (section) {
                            case 'landing':
                                setLandingData(data);
                                break;
                            case 'stats':
                                setStatsData(data);
                                break;
                            case 'advertisement':
                                setAdvertisementData(data);
                                break;
                            case 'dual_choices':
                                setDualChoicesData(data);
                                break;
                            case 'user_experience':
                                setUserExperienceData(data);
                                break;
                            case 'top_teachers':
                                setTopTeachersData(data);
                                break;
                            case 'imaged_links':
                                setImagedLinksData(data);
                                break;
                            case 'courses_demo':
                                setCoursesDemoData(data);
                                break;
                            case 'information_boxes':
                                setInformationBoxesData(data);
                                break;
                        }
                    }
                } else {
                    setError("Failed to load main page data");
                }
            })
            .catch((err) => {
                setError(err.message || "Failed to load main page data");
            })
            .finally(() => {
                setIsLoadingMainPage(false);
            });
    }, [section]);

    return {
        mainPageData,
        landingData,
        statsData,
        advertisementData,
        dualChoicesData,
        userExperienceData,
        topTeachersData,
        imagedLinksData,
        coursesDemoData,
        informationBoxesData,
        isLoadingMainPage: isLoadingMainPage,
        error
    };
}
