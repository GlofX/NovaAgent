"""
rootagent.py —— 最简 Agent 的“主程序”

这里把三样东西串起来：大模型是“大脑”，tools.py 里的函数是“手脚”，循环是“导演”。
程序会让大模型先想一想，再决定要不要调用工具，拿到工具结果后继续思考，直到给出最终答案。
"""
import json
import os

# 引入 OpenAI 客户端；阿里百炼提供的是 OpenAI 兼容接口，所以可以用同一套 SDK 调用。
from openai import OpenAI


from prompt import SYSTEM_PROMPT
from tools import AVAILABLE_TOOLS


# SimpleAgent 是我们亲手搭出来的最小 Agent，把“大脑、手脚、循环”装进一个类里。
class SimpleAgent:

    # 初始化方法：每创建一个 Agent，就先准备好大模型客户端和对话记忆。
    def __init__(self):
        """
        history: 保存对话上下文，agent 的记忆本。
        """
        # BASE_URL 是大模型服务的地址，就像“大脑办公室”的门牌号。
        BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

        # client 是和大模型通话的“电话”；API Key 从环境变量里拿
        self.client = OpenAI(base_url=BASE_URL, api_key=os.getenv("AI_DASHSCOPE_API_KEY"))

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
            # 打印当前是第几轮，方便我们像看侦探剧一样追踪 Agent 的思路。
            print(f"\n--- Step {step + 1} ---")

            # 第 1 步：调用 LLM，让“大脑”根据历史记录继续思考。
            response = self.client.chat.completions.create(
                # 指定要使用的模型，这里用阿里百炼里的 qwen3.6-plus。
                model="qwen3.6-plus",
                # 把完整记忆本交给大模型，它才能知道前面发生过什么。
                messages=self.history,
                # temperature=0 表示尽量稳定输出，少一点随机发挥，方便我们解析格式。
                temperature=0
            )

            # OpenAI 兼容协议（阿里百炼 / 通义也完全一致），接口返回标准结构。
            # 如果想调试完整返回报文，可以把下面两行取消注释。
            # json_str = json.dumps(response.model_dump(), ensure_ascii=False, indent=2)
            # print(f'返回报文：{json_str}')

            # 从返回结果里取出大模型真正说的文字内容。
            content = response.choices[0].message.content
            # 把大模型这一轮的想法打印出来，方便观察它决定了什么。
            print(f'大模型：\n {content}', end='\n---------------------\n')

            # 把大模型刚才的回复也存进“记忆本”，下一轮它能接着自己的思路往下走。
            self.history.append({"role": "assistant", "content": content})

            # 第 2 步：如果大模型已经写出 Final Answer，说明它认为任务完成了。
            if "Final Answer:" in content:
                # 打印完成提示，然后跳出循环，不再继续调用工具。
                print("\nTask Completed!")
                # break 就像按下停止键，结束这次 Agent 任务。
                break

            # 第 3 步：从大模型输出里提取 Action 和 Action Input。
            # Action 是它想用哪个工具，Action Input 是它想给工具传什么参数。
            action, action_input = self._parse_action(content)

            # 如果这一轮没有解析出工具名，就先跳过，进入下一轮让大模型继续说清楚。
            if not action:
                # continue 表示“这轮先到这儿，直接开始下一轮”。
                continue

            # 第 4 步：执行工具；关键点是工具由 Python 执行，不是大模型自己执行。
            observation = self._execute_tool(action, action_input)
            # 打印工具返回结果，Observation 就像工具递回来的“小纸条”。
            print(f"Observation:\n {observation}")

            # 第 5 步：把工具结果塞回记忆本，让大模型看到“刚才动手后的结果”。
            self.history.append({
                # 这里用 user 角色模拟外部世界告诉 Agent：工具执行结果来了。
                "role": "user",
                # Observation 后面加一句“请继续思考”，引导大模型进入下一轮推理。
                "content": f"Observation: {observation}\n请继续思考。"
            })

    # _parse_action 负责从大模型的一大段文字里，抠出“工具名”和“工具参数”。
    def _parse_action(self, text: str):

        # 这是一个简易解析器：如果连 Action 都没有，说明大模型没要求调用工具。
        if "Action:" not in text:
            # 返回两个 None，告诉主循环“这轮没有可执行动作”。
            return None, None

        # 把大模型回复按行切开，后面就能一行一行找关键词。
        lines = text.split('\n')
        # action 先设为空，等找到 Action: 那行再填进去。
        action = None
        # action_input 也先设为空，等找到 Action Input: 那行再解析 JSON。
        action_input = None

        # 遍历每一行，就像在一张纸上逐行找“工具名”和“参数”。
        for line in lines:
            # 如果这一行以 Action: 开头，就说明后面跟着工具名。
            if line.startswith("Action:"):
                # 去掉 Action: 标签，只留下真正的工具名，并清理前后空格。
                action = line.replace("Action:", "").strip()
            # 如果这一行以 Action Input: 开头，就说明后面跟着工具参数。
            if line.startswith("Action Input:"):
                # 参数应该是 JSON，但大模型偶尔可能写歪，所以这里也加兜底。
                try:
                    # 去掉标签后，把 JSON 字符串解析成 Python 字典。
                    action_input = json.loads(line.replace("Action Input:", "").strip())
                # 如果 JSON 解析失败，就给一个空字典，避免程序直接崩掉。
                except:
                    # 空字典表示“没有拿到可用参数”。
                    action_input = {}

        # 把解析到的工具名和参数交还给主循环。
        return action, action_input

    # _execute_tool 负责真正调用 Python 函数，也就是让 Agent 的“手脚”开始干活。
    def _execute_tool(self, action: str, action_input: dict):

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
            # 工具结果统一转成字符串，方便塞回大模型的上下文。
            return str(result)
        # 如果函数执行失败，就抓住异常。
        except Exception as e:
            # 把执行错误返回给大模型，让它有机会根据错误继续调整。
            return f"Execution Error: {e}"


# 只有直接运行这个文件时，下面的示例才会执行；被别的文件导入时不会自动跑。
if __name__ == "__main__":
    # 创建一个 SimpleAgent，相当于请出一个会思考、会用工具的小助手。
    agent = SimpleAgent()
    # 测试：让 Agent 读取当前目录下的 test.txt，然后计算文件中数字的和。
    agent.run("请读取当前目录下的 test.txt 文件，并计算出文件中数字的和。")


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
