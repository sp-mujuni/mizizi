"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/lib/auth";

export default function Navbar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();

  const links = [
    { href: "/", label: "Home" },
    { href: "/archive", label: "Archive" },
    { href: "/record", label: "Record" },
    { href: "/review", label: "Review" },
    { href: "/ai", label: "Ask Mizizi" },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-stone-200 bg-white/90 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/" className="flex items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand font-serif text-lg font-bold text-white">
            M
          </span>
          <span className="text-lg font-bold tracking-tight text-brand-dark">
            Mizizi
            <span className="ml-1 hidden text-xs font-normal text-stone-500 sm:inline">
              The Living Memory of Africa
            </span>
          </span>
        </Link>
        <div className="flex items-center gap-1 sm:gap-2">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={`rounded-md px-2 py-1.5 text-sm font-medium transition hover:bg-brand/10 hover:text-brand-dark sm:px-3 ${
                pathname === l.href ? "bg-brand/10 text-brand-dark" : "text-stone-600"
              }`}
            >
              {l.label}
            </Link>
          ))}
          {user ? (
            <>
              <Link
                href="/account"
                className="rounded-md bg-brand px-3 py-1.5 text-sm font-semibold text-white transition hover:bg-brand-dark"
              >
                {user.display_name ?? user.email}
              </Link>
              <button
                onClick={() => void logout()}
                className="rounded-md px-2 py-1.5 text-sm font-medium text-stone-500 transition hover:text-stone-800"
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="rounded-md px-2 py-1.5 text-sm font-medium text-stone-600 transition hover:text-brand-dark"
              >
                Sign in
              </Link>
              <Link
                href="/register"
                className="rounded-md bg-brand px-3 py-1.5 text-sm font-semibold text-white transition hover:bg-brand-dark"
              >
                Join
              </Link>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}