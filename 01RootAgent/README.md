# 01RootAgent — 最简 Agent 入门教程

`01RootAgent` 是 NovaAgent 的第一个模块：用尽量少的 Python 代码，从零搭出一个能“自己思考、自己选工具、自己继续推理”的 AI Agent。

它不是为了做一个生产级框架，而是为了让你看清 Agent 最底层的运行原理。

## 这个模块是什么

一句话：**这是一个最小可运行 Agent。**

它能做到：

1. 接收用户任务。
2. 调用大模型思考下一步。
3. 从大模型回复里解析出要调用的工具。
4. 用 Python 真正执行工具。
5. 把工具结果再交给大模型。
6. 循环这个过程，直到大模型给出最终答案。

示例任务：

```text
请读取当前目录下的 test.txt 文件，并计算出文件中数字的和。
```

Agent 会先读取文件，再调用计算器，最后回答结果。

## 核心理念

我们先彻底抛弃 CrewAI / LangChain / AutoGen 这些“重型脚手架”。

不管多复杂的 Agent，拆到物理层面，大多只有三样东西：

| 组件 | 在本模块里对应什么 | 形象理解 |
| --- | --- | --- |
| 大脑 | LLM Client | 负责读题、思考、决定下一步 |
| 手脚 | Tools | 负责真正干活，比如读文件、算数 |
| 循环 | Loop | 负责让大脑和手脚一轮轮配合 |

也就是说，Agent 的本质可以先理解成一句话：

> 写一个循环，让大模型自己决定调用哪个 Python 函数。

## 文件结构

```text
01RootAgent/
├── rootagent.py   # 主程序：把大模型、工具和循环串起来
├── tools.py       # 工具函数：Agent 可以使用的“手脚”
├── prompt.py      # 系统提示词：告诉大模型必须按什么格式回答
├── test.txt       # 测试文件：给 read_file 工具读取
└── README.md      # 当前模块说明文档
```

## 每个文件负责什么

### `rootagent.py`

这是整个模块的主角。

它定义了 `SimpleAgent`，里面最重要的是：

- `__init__()`：准备大模型客户端和对话历史。
- `run()`：启动 Agent 循环。
- `_parse_action()`：从大模型回复里解析工具名和参数。
- `_execute_tool()`：根据工具名调用真实的 Python 函数。

可以把它想成一个小导演：

> 它不亲自读文件、不亲自算数，但它知道什么时候该问大模型、什么时候该让工具动手。

### `tools.py`

这是 Agent 的工具箱。

当前提供两个工具：

| 工具名 | 作用 |
| --- | --- |
| `read_file` | 读取本地文件内容 |
| `calculator` | 计算数学表达式 |

同时它还有两个关键变量：

- `AVAILABLE_TOOLS`：给 Python 用的工具通讯录。
- `TOOL_SCHEMA`：给大模型看的工具说明书。

### `prompt.py`

这是写给大模型的规则说明。

它要求大模型必须按下面这种格式回答：

```text
Thought: 我现在在想什么
Action: 我要调用哪个工具
Action Input: 工具参数
Observation: 工具结果，这里由系统填写
Final Answer: 最终答案
```

为什么要这么严格？

因为 Python 代码需要从大模型的文字里解析出 `Action` 和 `Action Input`。如果大模型想怎么写就怎么写，程序就很难知道它到底想调用哪个工具。

## 运行前准备

### 1. 安装 Python 依赖

本模块使用 OpenAI 兼容 SDK：

```bash
pip install openai
```

### 2. 配置 API Key

代码里读取的环境变量名是：

```text
AI_DASHSCOPE_API_KEY
```

如果你使用 bash，可以这样设置：

```bash
export AI_DASHSCOPE_API_KEY="你的阿里百炼 API Key"
```

如果你在 Windows PowerShell 中运行，可以这样设置：

```powershell
$env:AI_DASHSCOPE_API_KEY="你的阿里百炼 API Key"
```

## 运行方式

进入模块目录：

```bash
cd 01RootAgent
```

运行主程序：

```bash
python rootagent.py
```

你会看到类似这样的过程：

```text
--- Step 1 ---
Thought: 用户要求读取 test.txt 文件...
Action: read_file
Action Input: {"path": "test.txt"}
Observation: 1111

--- Step 2 ---
Action: calculator
Action Input: {"expression": "1+1+1+1"}
Observation: 4

--- Step 3 ---
Final Answer: 文件 test.txt 中的数字之和为 4。
```

## 执行流程

整个 Agent 的工作流可以理解成：

```text
用户提出任务
    ↓
run() 把任务写进 history
    ↓
调用大模型，让它思考下一步
    ↓
大模型输出 Thought / Action / Action Input
    ↓
_parse_action() 解析出工具名和参数
    ↓
_execute_tool() 调用真实 Python 函数
    ↓
工具返回 Observation
    ↓
把 Observation 写回 history
    ↓
大模型继续思考
    ↓
直到输出 Final Answer
```

这个流程也叫 ReAct 思路：

- Reason：先思考。
- Act：再行动。
- Observe：观察行动结果。
- Repeat：重复，直到解决问题。

## 如何添加一个新工具

假设你想给 Agent 增加一个“获取当前时间”的工具，可以分三步。

### 第一步：在 `tools.py` 写函数

```python
def get_time():
    return "现在是演示时间"
```

### 第二步：注册到 `AVAILABLE_TOOLS`

```python
AVAILABLE_TOOLS = {
    "read_file": read_file,
    "calculator": calculator,
    "get_time": get_time,
}
```

### 第三步：写进 `TOOL_SCHEMA`

```python
{
    "name": "get_time",
    "description": "获取当前时间",
    "parameters": {}
}
```

这样大模型在系统提示词里就能看到这个新工具，并有机会主动调用它。



看完`01RootAgent`，应该能理解：

- Agent 不神秘，本质上就是“大模型 + 工具 + 循环”。
- 大模型不会真的执行函数，真正干活的是 Python。
- Prompt 格式很重要，因为代码要靠格式解析动作。
- `history` 就是 Agent 的短期记忆。
- `Observation` 是工具结果回流给大模型的关键桥梁。

## 常见问题

### 1. 报错：没有 API Key

请确认你已经设置：

```text
AI_DASHSCOPE_API_KEY
```

并且当前终端能读取到这个环境变量。

### 2. 读取不到 `test.txt`

`read_file` 使用的是相对路径。

如果任务里写的是 `test.txt`，建议先进入 `01RootAgent` 目录再运行：

```bash
cd 01RootAgent
python rootagent.py
```

### 3. 大模型没有按格式输出怎么办

这个版本使用的是简易文本解析，所以依赖大模型遵守 `prompt.py` 里的格式。

如果模型输出不稳定，可以尝试：

- 把 `temperature` 保持为 `0`。
- 在 `SYSTEM_PROMPT` 中更强硬地要求固定格式。
- 后续升级为更稳的结构化工具调用。

### 4. `calculator` 里的 `eval()` 安全吗

在示例里，它可以很直观地展示“调用计算器工具”。

但在正式项目中，不要直接对用户输入使用 `eval()`，因为它可能执行危险代码。生产环境应该换成更安全的数学表达式解析器。

