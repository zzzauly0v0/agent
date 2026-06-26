# 学习 claude code 的设计模式

> `learn-cc` 文件夹下的代码是 claude code 的设计模式的学习代码，主要是为了学习 claude code 的设计模式而写的，大部分都是采用的
> [claude code](https://learn.shareai.run/zh) 【这篇文章的介绍】

## 完成的部分

- 分为五层架构

### 工具与执行

#### 1. Agent Loop

##### 请求体类型

`response` 作为最基本的返回体类型，采用 pydantic 进行封装，属于 `Message` 实体类。这里主要介绍 `content` 属性和 `stop_reason`。

**`stop_reason` 在 SDK 中主要有以下几类：**

1. `end_turn`
2. `max_tokens`
3. `stop_sequence`
4. `tool_use` —— 在 agent loop 中最重要，用于判断模型是否继续对话
5. `pause_turn`
6. `refusal`

**`content` 属性**是一个 list，里面包含若干 `ContentBlock`：

```python
block = response.content
# 使用 block.type 选择对应的属性
```

##### Agent Loop 流程说明

**整体循环：**

```
用户输入提问
    ↓
整合消息队列（messages）
    ↓
传入大模型（client.messages.create）
    ↓
是否使用工具？
  ├─ 是 → 执行工具，结果叠加进消息队列 → 回到"传入大模型"
  └─ 否 → 退出循环
```

**Anthropic SDK 中的 response 结构**

调用 `client.messages.create(...)` 后返回一个 `Message` 对象，核心字段是：

- `response.role`：固定为 `"assistant"`
- `response.content`：一个 **list**，里面是若干个 content block

`content` 中的 block 共有 12 种类型，按 SDK 定义如下：

| Block 类型 | 说明 |
|---|---|
| `TextBlock` | 模型输出的文本内容 |
| `ThinkingBlock` | 模型的推理过程（开启 extended thinking 时出现） |
| `RedactedThinkingBlock` | 被屏蔽 / 加密的推理内容 |
| `ToolUseBlock` | 模型请求调用**本地工具**（需要客户端自己执行并回传结果） |
| `ServerToolUseBlock` | 模型请求调用**服务端工具**（由 Anthropic 服务器执行） |
| `WebSearchToolResultBlock` | 服务端 web_search 工具的执行结果 |
| `WebFetchToolResultBlock` | 服务端 web_fetch 工具的执行结果 |
| `CodeExecutionToolResultBlock` | 服务端代码执行工具的结果 |
| `BashCodeExecutionToolResultBlock` | 服务端 bash 代码执行工具的结果 |
| `TextEditorCodeExecutionToolResultBlock` | 服务端文本编辑器工具的结果 |
| `ToolSearchToolResultBlock` | 服务端工具检索（tool_search）的结果 |
| `ContainerUploadBlock` | 代码执行容器中生成 / 上传的文件 |

**关键区分**：`ToolUseBlock`（本地工具）需要你自己写代码执行，并手动构造 `tool_result` 块传回去；其余以 `*ToolResultBlock` 命名的 block 都是**服务端工具**，执行和结果生成都在 Anthropic 一侧完成，直接以成品形式返回。

**代理循环中的处理逻辑**

1. 模型生成的 `response.content` 中，若包含 `ToolUseBlock`，说明模型请求调用本地工具。
2. 代理循环遍历 `content`，找出 `ToolUseBlock`，本地执行对应工具，将结果包装为 `tool_result` 类型的 block。
3. 把这一轮的 assistant 消息（即模型返回的完整 `content`）和工具执行结果（以 `role: user` 形式）都追加进 `messages`，传给下一轮调用。
4. 循环直到 `response.stop_reason != "tool_use"`，结束循环。
5. 取 `messages` 中**最新一条**消息的 `content`，遍历其中的 block，筛选出 `type == "text"` 的部分输出。

```python
final_content = messages[-1]["content"]
if isinstance(final_content, list):
    for block in final_content:
        if getattr(block, "type", None) == "text":
            print(block.text)
```

##### CC 与示例代码的区别

由于绝大情况下是并发的过程，对话都是流式输出的，可能提前出现 `tool_use` 导致 `stop_reason` 失效，因此需要采用其他方式。

CC 用 `needsFollowUp` 标志：接收到流式消息时，只要检测到 `tool_use` 块就设为 `true`。`QueryEngine.ts` 会从 `message_delta` 捕获真实 `stop_reason` 用于其他逻辑，但 query loop 本身靠 `needsFollowUp` 决定是否继续。

#### 2. Tool Use

> 后续添加自己的学习心得

#### 3. Permission

> 后续添加自己的学习心得

#### 4. Hooks

> 后续添加自己的学习心得
