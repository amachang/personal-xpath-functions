import re
import sys
from lxml.etree import _Element, FunctionNamespace
from w3lib.html import HTML5_WHITESPACE
from typing import TypeVar, Any, Union, List, Tuple, Optional

class_separator_regex = re.compile(f"[{HTML5_WHITESPACE}]+")


def has_class(
    context: Any, node_set_or_cls: Union[List[_Element], str], *rest_cls_list: str
) -> bool:
    context_node, *cls_list = _fix_args(context, node_set_or_cls, *rest_cls_list)
    if len(cls_list) < 1:
        raise ValueError("XPath error: has-class must have at least 1 class name")

    if context_node is None:
        return False

    assert isinstance(context_node, _Element)

    node_cls_value = context_node.get("class")
    if node_cls_value is None:
        return False

    node_cls_list = class_separator_regex.split(node_cls_value)
    node_cls_list = [cls for cls in node_cls_list if 0 < len(cls)]
    node_cls_set = set(node_cls_list)
    if all(cls in node_cls_set for cls in cls_list):
        return True
    else:
        return False


T = TypeVar("T")
U = TypeVar("U")


def _fix_args(
    context: Any, first_arg: Union[List[_Element], T], *rest_args: U
) -> Tuple[Union[Optional[_Element], T, U], ...]:
    if isinstance(first_arg, list):
        if 0 < len(first_arg):
            node = first_arg[0]
        else:
            node = None
        isinstance(node, _Element)
        return node, *rest_args
    else:
        node = context.context_node
        isinstance(node, _Element)
        return node, first_arg, *rest_args


def _register_functions() -> None:
    ns = FunctionNamespace(None)
    for name, value in vars(sys.modules[__name__]).items():
        if callable(value) and not re.match(r"^_", name):
            name = re.sub(r"_", "-", name)
            ns[name] = value


_register_functions()
