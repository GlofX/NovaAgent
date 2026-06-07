"""
tools.py —— Agent 的“手和脚”

大模型本身只会读文字、写文字，不能真的打开文件或计算。
所以我们把 Python 函数包装成工具，让 Agent 想做事时可以“借用”这些手脚。
"""


# 先定义一个读文件工具，Agent 想看本地文件时就会用它。
def read_file(path: str):
    # 这句说明这个函数的用途：给它一个路径，它会把文件内容读出来。
    """读取本地文件"""

    # 模拟
    if not path.endswith(".txt"):
        return "Error: 只支持 .txt 文件"


    # 读文件可能失败，比如路径写错了，所以先准备一个“兜底网”。
    print('###########  调用了read_file（）函数#####################')
    try:
        # 打开指定文件，encoding='utf-8' 表示按中文友好的方式读取。
        with open(path, 'r', encoding='utf-8') as f:
            # 把文件里的所有文字一次性读出来，再交还给 Agent。
            return f.read()
    except Exception as e:
        return str(e)


# 再定义一个计算器工具，Agent 想算数学表达式时就会用它。
def calculator(expression: str):
    """计算数学表达式"""
    print('###########  调用了calculator（）函数#####################')
    try:
        # eval 会把字符串当成 Python 表达式执行；这里适合教学演示，正式项目不要直接执行用户输入。
        return eval(expression)
    except Exception as e:
        return str(e)


# 这是工具“通讯录”：大模型说出工具名字后，Python 就靠它找到真正要调用的函数。
AVAILABLE_TOOLS = {
    # 当大模型说 Action 是 read_file，就调用上面的 read_file 函数。
    "read_file": read_file,
    # 当大模型说 Action 是 calculator，就调用上面的 calculator 函数。
    "calculator": calculator
}


# 这是给大模型看的“工具说明书”，告诉它有哪些工具、每个工具要什么参数。
TOOL_SCHEMA = [
    {
        "name": "read_file",
        "description": "读取指定路径的文件内容",
        "parameters": {"path": "string"}
    },
    {
        "name": "calculator",
        "description": "计算数学表达式，如 '1 + 2 * 3'",
        "parameters": {"expression": "string"}
    }
]
