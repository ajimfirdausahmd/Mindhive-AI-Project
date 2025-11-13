from fastapi import APIRouter, HTTPException, Query
import ast, operator as op
from typing import Union

router = APIRouter()

OPS = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv}
UNARY = {ast.UAdd: lambda x: x, ast.USub: lambda x: -x}

def _eval(node: ast.AST) -> Union[int, float]:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY:
        return UNARY[type(node.op)](_eval(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in OPS:
        left = _eval(node.left); right = _eval(node.right)
        try:
            return OPS[type(node.op)](left, right)
        except ZeroDivisionError:
            raise ZeroDivisionError("Division by zero.")
    if isinstance(node, ast.Expr):
        return _eval(node.value)
    raise ValueError("Invalid or unsupported expression.")

def safe_eval(expr: str) -> Union[int, float]:
    try:
        tree = ast.parse(expr, mode="eval")
        return _eval(tree.body)
    except ZeroDivisionError as zde:
        raise zde
    except Exception:
        raise ValueError("Invalid expression. Use numbers, + - * /, parentheses.")

@router.get("/calculator")
def calculator(expr: str = Query(..., description="Calculator tools")):
    expr = expr.strip()

    if not expr:
        raise HTTPException(status_code=400, detail="Empty expression.")
    try:
        result = safe_eval(expr)
        return {"ok": True, "expr": expr, "result": result}
    except ZeroDivisionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))