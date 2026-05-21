"use client";

import { useEffect, useState } from "react";
import { api } from "../api";

export interface WorkWithUsLink {
  name: string;
  logo: string | null;
  url: string;
}

export interface WorkWithUsData {
  hero_title: string;
  hero_description: string;
  hero_link: WorkWithUsLink | null;
  hero_image: string | null;
  collaboration_section_title: string;
  collaboration_section_description: string;
  collaboration_section_step1_title: string;
  collaboration_section_step1_description: string;
  collaboration_section_step1_image: string | null;
  collaboration_section_step2_title: string;
  collaboration_section_step2_description: string;
  collaboration_section_step2_image: string | null;
  collaboration_section_step3_title: string;
  collaboration_section_step3_description: string;
  collaboration_section_step3_image: string | null;
  counter_section_item1_label: string;
  counter_section_item1_value: number;
  counter_section_item2_label: string;
  counter_section_item2_value: number;
  counter_section_item3_label: string;
  counter_section_item3_value: number;
  counter_section_item4_label: string;
  counter_section_item4_value: number;
  main_content_section_title: string;
  main_content_section_tab1_title: string;
  main_content_section_tab1_description: string;
  main_content_section_tab2_title: string;
  main_content_section_tab2_description: string;
  main_content_section_tab3_title: string;
  main_content_section_tab3_description: string;
  advertisement_section_title: string;
  advertisement_section_description: string;
  advertisement_section_link: WorkWithUsLink | null;
}

export interface WorkWithUsResumePayload {
  full_name: string;
  email: string;
  phone_number: string;
  message: string;
}

export function isValidIranPhoneNumber(phone: string): boolean {
  return /^09\d{9}$/.test(phone.trim());
}

export function useWorkWithUs() {
  const [workWithUsData, setWorkWithUsData] = useState<WorkWithUsData | null>(null);
  const [isLoadingWorkWithUs, setIsLoadingWorkWithUs] = useState(true);
  const [workWithUsError, setWorkWithUsError] = useState<string | null>(null);

  useEffect(() => {
    setIsLoadingWorkWithUs(true);
    setWorkWithUsError(null);

    api
      .get("/site/workwithus/")
      .then((response) => {
        if (response.data.success) {
          setWorkWithUsData(response.data.work_with_us);
        } else {
          setWorkWithUsError("Failed to load work-with-us data");
        }
      })
      .catch((err) => {
        setWorkWithUsError(err.message || "Failed to load work-with-us data");
      })
      .finally(() => {
        setIsLoadingWorkWithUs(false);
      });
  }, []);

  return { workWithUsData, isLoadingWorkWithUs, workWithUsError };
}

export async function submitWorkWithUsResume(payload: WorkWithUsResumePayload): Promise<{ success: boolean; message: string }> {
  try {
    const response = await api.post("/site/workwithus/resume-submission/", payload);
    return {
      success: !!response.data?.success,
      message: response.data?.message || (response.data?.success ? "Successful" : "Submission failed"),
    };
  } catch (err: any) {
    return {
      success: false,
      message: err?.response?.data?.message || "Submission failed",
    };
  }
}
