"use client";

import { useEffect, useState } from "react";
import {
    automaticClassManager,
    AdminClassRequest,
    AdminPlan,
    AdminCallLog,
    CreatePlanPayload,
} from "../automatic-class/automaticClassManager";

export function useAdminClassPanel() {
    const [adminRequests, setAdminRequests] = useState<AdminClassRequest[]>(automaticClassManager.getAdminRequests());
    const [adminRequestsTotal, setAdminRequestsTotal] = useState(automaticClassManager.getAdminRequestsTotal());
    const [adminPlans, setAdminPlans] = useState<AdminPlan[]>(automaticClassManager.getAdminPlans());
    const [adminPlansTotal, setAdminPlansTotal] = useState(automaticClassManager.getAdminPlansTotal());
    const [activePlan, setActivePlan] = useState<AdminPlan | null>(automaticClassManager.getActivePlan());
    const [callLogs, setCallLogs] = useState<AdminCallLog[]>(automaticClassManager.getCallLogs());
    const [isLoading, setIsLoading] = useState(automaticClassManager.getIsLoading());

    useEffect(() => {
        const unsub = automaticClassManager.subscribe(() => {
            setAdminRequests(automaticClassManager.getAdminRequests());
            setAdminRequestsTotal(automaticClassManager.getAdminRequestsTotal());
            setAdminPlans(automaticClassManager.getAdminPlans());
            setAdminPlansTotal(automaticClassManager.getAdminPlansTotal());
            setActivePlan(automaticClassManager.getActivePlan());
            setCallLogs(automaticClassManager.getCallLogs());
            setIsLoading(automaticClassManager.getIsLoading());
        });
        return unsub;
    }, []);

    return {
        adminRequests,
        adminRequestsTotal,
        adminPlans,
        adminPlansTotal,
        activePlan,
        callLogs,
        isLoading,
        fetchAdminRequests: automaticClassManager.fetchAdminRequests.bind(automaticClassManager),
        updateAdminRequest: automaticClassManager.updateAdminRequest.bind(automaticClassManager),
        fetchAdminPlans: automaticClassManager.fetchAdminPlans.bind(automaticClassManager),
        fetchAdminPlanDetail: automaticClassManager.fetchAdminPlanDetail.bind(automaticClassManager),
        createPlan: automaticClassManager.createPlan.bind(automaticClassManager),
        updatePlan: automaticClassManager.updatePlan.bind(automaticClassManager),
        updateAdminStep: automaticClassManager.updateAdminStep.bind(automaticClassManager),
        logCall: automaticClassManager.logCall.bind(automaticClassManager),
        clearActivePlan: automaticClassManager.clearActivePlan.bind(automaticClassManager),
    };
}
