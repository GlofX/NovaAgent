# NovaAgent — 从零手写 AI Agent 

NovaAgent 是一个从零开始构建 AI Agent 的项目。

这个项目的重点不是堆框架、堆概念，而是用尽量清晰的 Python 代码，把 Agent 最底层的工作方式拆开给你看：大模型如何思考、工具如何执行、循环如何把它们串起来。

## 项目简介

 像CrewAI、LangChain、AutoGen 这类框架很强大，但也容易让人一上来就陷进大量名词里：Agent、Task、Tool、Memory、Planner、Executor、Workflow……

NovaAgent 选择反过来：

> 先不用重型框架，先用纯 Python 把 Agent 的骨架手写出来。

等理解了底层原理，再去看各种框架，就会更容易知道它们到底在封装什么。

## 核心概念

在 NovaAgent 里，我们先把 Agent 拆成几个最基础的零件：

| 概念 | 作用 | 形象理解 |
| --- | --- | --- |
| LLM Client | 调用大模型 | Agent 的大脑 |
| Tools | 执行具体动作 | Agent 的手脚 |
| Prompt | 约束大模型行为 | 写给大脑的规则书 |
| Loop | 串联思考和行动 | Agent 的工作节奏 |
| Observation | 工具执行结果 | 手脚干完活递回来的小纸条 |
| History | 保存上下文 | Agent 的短期记忆 |

一个最小 Agent 的运行方式可以概括为：

```text
用户提出任务
    ↓
大模型思考下一步
    ↓
大模型决定调用工具
    ↓
Python 执行真实工具
    ↓
工具结果返回给大模型
    ↓
大模型继续思考
    ↓
输出最终答案
```

## 教程目录

| 模块 | 内容 | 难度 |
| --- | --- | --- |
| `01RootAgent` | 最简 Agent：LLM + Tools + Loop | 入门 |



后续模块可以在这个基础上继续扩展。



## 项目结构

```text
NovaAgent/
├── 01RootAgent/
│   ├── rootagent.py   # 最简 Agent 主程序
│   ├── tools.py       # 工具函数定义
│   ├── prompt.py      # 系统提示词
│   ├── test.txt       # 示例输入文件
│   └── README.md      # 01RootAgent 模块说明
└── README.md          # 项目总说明
```

## 快速开始

### 1. 安装依赖

当前模块使用 OpenAI 兼容 SDK：

```bash
pip install openai
```

### 2. 配置 API Key

`01RootAgent` 默认使用阿里百炼 OpenAI 兼容接口，代码会读取这个环境变量：

```text
AI_DASHSCOPE_API_KEY
```

bash 示例：

```bash
export AI_DASHSCOPE_API_KEY="你的阿里百炼 API Key"
```

Windows PowerShell 示例：

```powershell
$env:AI_DASHSCOPE_API_KEY="你的阿里百炼 API Key"
```



> 大模型负责“想”，Python 工具负责“做”，循环负责“让它们配合”。

## 说明

本项目是个人学习和实践过程中的整理。由于本人水平有限，Python 也算是第二语言，代码、注释和文档里难免会有不规范或理解不到位的地方。

如果你发现问题，欢迎指出；也请多多包涵。

## 设计哲学

NovaAgent 的设计哲学很简单：

1. 先理解本质，再使用框架。
2. 先跑通最小闭环，再逐步增加能力。
3. 注释要像讲故事，让普通人也能看懂。
4. 每一章都尽量做到可运行、可阅读、可修改。

如果你能看懂 `01RootAgent`，就已经抓住了 Agent 的第一性原理。
