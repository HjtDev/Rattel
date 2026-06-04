"use client";

import { useEffect, useState } from "react";
import { automaticClassManager, ClassRequest, AutomaticPlan, TodayData, ProgressData } from "../automatic-class/automaticClassManager";

export function useAutomaticClass() {
    const [classRequest, setClassRequest] = useState<ClassRequest | null>(automaticClassManager.getClassRequest());
    const [plan, setPlan] = useState<AutomaticPlan | null>(automaticClassManager.getPlan());
    const [todayData, setTodayData] = useState<TodayData | null>(automaticClassManager.getTodayData());
    const [progressData, setProgressData] = useState<ProgressData | null>(automaticClassManager.getProgressData());
    const [isLoading, setIsLoading] = useState(automaticClassManager.getIsLoading());
    const [noSubscription, setNoSubscription] = useState(automaticClassManager.getNoSubscription());

    useEffect(() => {
        const unsub = automaticClassManager.subscribe(() => {
            setClassRequest(automaticClassManager.getClassRequest());
            setPlan(automaticClassManager.getPlan());
            setTodayData(automaticClassManager.getTodayData());
            setProgressData(automaticClassManager.getProgressData());
            setIsLoading(automaticClassManager.getIsLoading());
            setNoSubscription(automaticClassManager.getNoSubscription());
        });
        return unsub;
    }, []);

    return {
        classRequest,
        plan,
        todayData,
        progressData,
        isLoading,
        noSubscription,
        fetchClassRequest: automaticClassManager.fetchClassRequest.bind(automaticClassManager),
        submitClassRequest: automaticClassManager.submitClassRequest.bind(automaticClassManager),
        fetchMyPlan: automaticClassManager.fetchMyPlan.bind(automaticClassManager),
        fetchTodaySteps: automaticClassManager.fetchTodaySteps.bind(automaticClassManager),
        fetchProgress: automaticClassManager.fetchProgress.bind(automaticClassManager),
        completeStep: automaticClassManager.completeStep.bind(automaticClassManager),
        reportDelay: automaticClassManager.reportDelay.bind(automaticClassManager),
    };
}
