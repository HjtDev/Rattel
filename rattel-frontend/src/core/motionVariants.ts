import type { Variants } from "framer-motion";

export const fadeInUp: Variants = {
    hidden: { opacity: 0, y: 30 },
    show: { opacity: 1, y: 0, transition: { duration: 0.55, ease: "easeOut" } }
};

export const fadeInLeft: Variants = {
    hidden: { opacity: 0, x: -50 },
    show: { opacity: 1, x: 0, transition: { duration: 0.6, ease: "easeOut" } }
};

export const fadeInRight: Variants = {
    hidden: { opacity: 0, x: 50 },
    show: { opacity: 1, x: 0, transition: { duration: 0.6, ease: "easeOut" } }
};

export const staggerContainer: Variants = {
    hidden: {},
    show: { transition: { staggerChildren: 0.1 } }
};

export const scaleIn: Variants = {
    hidden: { opacity: 0, scale: 0.93 },
    show: { opacity: 1, scale: 1, transition: { duration: 0.5, ease: "easeOut" } }
};
