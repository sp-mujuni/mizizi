"use client";

import Link from "next/link";
import { useState } from "react";
import { usePathname } from "next/navigation";

import { useAuth } from "@/lib/auth";

export default function Navbar() {
  const { user, isAdmin, logout } = useAuth();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const links = [
    { href: "/", label: "Home" },
    { href: "/archive", label: "Archive" },
    { href: "/record", label: "Record" },
    { href: "/review", label: "Review" },
    { href: "/ai", label: "Ask Mizizi" },
    ...(isAdmin ? [{ href: "/admin", label: "Admin" }] : []),
  ];

  const desktopLinkClass = (href: string) =>
    `rounded-md px-2 py-1.5 text-sm font-medium transition hover:bg-brand/10 hover:text-brand-dark sm:px-3 ${
      pathname === href ? "bg-brand/10 text-brand-dark" : "text-stone-600"
    }`;

  const mobileLinkClass = (href: string) =>
    `block rounded-lg px-3 py-2.5 text-sm font-medium transition ${
      pathname === href ? "bg-brand/10 text-brand-dark" : "text-stone-600 hover:bg-stone-100"
    }`;

  function close() {
    setOpen(false);
  }

  return (
    <header className="sticky top-0 z-50 border-b border-stone-200 bg-white/90 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/" className="flex items-center gap-2" onClick={close}>
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

        {/* Desktop navigation */}
        <div className="hidden items-center gap-1 md:flex md:gap-2">
          {links.map((l) => (
            <Link key={l.href} href={l.href} className={desktopLinkClass(l.href)}>
              {l.label}
            </Link>
          ))}
          <div className="ml-2 flex items-center gap-1 sm:gap-2">
            {user ? (
              <>
                <Link
                  href="/account"
                  className="max-w-32 truncate rounded-md bg-brand px-3 py-1.5 text-sm font-semibold text-white transition hover:bg-brand-dark"
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
        </div>

        {/* Hamburger toggle (mobile only) */}
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          aria-controls="mobile-menu"
          aria-label={open ? "Close menu" : "Open menu"}
          className="flex h-10 w-10 items-center justify-center rounded-lg border border-stone-200 text-stone-700 transition hover:bg-stone-100 md:hidden"
        >
          {open ? (
            <svg
              className="h-6 w-6"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          ) : (
            <svg
              className="h-6 w-6"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          )}
        </button>
      </nav>

      {/* Mobile dropdown menu */}
      {open && (
        <div id="mobile-menu" className="border-t border-stone-200 bg-white/95 backdrop-blur md:hidden">
          <nav className="mx-auto max-w-6xl space-y-1 px-4 py-3">
            {links.map((l) => (
              <Link key={l.href} href={l.href} className={mobileLinkClass(l.href)} onClick={close}>
                {l.label}
              </Link>
            ))}
            <div className="mt-2 flex items-center gap-2 border-t border-stone-100 pt-3">
              {user ? (
                <>
                  <Link
                    href="/account"
                    onClick={close}
                    className="flex-1 truncate rounded-lg bg-brand px-3 py-2.5 text-center text-sm font-semibold text-white transition hover:bg-brand-dark"
                  >
                    {user.display_name ?? user.email}
                  </Link>
                  <button
                    onClick={() => {
                      close();
                      void logout();
                    }}
                    className="rounded-lg border border-stone-300 px-4 py-2.5 text-sm font-medium text-stone-600 transition hover:bg-stone-100"
                  >
                    Sign out
                  </button>
                </>
              ) : (
                <>
                  <Link
                    href="/login"
                    onClick={close}
                    className="flex-1 rounded-lg border border-brand/30 px-3 py-2.5 text-center text-sm font-semibold text-brand-dark transition hover:bg-brand/10"
                  >
                    Sign in
                  </Link>
                  <Link
                    href="/register"
                    onClick={close}
                    className="flex-1 rounded-lg bg-brand px-3 py-2.5 text-center text-sm font-semibold text-white transition hover:bg-brand-dark"
                  >
                    Join Mizizi
                  </Link>
                </>
              )}
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}
