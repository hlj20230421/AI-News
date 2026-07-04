"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { login } from "../../lib/api";
import { setToken } from "../../lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await login(password);
      setToken(data.access_token);
      router.replace("/");
    } catch {
      setError("登录失败，请检查口令");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <form className="card login-card" onSubmit={onSubmit}>
        <h2>AI-News 管理后台</h2>
        <p className="muted">请输入管理员口令登录</p>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="管理员口令"
          autoComplete="current-password"
        />
        {error ? <p className="error">{error}</p> : null}
        <button type="submit" disabled={loading || !password}>
          {loading ? "登录中..." : "登录"}
        </button>
      </form>
    </div>
  );
}
