import type { Metadata } from "next";
import Script from "next/script";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

// Vendor CSS
import "../public/assets/vendor/font-awesome/css/all.min.css";
import "../public/assets/vendor/bootstrap-icons/bootstrap-icons.css";
import "../public/assets/vendor/tiny-slider/tiny-slider.css";
import "../public/assets/vendor/glightbox/css/glightbox.css";
import "../public/assets/vendor/aos/aos.css";
import "../public/assets/vendor/choices/css/choices.min.css";
import "../public/assets/vendor/overlay-scrollbar/css/overlayscrollbars.min.css";

// Template CSS
import "../public/assets/css/style-rtl.css";

export const metadata: Metadata = {
  title: "Rattel",
  description: "Rattel learning platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fa" dir="rtl">
      <body>
        {children}
        <ToastContainer
          position="top-center"
          autoClose={4000}
          hideProgressBar={false}
          closeOnClick
          pauseOnHover
        />
        
        {/* Vendor JS - load in order */}
        <Script src="/assets/vendor/bootstrap/dist/js/bootstrap.bundle.min.js" strategy="beforeInteractive" />
        <Script src="/assets/vendor/tiny-slider/tiny-slider-rtl.js" strategy="lazyOnload" />
        <Script src="/assets/vendor/glightbox/js/glightbox.js" strategy="lazyOnload" />
        <Script src="/assets/vendor/purecounterjs/dist/purecounter_vanilla.js" strategy="lazyOnload" />
        <Script src="/assets/vendor/aos/aos.js" strategy="lazyOnload" />
        <Script src="/assets/vendor/choices/js/choices.min.js" strategy="lazyOnload" />
        <Script src="/assets/vendor/sticky-js/sticky.min.js" strategy="lazyOnload" />
        <Script src="/assets/vendor/overlay-scrollbar/js/overlayscrollbars.min.js" strategy="lazyOnload" />
        
        {/* Template JS - must load after vendors */}
        <Script src="/assets/js/functions.js" strategy="lazyOnload" />
      </body>
    </html>
  );
}
