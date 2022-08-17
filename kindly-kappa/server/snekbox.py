import requests

EVAL_URL = "http://localhost:8060/eval"


def evaluate(code: str) -> str:
    """Evaluate code thanks to the snekbox API.

    Args:
        code: The code to evaluate.
    """
    response = requests.post(EVAL_URL, json={"input": code})
    return response.json()["stdout"]
