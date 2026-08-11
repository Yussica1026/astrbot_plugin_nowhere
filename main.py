"""AstrBot adapter for the original Nowhere world-walking runtime."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

PLUGIN_ROOT = Path(__file__).resolve().parent
DATA_ROOT = (Path.cwd() / "data" / "plugin_data" / "astrbot_plugin_nowhere").resolve()
DATA_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("NOWHERE_HOME", str(DATA_ROOT))
sys.path.insert(0, str(PLUGIN_ROOT / "vendor"))

from nowhere import server as nowhere  # noqa: E402


def _text(result: Any) -> str:
    if isinstance(result, dict):
        return str(result.get("text") or json.dumps(result, ensure_ascii=False, default=str))
    return str(result)


async def dispatch(action: str, **args: Any) -> dict[str, Any]:
    """Call the unmodified upstream implementation behind a stable AstrBot facade."""
    action = action.strip().lower()
    if action == "open_door":
        return await nowhere.open_door_impl(args.get("to") or None)
    if action == "continue_journey":
        return await nowhere.open_door_impl(resume=True)
    if action == "walk":
        return await nowhere.walk_impl(args.get("direction") or "forward", float(args.get("distance_km") or 2))
    if action == "walk_to":
        return await nowhere.walk_to_impl(str(args.get("place") or args.get("to") or ""))
    if action == "look_around":
        return await nowhere.look_around_impl()
    if action == "listen":
        return await nowhere.listen_impl(int(args.get("seconds") or 10))
    if action == "ask":
        return await nowhere.ask_impl(str(args.get("topic") or "这里"))
    if action == "wait":
        return await nowhere.wait_impl(float(args.get("hours") or 1))
    if action == "mark":
        return nowhere.mark_impl(str(args.get("name") or "此处"), str(args.get("note") or ""), bool(args.get("overwrite")))
    if action == "marks":
        return nowhere.marks_impl()
    if action == "where_am_i":
        return nowhere.where_am_i_impl()
    if action in {"postcard", "send_postcard"}:
        return nowhere.send_postcard_impl(str(args.get("text") or "从路上寄回一张明信片。"))
    if action == "souvenir":
        item = nowhere._state.souvenir
        return {"text": "身上什么都没带。空手走的。", "data": {"souvenir": None}} if item is None else {"text": f"你身上带着{item['name']}。来自{item['from']}。", "data": {"souvenir": item}}
    if action == "give_souvenir":
        item = nowhere._state.souvenir
        if item is None:
            return {"text": "身上什么都没有。", "data": {"error": "empty"}}
        nowhere._state.souvenir = None
        nowhere._state.save()
        return {"text": f"你把{item['name']}放在了路边。也许会有人捡到。", "data": {"dropped": item}}
    raise ValueError(f"未知动作：{action}")


class NowherePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        logger.info(f"乌有乡原版旅行运行时已加载，数据目录：{DATA_ROOT}")

    @filter.llm_tool(name="nowhere_travel")
    async def nowhere_travel(
        self,
        event: AstrMessageEvent,
        action: str,
        to: str = "",
        direction: str = "forward",
        distance_km: float = 2,
        place: str = "",
        topic: str = "",
        name: str = "",
        note: str = "",
        text: str = "",
        hours: float = 1,
        seconds: int = 10,
        overwrite: bool = False,
    ):
        """在乌有乡真实地球旅行。必须调用工具才能声称已经行走或观察。

        Args:
            action(string): 动作：open_door、continue_journey、walk、walk_to、look_around、listen、ask、wait、mark、marks、where_am_i、postcard、souvenir、give_souvenir。
            to(string): 开门时的目的地，可留空随机降落。
            direction(string): 行走方向，支持 N/NE/E/SE/S/SW/W/NW、forward、uphill、toward_sea。
            distance_km(number): 行走距离（公里）。
            place(string): walk_to 的命名地点。
            topic(string): ask 时想询问的主题。
            name(string): 地点标记名称。
            note(string): 地点标记备注。
            text(string): 明信片正文。
            hours(number): 原地等待小时数。
            seconds(number): 收听电台秒数。
            overwrite(boolean): 是否覆盖同名地点标记。
        """
        try:
            result = await dispatch(action, to=to, direction=direction, distance_km=distance_km, place=place, topic=topic, name=name, note=note, text=text, hours=hours, seconds=seconds, overwrite=overwrite)
            yield event.plain_result(_text(result))
        except Exception as error:
            logger.exception(f"乌有乡动作失败：{action}")
            yield event.plain_result(f"乌有乡动作失败：{error}")

    @filter.command("nowhere")
    async def nowhere_command(self, event: AstrMessageEvent):
        """乌有乡手动入口：/nowhere [状态|开门 地点|走 方向 距离|观察|继续]"""
        raw = event.message_str.strip().split()[1:]
        command = raw[0] if raw else "状态"
        aliases = {"状态": "where_am_i", "开门": "open_door", "走": "walk", "观察": "look_around", "继续": "continue_journey", "收听": "listen", "标记": "mark", "明信片": "postcard"}
        action = aliases.get(command, command)
        args: dict[str, Any] = {}
        if action == "open_door" and len(raw) > 1:
            args["to"] = " ".join(raw[1:])
        elif action == "walk":
            args["direction"] = raw[1] if len(raw) > 1 else "forward"
            args["distance_km"] = float(raw[2]) if len(raw) > 2 else 2
        elif action == "mark" and len(raw) > 1:
            args["name"] = " ".join(raw[1:])
        elif action == "postcard" and len(raw) > 1:
            args["text"] = " ".join(raw[1:])
        try:
            yield event.plain_result(_text(await dispatch(action, **args)))
        except Exception as error:
            yield event.plain_result(f"乌有乡动作失败：{error}")

    async def terminate(self):
        logger.info(f"乌有乡插件已停止，旅程数据仍保留在 {DATA_ROOT}")
