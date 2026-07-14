import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ali Raza's Assistant",
  description:
    "A fast, private-by-design AI chat experience powered by LangGraph and Groq.",
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
