"""
sysagent.py —— 最简 Agent 的“主程序”

这里把三样东西串起来：大模型是“大脑”，tools.py 里的函数是“手脚”，循环是“导演”。
程序会让大模型先想一想，再决定要不要调用工具，拿到工具结果后继续思考，直到给出最终答案。
"""
import json
import os

from openai import OpenAI

from prompt import SYSTEM_PROMPT
from tools import AVAILABLE_TOOLS


class SimpleAgent:


    # 简单的滑动窗口截断（防止爆 Token）
    MAX_HISTORY = 10
    BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def __init__(self):
        """
        history: 保存对话上下文，agent 的记忆本。
        """
        self.client = OpenAI(base_url=SimpleAgent.BASE_URL, api_key=os.getenv("AI_DASHSCOPE_API_KEY"))
        # 初始对话先放 system 消息，相当于开场前先告诉大模型游戏规则。
        # SYSTEM_PROMPT 会告诉它有哪些工具，以及必须用 Thought/Action 这种格式回答。
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]

    # run 是 Agent 的主循环：用户给任务后，它会反复“思考 → 动手 → 看结果”。
    def run(self, user_task: str, max_steps=10):
        """
        :param user_task: 用户交给 Agent 的任务，比如“读取 test.txt 并计算数字之和”。
        :param max_steps: 最多让 Agent 思考几轮，防止它一直绕圈停不下来。
        :return: 这个演示版直接打印过程，不额外返回结果。
        """
        # 把用户刚说的话存进“记忆本”，这样大模型下一次调用时能看到任务。
        self.history.append({"role": "user", "content": user_task})

        # 开始循环，让 Agent 自己决定每一步要不要用工具、用哪个工具。
        for step in range(max_steps):

            print(f"\n--- Step {step + 1} ---")

            if len(self.history) > SimpleAgent.MAX_HISTORY:
                # 保留 System Prompt 和最近 N 条
                self.history = [self.history[0]] + self.history[-SimpleAgent.MAX_HISTORY:]

            # 第 1 步：调用 LLM，让“大脑”根据历史记录继续思考。
            response = self.client.chat.completions.create(
                model="qwen3.6-plus",
                messages=self.history,
                temperature=0,
                # 指定输出格式
                response_format={"type": "json_object"}
            )

            json_str = json.dumps(response.model_dump(), ensure_ascii=False, indent=2)
            print(f'返回报文：{json_str}')
            content = response.choices[0].message.content
            print(f'大模型：\n {content}', end='\n---------------------\n')

            # 把大模型刚才的回复也存进“记忆本”，下一轮它能接着自己的思路往下走。
            self.history.append({"role": "assistant", "content": content})

            # 2. 解析 LLM 的 JSON 输出
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                print(f"❌ JSON 解析失败: {e}")
                # 添加一个错误消息到历史，帮助模型修正
                self.history.append({
                    "role": "user",
                    "content": f"你的响应不是有效的 JSON 格式。请确保输出合法的 JSON。"
                })
                continue

            # 3. 判断是否结束
            if result.get("is_final") is True:
                final_answer = result.get("final_answer", "")
                print("\n✅ Task Completed!")
                print(f"💬 Final Answer: {final_answer}")
                break

            action, action_input = self._parse_action(dict(result))

            # 4. 如果这一轮没有解析出工具名，就先跳过，进入下一轮让大模型继续说清楚。
            if not action:
                continue

            print(f'函数:{action} ,参数： {action_input}')

            # 第 5 步：执行工具；关键点是工具由 Python 执行，不是大模型自己执行。
            observation = self._execute_tool(action, action_input)
            # 打印工具返回结果，Observation 就像工具递回来的“小纸条”。
            print(f"Observation:\n {observation}")

            #6. ✅ 错误反思
            if "Error" in observation or "error" in observation.lower():
                reflection_prompt = (
                    f"你刚才调用工具失败了，错误信息是：{observation}。"
                    f"请反思原因并修正参数，不要重复同样的错误。"
                )
                self.history.append({
                    "role": "user",
                    "content": reflection_prompt
                })


            # 第 7 步：把工具结果塞回记忆本，让大模型看到“刚才动手后的结果”。
            self.history.append({
                # 这里用 user 角色模拟外部世界告诉 Agent：工具执行结果来了。
                "role": "user",
                # Observation 后面加一句“请继续思考”，引导大模型进入下一轮推理。
                "content": f"Observation: {observation}\n请继续思考。"
            })

    # _parse_action 负责从大模型的一大段文字里，抠出“工具名”和“工具参数”。
    def _parse_action(self, result: dict):

        """
         从大模型返回的 JSON 中解析 action 和 action_input
         """

        # 防御性编程：如果不是 dict，直接返回
        if not isinstance(result, dict):
            return None, None

        action = None
        action_input = None

        action = result.get("action")
        action_input = result.get("action_input", {})

        # 如果 action 为空或显式设置为 null
        if not action or action == "null":
            return None, None

        return action, action_input


    def _execute_tool(self, action: str, action_input: dict):
        """
        _execute_tool 负责真正调用 Python 函数，也就是让 Agent 的“手脚”开始干活。
        :param action: 函数名
        :param action_input:  参数
        :return:
        """
        # 先检查工具名在不在通讯录里，防止大模型瞎编一个不存在的工具。
        if action not in AVAILABLE_TOOLS:
            # 如果工具不存在，就返回错误文字，让大模型知道它选错工具了。
            return f"Error: Tool '{action}' not found."
        # 从工具通讯录里拿到真正的 Python 函数。
        tool_func = AVAILABLE_TOOLS[action]

        # 真正执行工具时也可能出错，所以再加一层兜底。
        try:
            # **action_input 会把字典拆成关键字参数，好比把包裹拆开后逐件交给函数。
            result = tool_func(**action_input)
            print(f'执行函数结果： {str(result)}')

            return str(result)

        except Exception as e:
            # 把执行错误返回给大模型，让它有机会根据错误继续调整。
            return f"Execution Error: {e}"


# 只有直接运行这个文件时，下面的示例才会执行；被别的文件导入时不会自动跑。
if __name__ == "__main__":

    agent = SimpleAgent()
    # agent.run("请读取当前目录下的 test.txt 文件，并计算出文件中数字的和。")
    # 让它读一个格式错误或者不存在的文件
    agent.run("请读取当前目录下的 test.t 文件，并计算出文件中数字的和。")
    # agent.run("请读取当前目录下的 not_exist.txt 文件，并计算出文件中数字的和。")


r"""
下面是一段可能的运行效果示例：

D:\env\conda\envs\NovaAgent\python.exe E:\codes\py\NovaAgent\01RootAgent\rootagent.py

--- Step 1 ---

Thought: 用户要求读取 `test.txt` 文件并计算其中数字的和。首先，我需要读取该文件的内容。
Action: read_file
Action Input: {"path": "test.txt"}
Observation: 1111

--- Step 2 ---
Action: calculator
Action Input: {"expression": "1+1+1+1"}
Observation: 4

--- Step 3 ---
Final Answer: 文件 test.txt 中的数字之和为 4。

Task Completed!

Process finished with exit code 0
"""
