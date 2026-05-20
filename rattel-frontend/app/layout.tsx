import type { Metadata } from "next";
import Script from "next/script";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import "./globals.css";

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
import Navbar from "@/src/components/layout/Navbar";
import Footer from "@/src/components/layout/Footer";

const siteName = "موسسه فرهنگی اکسیر قرآن";
const siteUrl = "https://exirequran.ir";
const siteDescription =
  "اکسیر قرآن؛ مرجع تخصصی تولیدات رسانه‌ای و سامانه آموزش مجازی علوم قرآن، تدبر، تلاوت و حفظ، با بهره‌گیری از اساتید برجسته در مسیر تعلیم و ترویج فرهنگ اهل‌بیت ع";
const siteKeywords = [
  "اکسیر قرآن",
  "ExireQuran",
  "آموزش قرآن",
  "سامانه آموزش قرآن",
  "حفظ قرآن",
  "تلاوت قرآن",
  "مسابقات قرآنی",
  "آموزش تجوید",
  "آموزش صوت و لحن",
  "آموزش روخوانی قرآن",
  "آموزش روانخوانی قرآن",
  "کلاس آنلاین قرآن",
  "دوره قرآن آنلاین",
  "Quran learning platform",
  "Online Quran classes",
  "Quran memorization program",
  "Quran competitions",
  "Tajweed course",
  "Quran recitation training",
  "Hifz program",
];
const organizationProfiles = [
  "https://eitaa.com/Rattel",
  "https://ble.ir/Rattel",
  "https://www.aparat.com/Rattel",
  "https://t.me/Rattel",
  "https://instagram.com/Rattel",
  "https://x.com/Rattel",
  "https://youtube.com/@Rattel",
  "https://www.linkedin.com/company/Rattel",
  "https://facebook.com/Rattel",
  "https://www.tiktok.com/@Rattel",
  "https://www.pinterest.com/Rattel",
  "https://wa.me/Rattel",
];

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: siteName,
    template: `%s | ${siteName}`,
  },
  description: siteDescription,
  applicationName: "ExireQuran",
  authors: [{ name: "Hossein Esfahanian" }],
  creator: "Hossein Esfahanian",
  publisher: "ExireQuran",
  category: "Education",
  generator: "Next.js",
  referrer: "origin-when-cross-origin",
  keywords: siteKeywords,
  alternates: {
    canonical: "/",
    languages: {
      fa: "/",
      "en-US": "/en",
    },
  },
  robots: {
    index: true,
    follow: true,
    nocache: false,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  openGraph: {
    type: "website",
    locale: "fa_IR",
    alternateLocale: "en_US",
    url: siteUrl,
    siteName: "ExireQuran",
    title: siteName,
    description: siteDescription,
    emails: ["info@exirequran.ir"],
    countryName: "IR",
    images: [
      {
        url: "/favicon.ico",
        width: 256,
        height: 256,
        alt: "ExireQuran Logo",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: siteName,
    description: siteDescription,
    creator: "@Rattel",
    site: "@Rattel",
    images: ["/favicon.ico"],
  },
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon.ico",
    apple: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fa" dir="rtl">
      <body>
        {<Navbar />}
        {children}
        {<Footer />}
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
        <Script
          id="organization-jsonld"
          type="application/ld+json"
          strategy="afterInteractive"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "EducationalOrganization",
              name: "ExireQuran",
              alternateName: "اکسیر قرآن",
              url: siteUrl,
              email: "info@exirequran.ir",
              founder: {
                "@type": "Person",
                name: "Hossein Esfahanian",
              },
              sameAs: organizationProfiles,
              description: siteDescription,
              inLanguage: ["fa", "en"],
              keywords: siteKeywords.join(", "),
            }),
          }}
        />
      </body>
    </html>
  );
}
