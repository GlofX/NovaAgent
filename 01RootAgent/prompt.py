"""
prompt.py —— 给 Agent 大脑的“行为规则书”

这段系统提示词会在对话一开始发给大模型，告诉它必须按固定格式说话。
只有格式稳定，后面的 Python 代码才能准确解析出它想调用哪个工具。
"""

import json

from tools import AVAILABLE_TOOLS, TOOL_SCHEMA


# SYSTEM_PROMPT 就像写给大模型的“考场规则”：必须按这个格式一步步回答。
SYSTEM_PROMPT = f"""
你是一个智能助手。你必须严格按照以下格式回答：

Thought: 你现在在想什么？
Action: 要调用的工具名（必须是 {list(AVAILABLE_TOOLS.keys())} 之一）
Action Input: 工具的参数（JSON格式）
Observation: （这里不用写，留给系统填充）
...（重复 Thought/Action/Action Input/Observation 直到你得出结论）
Final Answer: 给用户的最终答案

可用工具列表：
{json.dumps(TOOL_SCHEMA, indent=2)}
"""
