import re
import sys
import inspect
from lxml.etree import _Element, FunctionNamespace
from w3lib.html import HTML5_WHITESPACE
from typing import TypeVar, Any, Union, List, Tuple, Optional, Callable, cast
from typeguard import check_type, TypeCheckError, typechecked
from typing_extensions import get_args, get_origin, assert_type

class_separator_regex = re.compile(f"[{HTML5_WHITESPACE}]+")

NodeType = Union[_Element, str]
NodeSetType = List[NodeType]
ValueType = Union[bool, float, str, NodeSetType]


@typechecked
def has_class(context: Any, *args: ValueType) -> bool:
    types = Tuple[str, ...]
    context_node, cls_list = fix_args(
        context,
        *args,
        types=types,
        optional_context_node=True,
    )
    cls_list = cast(types, cls_list)
    expected_cls_set = set(cls_list)

    if not isinstance(context_node, _Element):
        return False

    node_cls_value = context_node.get("class")
    if node_cls_value is None:
        return False

    node_cls_list = class_separator_regex.split(node_cls_value)
    node_cls_list = [cls for cls in node_cls_list if 0 < len(cls)]
    node_cls_set = set(node_cls_list)
    if all(cls in node_cls_set for cls in expected_cls_set):
        return True
    else:
        return False


@typechecked
def re_match(context: Any, *args: ValueType) -> bool:
    types = Tuple[str, str, Optional[str]]
    context_node, fixed_args = fix_args(context, *args, types=types)
    target, pattern, flags_text = cast(types, fixed_args)
    flag = parse_regex_flags_text(flags_text)

    match = re.search(pattern, target, flag)
    return match is not None


@typechecked
def re_sub(context: Any, *args: ValueType) -> str:
    types = Tuple[str, str, str, Optional[str]]
    context_node, fixed_args = fix_args(context, *args, types=types)
    target, pattern, template, flags_text = cast(types, fixed_args)
    flag = parse_regex_flags_text(flags_text)

    return re.sub(pattern, template, target, flag)


@typechecked
def table_mapped_keys(context: Any, *args: ValueType) -> NodeSetType:
    context_node, () = fix_args(
        context,
        *args,
        types=Tuple[()],
        optional_context_node=True,
    )

    if not isinstance(context_node, _Element):
        return []

    tag_name = context_node.tag

    result: NodeSetType = []
    if tag_name == "table":
        result.extend(
            cast(
                List[str],
                context_node.xpath(
                    "(./tbody | ./thead | ./tfoot | .)/tr/*[name() = 'td' or name() = 'th'][1]/text()"
                ),
            )
        )
    elif tag_name == "dl":
        result.extend(cast(List[str], context_node.xpath("./dt/text()")))
    else:
        raise ValueError(f"Unsupported element: {tag_name}")

    return result


@typechecked
def table_mapped_value(context: Any, *args: ValueType) -> NodeSetType:
    context_node, (key,) = fix_args(
        context,
        *args,
        types=Tuple[str],
        optional_context_node=True,
    )
    assert isinstance(key, str)

    if not isinstance(context_node, _Element):
        return []

    tag_name = context_node.tag

    result: NodeSetType = []
    if tag_name == "table":
        result.extend(
            cast(
                List[_Element],
                context_node.xpath(
                    "(./tbody | ./thead | ./tfoot | .)/tr/*[name() = 'td' or name() = 'th'][1][re-match(normalize-space(.), $pattern)]/following-sibling::*[name() = 'td' or name() = 'th']",
                    pattern=f"^{re.escape(key)}$",
                ),
            )
        )
    elif tag_name == "dl":
        dt_el_list = cast(
            List[_Element],
            context_node.xpath(
                "./dt[re-match(normalize-space(.), $pattern)]",
                pattern=f"^{re.escape(key)}$",
            ),
        )
        result = []
        for dt_el in dt_el_list:
            sibling_el_list = cast(
                List[_Element],
                dt_el.xpath(
                    "./following-sibling::*[name() = 'dt' or name() = 'dd']",
                ),
            )
            for sibling_el in sibling_el_list:
                if sibling_el.tag == "dd":
                    result.append(sibling_el)
                else:
                    break
    else:
        raise ValueError(f"Unsupported element: {tag_name}")

    return result


@typechecked
def parse_regex_flags_text(flags_text: Optional[str]) -> int:
    flag = 0
    if flags_text is not None:
        for flag_character in flags_text:
            flag_character = flag_character.lower()
            if flag_character == "a":
                flag |= re.A
            elif flag_character == "i":
                flag |= re.I
            elif flag_character == "m":
                flag |= re.M
            elif flag_character == "s":
                flag |= re.S
            else:
                raise ValueError(f"Unknown regex flag: {flag_character}")
    return flag


@typechecked
def fix_args(
    context: Any,
    *org_args: ValueType,
    types: Any,
    optional_context_node: bool = False,
) -> Tuple[Optional[NodeType], Tuple[Optional[ValueType], ...]]:
    assert get_origin(types) == tuple

    function_name = "<unknown function>"

    current_frame = inspect.currentframe()
    if current_frame is not None:
        previous_frame = current_frame.f_back
        if previous_frame is not None:
            previous_frame_info = inspect.getframeinfo(previous_frame)
            function_name = previous_frame_info[2]

    if optional_context_node:
        if 0 < len(org_args) and is_node_set_type(org_args[0]):
            assert isinstance(org_args[0], list)
            if 0 < len(org_args[0]):
                context_node = org_args[0][0]
            else:
                context_node = None
            args = org_args[1:]
        else:
            context_node = context.context_node
            args = org_args
    else:
        context_node = context.context_node
        args = org_args

    type_args = get_args(types)
    if type_args == ((),):
        type_args = ()
    has_ellipsis = 0 < len(type_args) and type_args[-1] == Ellipsis
    if has_ellipsis:
        type_args = type_args[:-1]
    else:
        type_args = type_args

    converted_args: List[Optional[ValueType]] = []
    for index, type_arg in enumerate(type_args):
        if index < len(args):
            actual_type_arg = strip_optional_type(type_arg)
            converted_args.append(convert_value(args[index], actual_type_arg))
        else:
            if get_origin(type_arg) == Union:
                sub_types = get_args(type_arg)
                if len(sub_types) == 2 and type(None) in sub_types:
                    converted_args.append(None)
                else:
                    raise ValueError(
                        f"Invalid union type: {type_arg} in {function_name}"
                    )
            else:
                raise ValueError(
                    f"{function_name} expected {len(type_args)} arguments, but given {len(args)} arguments"
                )

    if has_ellipsis:
        last_type_arg = type_args[-1]
        last_actual_type_arg = strip_optional_type(last_type_arg)
        for arg in args[len(type_args) :]:
            converted_args.append(convert_value(arg, last_actual_type_arg))
    else:
        if len(type_args) < len(args):
            raise ValueError(
                f"{function_name} expected {len(type_args)} arguments, but given {len(args)} arguments"
            )

    return context_node, tuple(converted_args)


@typechecked
def strip_optional_type(original_type: Any) -> Any:
    if get_origin(original_type) == Union:
        sub_types = get_args(original_type)
        if len(sub_types) == 2:
            try:
                index = sub_types.index(type(None))
                return sub_types[1 if index == 0 else 0]
            except ValueError:
                return original_type
        else:
            return original_type
    else:
        return original_type


@typechecked
def convert_value(value: ValueType, value_type: Any) -> ValueType:
    origin_type = get_origin(value_type)
    if origin_type == list:
        if isinstance(value, list):
            return value
        else:
            raise ValueError(
                f"Any primitive types cannot convert to NodeSet: {origin_type}"
            )
    elif origin_type is None:
        primitive_value_type = value_type
        assert primitive_value_type in {float, str, bool}

        if isinstance(value, primitive_value_type):
            return cast(Union[float, str, bool], value)
        else:
            if isinstance(value, list):
                if primitive_value_type == bool:
                    return 0 < len(value)

                first_node = None
                if 0 < len(value):
                    first_node = value[0]

                if first_node is None:
                    str_value = ""
                elif isinstance(first_node, str):
                    str_value = first_node
                else:
                    str_value = cast(
                        str,
                        first_node.xpath("string(.)") if first_node is not None else "",
                    )

                if primitive_value_type == str:
                    return str_value

                assert primitive_value_type == float
                try:
                    return float(str_value)
                except ValueError:
                    return float("nan")
            else:
                return cast(Union[float, str, bool], primitive_value_type(value))
    else:
        raise ValueError(f"Unsupported non premitive type: {value_type}")


@typechecked
def is_node_set_type(obj: Any) -> bool:
    if isinstance(obj, list):
        return all(isinstance(el, _Element) or isinstance(el, str) for el in obj)
    else:
        return False


@typechecked
def register_default_functions() -> None:
    module_dict = vars(sys.modules[__name__])
    export_function_names = {
        "has_class",
        "table_mapped_keys",
        "table_mapped_value",
        "re_match",
        "re_sub",
    }
    for name in export_function_names:
        fn = module_dict[name]
        assert callable(fn)
        name = re.sub(r"_", "-", name)
        register_function(name, fn)


@typechecked
def register_function(function_name: str, fn: Callable) -> None:
    ns = FunctionNamespace(None)
    ns[function_name] = fn


register_default_functions()
