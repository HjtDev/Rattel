import axios from "axios";
import { setupCache } from "axios-cache-interceptor";
import { toast } from "react-toastify";

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
  (error) => {
    if (!error.response) {
      toast.error("Network error. Please check your connection.");
      return Promise.reject(error);
    }

    const { status } = error.response;

    switch (status) {
      case 429:
        toast.warning("Too many requests. Please slow down.");
        break;
      case 401:
        toast.error("Session expired. Please log in again.");
        break;
      case 403:
        toast.error("You do not have permission to perform this action.");
        break;
      case 500:
        toast.error("Server error. Please try again later.");
        break;
    }

    return Promise.reject(error);
  }
);
