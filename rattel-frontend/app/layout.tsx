import type { Metadata } from "next";
import Script from "next/script";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
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
        <Script src="/assets/js/functions.js" strategy="lazyOnload" />
      </body>
    </html>
  );
}
