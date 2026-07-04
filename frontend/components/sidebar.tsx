"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "../lib/auth";

const items = [
  { href: "/", label: "Dashboard" },
  { href: "/articles", label: "文章" },
  { href: "/sources", label: "信息源" },
  { href: "/push-history", label: "推送历史" },
  { href: "/settings", label: "设置" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  function logout() {
    clearToken();
    router.replace("/login");
  }

  return (
    <aside className="sidebar">
      <h1>AI-News</h1>
      {items.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className={`nav-item ${pathname === item.href ? "active" : ""}`}
        >
          {item.label}
        </Link>
      ))}
      <button className="logout-btn" onClick={logout}>
        退出登录
      </button>
    </aside>
  );
}
