"use client";

import { useEffect, useState } from "react";
import { api } from "../api";

export interface AboutUsLink {
  name: string;
  logo: string | null;
  url: string;
}

export interface AboutUsInformation {
  title: string;
  description: string;
  image: string;
  order: number;
}

export interface AboutUsData {
  image_section_title: string;
  image_section_top_right_image: string | null;
  image_section_bottom_right_image: string | null;
  image_section_middle_image: string | null;
  image_section_bottom_left_image: string | null;
  image_section_box_title: string;
  image_section_box_description: string;
  info_section_title: string;
  info_section_description: string;
  info_section_information_boxes: AboutUsInformation[];
  trust_logo_section_title: string;
  trust_logo_section_links: AboutUsLink[];
}

export function useAboutUs() {
  const [aboutUsData, setAboutUsData] = useState<AboutUsData | null>(null);
  const [isLoadingAboutUs, setIsLoadingAboutUs] = useState(true);
  const [aboutUsError, setAboutUsError] = useState<string | null>(null);

  useEffect(() => {
    setIsLoadingAboutUs(true);
    setAboutUsError(null);

    api
      .get("/site/aboutus/")
      .then((response) => {
        if (response.data.success) {
          setAboutUsData(response.data.about_us);
        } else {
          setAboutUsError("Failed to load about us data");
        }
      })
      .catch((err) => {
        setAboutUsError(err.message || "Failed to load about us data");
      })
      .finally(() => {
        setIsLoadingAboutUs(false);
      });
  }, []);

  return { aboutUsData, isLoadingAboutUs, aboutUsError };
}
