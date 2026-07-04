"""FeishuNotifier：自定义机器人 Webhook 推送。

支持：
- 文本 / 交互卡片
- 可选签名（HMAC-SHA256）
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import time
from typing import Any

import httpx

from app.config import settings
from app.notifiers.base import BaseNotifier
from app.utils.logging import logger


def gen_feishu_sign(timestamp: int, secret: str) -> str:
    """飞书自定义机器人签名算法。

    与飞书官方文档一致：把 `f"{ts}\n{secret}"` 作为 key 对空字符串做 HMAC-SHA256，
    再 base64 编码。
    """
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(
        string_to_sign.encode("utf-8"),
        msg=b"",
        digestmod=hashlib.sha256,
    ).digest()
    return base64.b64encode(hmac_code).decode("utf-8")


class FeishuNotifier(BaseNotifier):
    """飞书自定义机器人。"""

    name = "feishu"

    def __init__(
        self,
        webhook: str | None = None,
        secret: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.webhook = webhook or settings.feishu_webhook
        self.secret = secret if secret is not None else settings.feishu_secret
        self.timeout = timeout

    def _attach_sign(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.secret:
            return payload
        ts = int(time.time())
        return {
            "timestamp": str(ts),
            "sign": gen_feishu_sign(ts, self.secret),
            **payload,
        }

    def send(self, payload: dict[str, Any]) -> bool:
        """发送一条消息。失败返回 False，并记录日志。"""
        if not self.webhook:
            logger.error("FEISHU_WEBHOOK 未配置，跳过推送")
            return False

        body = self._attach_sign(payload)
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(self.webhook, json=body)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:  # noqa: BLE001
            logger.error("飞书推送 HTTP 异常: {}", exc)
            return False

        # 飞书返回：{"code":0,"msg":"success","data":{...}} 或 {"StatusCode":0,...}
        code = data.get("code", data.get("StatusCode", -1))
        if code == 0:
            logger.info("飞书推送成功")
            return True

        logger.error("飞书返回错误: {}", data)
        return False


__all__ = ["FeishuNotifier", "gen_feishu_sign"]
