from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from domain import server

# == This is the response_format of CalendarEvent
class CalendarEvent(BaseModel):
    name: str = Field(description="事件名称")
    date: str = Field(description="事件日期,例如 'Friday'")
    participants: list[str] = Field(description="参与者姓名列表")

# == This is the response_format of MathReasoning 
class Step(BaseModel):
    explanation: str = Field(description="步骤解释")
    output: str = Field(description="每步的输出结果")

class MathReasoning(BaseModel):
    steps: list[Step] = Field(description="需要推理的步骤")
    final_answer: str = Field(description="最终结果答案")

# == This is the response_format of ContentCompliance
class Category(str, Enum):
    violence = "violence"
    sexual = "sexual"
    self_harm = "self_harm"

class ContentCompliance(BaseModel):
    is_violating: bool
    category: Optional[Category]
    explanation_if_violating: Optional[str]

SYSTEM_PROMPT_CALENDAR = """\
Extract calendar event information from the user message.

Respond with ONLY a JSON object, no prose, using EXACTLY these field names:
- "name": string, the event name
- "date": string, the event date
- "participants": array of strings, participant names
"""

SYSTEM_PROMPT_MATH = """\
You are a helpful math tutor. Guide the user through the solution step by step.

Respond with ONLY a JSON object, no prose, using EXACTLY these field names:
- "steps": array of objects, each object has:
    - "explanation": string, what this step does
    - "output": string, the result after this step
- "final_answer": string, the final answer
"""

SYSTEM_PROMPT_COMPLIANCE = """\
Determine if the user input violates specific guidelines and explain if they do.

Respond with ONLY a JSON object, no prose, using EXACTLY these field names:
- "is_violating": boolean, true if the content violates policies, false otherwise
- "category": string or null, must be exactly one of "violence", "sexual", or "self_harm" if is_violating is true, otherwise null
- "explanation_if_violating": string or null, a brief explanation of why the content is violating, or null if it is compliant
"""

completion = server.client.chat.completions.parse(
    model=server.model_name,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT_COMPLIANCE},
        {
            "role": "user",
            "content": "How do I prepare for a job interview?",
        },
    ],

    response_format=ContentCompliance,
)

import json

event = completion.choices[0].message.parsed
print(json.dumps(event.model_dump(), indent=2, ensure_ascii=False))
