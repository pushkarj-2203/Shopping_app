"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, getToken, setToken } from "@/lib/api";

export default function Nav() {
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) return;
    api.me().then((u) => setEmail(u.email)).catch(() => setToken(null));
  }, []);

  return (
    <header className="border-b border-gray-100 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <Link href="/" className="text-lg font-bold text-brand">
          PriceWise<span className="text-gray-400"> AI</span>
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link href="/search" className="text-gray-600 hover:text-brand">Find a product</Link>
          {email ? (
            <span className="text-gray-500">{email}</span>
          ) : (
            <Link href="/login" className="font-medium text-brand hover:underline">Sign in</Link>
          )}
        </nav>
      </div>
    </header>
  );
}
