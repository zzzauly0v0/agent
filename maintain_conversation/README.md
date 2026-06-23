# maintain_conversation 排错与结构化输出笔记

记录在 DashScope 兼容端点(`qwen3.6-flash`)上跑 OpenAI Python SDK 结构化输出时遇到的一连串问题、根因和修法,作为后续接同类模型的参考。

---

## 1. 连接池优化(`domain/serve.py`)

### 改动前
- `Server` 只是一个 Pydantic 模型,存 `api_key` / `model_name`。
- 真正的 `OpenAI(...)` 客户端在 `main.py` 里临时创建,使用 httpx 默认连接池(无显式上限、无 keepalive、无超时拆分)。

### 改动后
- 把 `OpenAI` 客户端纳入 `Server`,启动时一次性构造,全进程复用。
- 底层换成显式配置的 `httpx.Client`:
  - `httpx.Limits(max_connections=100, max_keepalive_connections=20, keepalive_expiry=30)` —— 限制总并发,复用 TCP/TLS,避免每次重连。
  - `httpx.Timeout(connect=10, read=60, write=60, pool=5)` —— 拆开四种超时,防止 pool 等空闲连接卡死。
  - `max_retries=2` —— 利用 OpenAI SDK 自带指数退避。
- 全部参数通过 `OPENAI_POOL_*` / `OPENAI_*_TIMEOUT` 环境变量覆盖,生产调参不改代码。
- 启动时校验 `DASHSCOPE_API_KEY` / `MODEL`,缺了直接 `RuntimeError`,避免下游空值崩溃。
- `Server.close()` 用于优雅关闭。

异步场景把 `httpx.Client` 换成 `httpx.AsyncClient` + `AsyncOpenAI` 即可,池参数不变。

---

## 2. `ModuleNotFoundError: No module named 'domain'`

### 现象
在 `maintain_conversation/` 子目录里 `uv run chain_response.py`,报找不到 `domain`。

### 根因
Python 只把当前目录加进 `sys.path`,根目录的 `domain/` 包看不到。

### 修法
把项目本身做成可安装包,`uv sync` 会把它装成 editable,任意目录都能 `from domain import server`:

1. `pyproject.toml` 加上:
   ```toml
   [build-system]
   requires = ["hatchling"]
   build-backend = "hatchling.build"

   [tool.hatch.build.targets.wheel]
   packages = ["domain", "maintain_conversation"]
   ```
2. `maintain_conversation/__init__.py` 创建为空文件(包标识)。
3. `uv sync` 后输出 `+ agent==0.1.0 (from file:///...)`,即装好了。

---

## 3. `responses.parse` 返回自然语言导致 `json_invalid`

### 现象
```
pydantic_core.ValidationError: Invalid JSON: expected value at line 1 column 1
input_value="Here's the extracted event..."
```

### 根因
DashScope 兼容端点对 `/responses` 接口的结构化输出支持非常弱 —— 模型直接吐了一段自然语言,根本不是 JSON。

### 修法
切到兼容更成熟的 `/chat/completions`:

```python
completion = server.client.chat.completions.parse(...)
event = completion.choices[0].message.parsed
```

---

## 4. `ValidationError: Field required` —— 字段名对不上

### 现象
模型返回了合法 JSON,但字段名是 `event_name` / `step_by_step_guide` / `problem` 这种自创的,跟 Pydantic schema 对不上。

### 根因(关键)
DashScope 是**非 strict 结构化输出**:
- 它把 OpenAI 的 `json_schema` 降级成 `json_object` 模式。
- `json_object` 只保证返回**合法 JSON**,**不保证字段名匹配 schema**。
- OpenAI 官方端点的 strict 模式会在 token 级别按 schema 约束输出,DashScope 不会。
- 因此 `Field(description=...)` 在 DashScope 这边几乎无效。

### 修法
**在 system prompt 里把字段名硬编码列出来**,用提示工程兜底:

```python
SYSTEM_PROMPT_MATH = """\
You are a helpful math tutor. Guide the user through the solution step by step.

Respond with ONLY a JSON object, no prose, using EXACTLY these field names:
- "steps": array of objects, each object has:
    - "explanation": string, what this step does
    - "output": string, the result after this step
- "final_answer": string, the final answer
"""
```

切回 OpenAI 官方端点 + GPT-4o 时这段可以删掉,strict 模式接管。

---

## 5. `400 BadRequest: 'messages' must contain the word 'json'`

### 现象
```
openai.BadRequestError: Error code: 400 - InternalError.Algo.InvalidParameter:
'messages' must contain the word 'json' in some form, to use 'response_format' of type 'json_object'.
```

### 根因
DashScope 兼容层硬性校验:启用 `response_format` 时,prompt 里必须出现 "json" 字样。这是早期 OpenAI `json_object` 模式的限制,DashScope 抄了这条。OpenAI 现在的 strict 模式没这个要求。

### 修法
system prompt 里包含 "JSON" 即可(写"only a JSON object"等)。第 4 节的 prompt 模板天然满足。

---

## 6. 打印格式的迷思 —— 不是模型的问题,是 `print` 的问题

### 现象
直接 `print(event)` 输出:
```
steps=[Step(explanation='...', output='...')] final_answer='x = -15/4'
```
而不是想要的格式化 JSON。

### 根因
`completion.choices[0].message.parsed` 已经是 SDK 反序列化好的 **Pydantic 对象**,`print` 调的是它的 `__repr__`,不是 JSON。

### 三种打印方式

| 写法 | 输出 |
|---|---|
| `print(event)` | Python repr 风格 |
| `print(event.model_dump_json(indent=2))` | 格式化 JSON,中文转成 `\uXXXX` |
| `print(json.dumps(event.model_dump(), indent=2, ensure_ascii=False))` | 格式化 JSON,中文原样 |

要拿模型返回的**原始 JSON 字符串**,直接读 `completion.choices[0].message.content`。

---

## 7. OpenAI 官方示例 vs 当前代码 —— 差异速查表

| 方面 | OpenAI 官方 (GPT-4o) | 当前 (DashScope qwen) | 原因 |
|---|---|---|---|
| API 端点 | `client.responses.parse` | `client.chat.completions.parse` | `/responses` 在 DashScope 兼容很弱 |
| 模型 | `gpt-4o-2024-08-06` | `qwen3.6-flash` | 前者支持 strict,后者只有 `json_object` |
| 字段名约束 | schema 自动强制 | 必须 prompt 里硬编码 | 非 strict 不保证字段名 |
| prompt 必含 "json" | 不需要 | 必须 | `json_object` 模式校验 |
| `Field(description=...)` | 进 schema,模型会读 | 几乎无效 | 同上 |
| 取结果 | `response.output_parsed` | `completion.choices[0].message.parsed` | 响应结构不同 |

**切回 OpenAI 官方**:换 `api_key`、不传 `base_url`,官方示例可原样跑通。

---

## 8. 当前可工作的最小范式(给 DashScope 兼容端点)

```python
import json

from pydantic import BaseModel, Field

from domain import server


class Step(BaseModel):
    explanation: str = Field(description="步骤解释")
    output: str = Field(description="每步的输出结果")


class MathReasoning(BaseModel):
    steps: list[Step]
    final_answer: str


# 关键:prompt 里既要有 "JSON" 字样,又要把字段名列清楚
SYSTEM_PROMPT = """\
You are a helpful math tutor. Guide the user through the solution step by step.

Respond with ONLY a JSON object, no prose, using EXACTLY these field names:
- "steps": array of objects, each object has:
    - "explanation": string, what this step does
    - "output": string, the result after this step
- "final_answer": string, the final answer
"""

completion = server.client.chat.completions.parse(
    model=server.model_name,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "how can I solve 8x + 7 = -23"},
    ],
    response_format=MathReasoning,
)

event = completion.choices[0].message.parsed
print(json.dumps(event.model_dump(), indent=2, ensure_ascii=False))
```
---
## 问题

### 9.1 `response_format` vs `text_format` —— 两个 API 两套参数

OpenAI 同时维护着两个 API,结构化输出参数名不一样,容易混淆。

| 参数 | 属于哪个 API | 输入是什么 |
|---|---|---|
| `response_format` | **Chat Completions** (`client.chat.completions.*`) | 接受 Pydantic 类 / `{"type": "json_schema", ...}` / `{"type": "json_object"}` |
| `text_format` | **Responses** (`client.responses.parse`) | 只接受 Pydantic 类(SDK 帮你转 schema) |
| `text={"format": {...}}` | **Responses** (`client.responses.create`) | 原始 dict 写法,等价于上面那个 |

三种写法等价,只是接口和抽象层级不同:

```python
# A. Chat Completions + Pydantic
client.chat.completions.parse(messages=[...], response_format=MathReasoning)

# B. Responses + Pydantic(SDK 自动转 schema)
client.responses.parse(input=[...], text_format=MathReasoning)

# C. Responses + 原始 dict(完全手写 schema)
client.responses.create(input=[...], text={"format": {
    "type": "json_schema", "name": "math_response",
    "schema": {...}, "strict": True,
}})
```

**为什么有两个 API:**
- `Chat Completions`(2023):老 API,业界标准,所有兼容厂商都对着它做。
- `Responses`(2024):新 API,设计上更适合 agent 场景(支持 reasoning、conversations、tool 编排)。

**对 DashScope 的实测结论:**

| API 路径 | DashScope 兼容性 |
|---|---|
| `chat.completions` + `response_format=Model` | ⚠️ 部分支持,降级成 `json_object`,字段名靠 prompt 兜底 |
| `responses.parse` + `text_format=Model` | ❌ 静默忽略 `text_format`,模型直接吐 Markdown |
| `responses.create` + `text={"format": {...}}` | ❌ 同上,**不报 400,但拿不到结构化数据** |

新 API 在 DashScope 上反而更糟 —— 至少报错还能排查,静默忽略最致命。所以当前阶段坚持 `chat.completions.parse` 是正解。

---

### 9.2 `json_schema` vs `json_object` —— 严格程度差一个量级

两者都是 `response_format` 的 type,但保证级别完全不同。

| 维度 | `json_object` | `json_schema` (strict=true) |
|---|---|---|
| 保证什么 | 输出是合法 JSON | 合法 JSON **且严格匹配 schema** |
| 字段名 | 不约束,模型自己起 | 强制按 schema |
| 字段类型 | 不约束 | 强制(string/number/array 不会乱) |
| 必填字段 | 不约束,可能漏 | `required` 全部出现 |
| 额外字段 | 可能多出来 | `additionalProperties: false` 严格禁止 |
| prompt 必含 "json" | ✅ 必须 | ❌ 不需要 |
| 实现机制 | 后处理校验 JSON 合法性 | 解码层用 grammar/FSM **约束 token**,根本无法生成不合规输出 |
| 何时引入 | 早期 (2023, GPT-3.5/4) | 较新 (2024-08, GPT-4o-2024-08-06+) |

**直观例子。** 输入 `Extract event info from "Alice and Bob meet on Friday"`,要的字段是 `name / date / participants`。

`json_object` 模式下面这些都会通过校验,但下游 Pydantic 全炸:
```json
{ "event_name": "meet", "when": "Friday", "people": ["Alice", "Bob"] }
{ "name": "meet", "date": "Friday" }                              // 漏 participants
{ "name": "meet", "date": "Friday", "participants": "Alice, Bob" } // 类型错
```

`json_schema` strict 模式下**只可能**返回:
```json
{ "name": "meet", "date": "Friday", "participants": ["Alice", "Bob"] }
```

**为什么 strict 这么强:** 不是后处理校验,是在采样阶段每生成一个 token 之前就用编译好的 grammar 限制可选 token 集合。比如 schema 要求当前位置必须是 `"steps"`,那除了能拼出 `"steps"` 的 token,其他 token 概率直接置零。模型连"想错"都没机会。

**Pydantic 写法走的是哪条路?**

`response_format=MathReasoning` / `text_format=MathReasoning` 这种 Pydantic 写法,SDK 会把 Pydantic 模型转成 `json_schema` + `strict=true`,**不是 `json_object`**。所以官方代码看起来很短,其实底层走的是最强模式。

**这就解释了为什么 DashScope 上效果差** —— DashScope 的 `json_schema` 不是真 strict,服务端把它降级成 `json_object` 跑,strict 这层能力丢了。所以最终落到我们这边,只能用 prompt 工程模拟字段名约束。

---

## 经验总结

1. **连接池要显式配置**,默认值在生产环境往往是雷区。
2. **跨目录导入靠包安装**,不要靠 `sys.path` 魔法。
3. **兼容端点不等于完全兼容**,strict 结构化输出基本是 OpenAI 独占;在国产模型上要用提示工程补齐字段名。
4. **报错先看是哪一层**:HTTP 400 是端点校验,Pydantic ValidationError 是字段对不上,JSON parse error 是模型根本没出 JSON。
5. **`parsed` 是对象、`content` 是字符串**,打印格式按需选。
