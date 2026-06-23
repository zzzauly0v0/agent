import os

import httpx
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field

DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 连接池/超时调优 —— 通过环境变量覆盖,生产环境无需改代码
MAX_CONNECTIONS = int(os.getenv("OPENAI_POOL_MAX_CONNECTIONS", "100"))
MAX_KEEPALIVE = int(os.getenv("OPENAI_POOL_MAX_KEEPALIVE", "20"))
KEEPALIVE_EXPIRY = float(os.getenv("OPENAI_POOL_KEEPALIVE_EXPIRY", "30"))
CONNECT_TIMEOUT = float(os.getenv("OPENAI_CONNECT_TIMEOUT", "10"))
READ_TIMEOUT = float(os.getenv("OPENAI_READ_TIMEOUT", "60"))
WRITE_TIMEOUT = float(os.getenv("OPENAI_WRITE_TIMEOUT", "60"))
POOL_TIMEOUT = float(os.getenv("OPENAI_POOL_TIMEOUT", "5"))
MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "2"))


def _build_http_client() -> httpx.Client:
    limits = httpx.Limits(
        max_connections=MAX_CONNECTIONS,
        max_keepalive_connections=MAX_KEEPALIVE,
        keepalive_expiry=KEEPALIVE_EXPIRY,
    )
    timeout = httpx.Timeout(
        connect=CONNECT_TIMEOUT,
        read=READ_TIMEOUT,
        write=WRITE_TIMEOUT,
        pool=POOL_TIMEOUT,
    )
    return httpx.Client(limits=limits, timeout=timeout, http2=False)


class Server(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    api_key: str
    model_name: str
    base_url: str = DASHSCOPE_BASE_URL
    client: OpenAI = Field(default=None, repr=False)

    def model_post_init(self, __context) -> None:
        if self.client is None:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                http_client=_build_http_client(),
                max_retries=MAX_RETRIES,
            )

    def close(self) -> None:
        self.client.close()


api_key = os.getenv("DASHSCOPE_API_KEY")
MODEL = os.getenv("MODEL")

if not api_key or not MODEL:
    raise RuntimeError("环境变量 DASHSCOPE_API_KEY 和 MODEL 必须设置")

server = Server(api_key=api_key, model_name=MODEL)
