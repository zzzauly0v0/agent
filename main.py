import json

from domain import server


def to_dict(obj):
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    if hasattr(obj, "__dict__"):
        return {k: to_dict(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    if isinstance(obj, list):
        return [to_dict(i) for i in obj]
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    return obj


def main() -> None:
    response = server.client.responses.create(
        model=server.model_name,
        reasoning={"effort": "low"},
        instructions="你扮演一位数学家",
        input="你觉得深度学习中最重要的是什么",
    )
    print(json.dumps(to_dict(response), indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
