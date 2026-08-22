import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import Navbar from "@/components/navbar";
import { AuthProvider } from "@/lib/auth";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Mizizi — The Living Memory of Uganda",
  description:
    "So the stories don't disappear. An AI-powered living archive for Ugandan oral culture.",
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
          <p className="font-medium text-stone-700">Mizizi — The Living Memory of Uganda</p>
          <p className="mt-1 italic">&ldquo;No generation should be the last generation to remember a story.&rdquo;</p>
          <nav className="mt-4 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-stone-500">
            <Link href="/terms" className="hover:text-brand-dark hover:underline">
              Terms of Service
            </Link>
            <span className="text-stone-300">·</span>
            <Link href="/privacy" className="hover:text-brand-dark hover:underline">
              Privacy Policy
            </Link>
          </nav>
        </footer>
      </body>
    </html>
  );
}