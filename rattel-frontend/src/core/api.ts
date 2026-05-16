import axios from "axios";
import { setupCache } from "axios-cache-interceptor";
import { toast } from "react-toastify";
import { authManager } from "./auth/authManager";

const baseClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL + "/api/v1",
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

export const api = setupCache(baseClient, {
  ttl: 1000 * 60 * 5,
  methods: ["get"],
});

let refreshPromise: Promise<boolean> | null = null;

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (!error.response) {
      toast.error("Network error. Please check your connection.");
      return Promise.reject(error);
    }

    const { status } = error.response;
    const originalRequest = error.config;
    const requestUrl = originalRequest?.url || "";
    const isRefreshRequest = requestUrl.includes("/auth/refresh/");

    // Never try to refresh if refresh endpoint itself failed (prevents recursive retry loop).
    if (status === 401 && isRefreshRequest) {
      authManager.logout();
      toast.error("لطفا مجددا وارد حساب خود شوید.");
      if (typeof window !== "undefined") {
        window.location.href = "/auth/login/";
      }
      return Promise.reject(error);
    }

    // Handle 401 - try to refresh token once
    if (status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      if (!refreshPromise) {
        refreshPromise = authManager.refreshAccessToken().finally(() => {
          refreshPromise = null;
        });
      }

      const refreshed = await refreshPromise;
      
      if (refreshed) {
        const newToken = authManager.getAccessToken();
        if (newToken) {
          originalRequest.headers = originalRequest.headers || {};
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return api(originalRequest);
        }
      }

      // Refresh failed - logout user
      authManager.logout();
      toast.error("لطفا مجددا وارد حساب خود شوید.");
      if (typeof window !== "undefined") {
        window.location.href = "/auth/login/";
      }
      return Promise.reject(error);
    }

    switch (status) {
      case 429:
        toast.warning("تعداد درخواست های شما بیش از حد مجاز است لطفا کمی صبر کنید.");
        break;
      case 401:
        toast.error("لطفا مجددا وارد حساب خود شوید.");
        break;
      case 403:
        toast.error("دسترسی شما محدود شده است.");
        break;
      case 500:
        toast.error("مشکلی پیش آمده است لطفا بعدا تلاش کنید.");
        break;
    }

    return Promise.reject(error);
  }
);
