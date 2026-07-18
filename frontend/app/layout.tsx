import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RazaMind",
  description:
    "An observable AI chat experience powered by LangGraph, Groq, and LangSmith.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
