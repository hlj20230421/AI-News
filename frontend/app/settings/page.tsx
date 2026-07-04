export default function SettingsPage() {
  return (
    <div>
      <h2>设置</h2>
      <div className="card">
        <p className="muted">
          偏好与系统配置请在项目根目录 <code>.env</code> 中修改，然后重启 Docker 服务。
        </p>
        <ul>
          <li>LLM 提供商与模型：<code>LLM_PROVIDER</code> / <code>LLM_MODEL</code></li>
          <li>飞书 Webhook：<code>FEISHU_WEBHOOK</code></li>
          <li>管理员口令：<code>ADMIN_PASSWORD</code></li>
          <li>API 端口：<code>APP_PORT</code>（默认 8001）</li>
        </ul>
      </div>
    </div>
  );
}
