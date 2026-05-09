import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SwissEdge Public Prototype",
  description:
    "Static SwissEdge public research article prototype for educational research documentation.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-theme="light">
      <body>{children}</body>
    </html>
  );
}
