import type { Metadata } from "next";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
// TEMPLATE: import your main template CSS files below
// import "../src/styles/template.css";
import "./globals.css";

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
      </body>
    </html>
  );
}
