"use client";

import { useEffect, useState } from "react";
import {
    ActiveAttempt,
    LeaderboardEntry,
    Quiz,
    QuizAdmin,
    QuizAttempt,
    quizManager,
} from "../quiz/quizManager";

export function useQuiz() {
    const [quizzes, setQuizzes] = useState<Quiz[]>(quizManager.getQuizzes());
    const [quizzesTotal, setQuizzesTotal] = useState(quizManager.getQuizzesTotal());
    const [quizzesTotalPages, setQuizzesTotalPages] = useState(quizManager.getQuizzesTotalPages());
    const [currentQuiz, setCurrentQuiz] = useState<Quiz | null>(quizManager.getCurrentQuiz());
    const [activeAttempt, setActiveAttempt] = useState<ActiveAttempt | null>(quizManager.getActiveAttempt());
    const [myAttempts, setMyAttempts] = useState<QuizAttempt[]>(quizManager.getMyAttempts());
    const [myAttemptsTotal, setMyAttemptsTotal] = useState(quizManager.getMyAttemptsTotal());
    const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>(quizManager.getLeaderboard());
    const [userRank, setUserRank] = useState<number | null>(quizManager.getUserRank());
    const [userLeaderboardEntry, setUserLeaderboardEntry] = useState<(LeaderboardEntry & { rank: number }) | null>(quizManager.getUserLeaderboardEntry());
    const [adminQuizzes, setAdminQuizzes] = useState<QuizAdmin[]>(quizManager.getAdminQuizzes());
    const [adminQuizzesTotal, setAdminQuizzesTotal] = useState(quizManager.getAdminQuizzesTotal());
    const [adminCategories, setAdminCategories] = useState(quizManager.getAdminCategories());
    const [isLoading, setIsLoading] = useState(quizManager.getIsLoading());

    useEffect(() => {
        const unsubscribe = quizManager.subscribe(() => {
            setQuizzes(quizManager.getQuizzes());
            setQuizzesTotal(quizManager.getQuizzesTotal());
            setQuizzesTotalPages(quizManager.getQuizzesTotalPages());
            setCurrentQuiz(quizManager.getCurrentQuiz());
            setActiveAttempt(quizManager.getActiveAttempt());
            setMyAttempts(quizManager.getMyAttempts());
            setMyAttemptsTotal(quizManager.getMyAttemptsTotal());
            setLeaderboard(quizManager.getLeaderboard());
            setUserRank(quizManager.getUserRank());
            setUserLeaderboardEntry(quizManager.getUserLeaderboardEntry());
            setAdminQuizzes(quizManager.getAdminQuizzes());
            setAdminQuizzesTotal(quizManager.getAdminQuizzesTotal());
            setAdminCategories(quizManager.getAdminCategories());
            setIsLoading(quizManager.getIsLoading());
        });
        return unsubscribe;
    }, []);

    return {
        quizzes,
        quizzesTotal,
        quizzesTotalPages,
        currentQuiz,
        activeAttempt,
        myAttempts,
        myAttemptsTotal,
        leaderboard,
        userRank,
        userLeaderboardEntry,
        adminQuizzes,
        adminQuizzesTotal,
        adminCategories,
        isLoading,
        fetchQuizzes: quizManager.fetchQuizzes.bind(quizManager),
        fetchQuizDetail: quizManager.fetchQuizDetail.bind(quizManager),
        startQuiz: quizManager.startQuiz.bind(quizManager),
        submitAnswer: quizManager.submitAnswer.bind(quizManager),
        finishQuiz: quizManager.finishQuiz.bind(quizManager),
        fetchLeaderboard: quizManager.fetchLeaderboard.bind(quizManager),
        fetchMyAttempts: quizManager.fetchMyAttempts.bind(quizManager),
        clearActiveAttempt: quizManager.clearActiveAttempt.bind(quizManager),
        fetchAdminQuizzes: quizManager.fetchAdminQuizzes.bind(quizManager),
        createQuiz: quizManager.createQuiz.bind(quizManager),
        updateQuiz: quizManager.updateQuiz.bind(quizManager),
        deleteQuiz: quizManager.deleteQuiz.bind(quizManager),
        fetchAdminQuizDetail: quizManager.fetchAdminQuizDetail.bind(quizManager),
        createQuestion: quizManager.createQuestion.bind(quizManager),
        updateQuestion: quizManager.updateQuestion.bind(quizManager),
        deleteQuestion: quizManager.deleteQuestion.bind(quizManager),
        reorderQuestions: quizManager.reorderQuestions.bind(quizManager),
        createAccessRequirement: quizManager.createAccessRequirement.bind(quizManager),
        deleteAccessRequirement: quizManager.deleteAccessRequirement.bind(quizManager),
        fetchAdminCategories: quizManager.fetchAdminCategories.bind(quizManager),
        createAdminCategory: quizManager.createAdminCategory.bind(quizManager),
    };
}
