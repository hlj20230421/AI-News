"""推送通道抽象基类。"""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseNotifier(ABC):
    """所有推送通道的基类。"""

    name: str = "base"

    @abstractmethod
    def send(self, payload: dict) -> bool:
        """发送消息，返回是否成功。"""
        raise NotImplementedError
