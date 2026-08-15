import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Navbar from "@/components/navbar";
import { AuthProvider } from "@/lib/auth";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Mizizi — The Living Memory of Africa",
  description:
    "So the stories don't disappear. An AI-powered living archive for African oral culture.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">
        <AuthProvider>
          <Navbar />
          <main className="flex-1">{children}</main>
        </AuthProvider>
        <footer className="border-t border-stone-200 bg-white/60 py-8 text-center text-sm text-stone-500">
          <p className="font-medium text-stone-700">Mizizi — The Living Memory of Africa</p>
          <p className="mt-1 italic">&ldquo;No generation should be the last generation to remember a story.&rdquo;</p>
        </footer>
      </body>
    </html>
  );
}