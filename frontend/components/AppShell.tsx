"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { isLoggedIn } from "../lib/auth";
import Sidebar from "./sidebar";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (pathname === "/login") return;
    if (!isLoggedIn()) {
      router.replace("/login");
    }
  }, [pathname, router]);

  if (pathname === "/login") {
    return <>{children}</>;
  }

  return (
    <div className="layout">
      <Sidebar />
      <main className="main">{children}</main>
    </div>
  );
}
