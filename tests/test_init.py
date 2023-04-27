from lxml import etree
from lxml.etree import _Element
from personal_xpath_functions import *
import pytest
from typing import cast, List
from math import isnan


def test_has_class() -> None:
    root = etree.fromstring(
        "<p><a class='foo bar baz'>111</a><b class='foo aaa bbb ccc'>222</b></p>"
    )

    nodes = cast(List[_Element], root.xpath("//*[has-class('foo')]"))
    assert len(nodes) == 2
    assert [node.tag for node in nodes] == ["a", "b"]

    nodes = cast(List[_Element], root.xpath("//*[has-class('foo', 'bar')]"))
    assert isinstance(nodes, list)
    assert len(nodes) == 1
    assert [node.tag for node in nodes] == ["a"]

    nodes = cast(List[_Element], root.xpath("//*[has-class('foo', 'ccc')]"))
    assert [node.tag for node in nodes] == ["b"]

    assert root.xpath("has-class(//a, 'foo', 'bar')") == True
    assert root.xpath("has-class(//b, 'foo', 'bar')") == False
    assert root.xpath("has-class(//c, 'foo')") == False

    with pytest.raises(ValueError):
        root.xpath("//a[has-class()]")

    with pytest.raises(ValueError):
        root.xpath("has-class(//a)")


def test_re_match() -> None:
    root = etree.fromstring(
        """
        <body>
            <div>
                <h1>section foo</h1>
                <a href="bar">baz</a>
                <a href="boo">far</a>
            </div>
            <div>
                <h1>section aaa</h1>
                <a href="bbb">ccc</a>
            </div>
        </body>
        """
    )

    values = cast(List[str], root.xpath(r".//div[re-match(h1, '\bfoo$')]//a/@href"))
    assert values == ["bar", "boo"]

    root = etree.fromstring("<div>aあa</div>")
    assert root.xpath("re-match(., '^\w+$')") == True
    assert root.xpath("re-match(., '^\w+$', 'a')") == False
    assert root.xpath("re-match(., '^\w\W\w$', 'A')") == True

    root = etree.fromstring("<div>aAa</div>")
    assert root.xpath("re-match(., '^a+$')") == False
    assert root.xpath("re-match(., '^a+$', 'I')") == True
    assert root.xpath("re-match(., '^A+$', 'i')") == True

    root = etree.fromstring("<div>foo\nbar</div>")
    assert root.xpath("re-match(., '^foo$\n^bar$')") == False
    assert root.xpath("re-match(., '^foo$\n^bar$', 'm')") == True
    assert root.xpath("re-match(., '^.{7}$')") == False
    assert root.xpath("re-match(., '^.{7}$', 's')") == True

    with pytest.raises(ValueError):
        root = etree.fromstring("<div>foo</div>")
        root.xpath("re-match(., '.', 'z')")


def test_re_sub() -> None:
    root = etree.fromstring(
        """
        <body>
            <div>
                <h1>section foo</h1>
                <p>foo</p>
                <a href="bar">baz</a>
            </div>
            <div>
                <h1>section aaa</h1>
                <p>bbb</p>
                <a href="ccc">ddd</a>
            </div>
        </body>
        """
    )

    values = cast(
        List[str],
        root.xpath(r".//div[re-sub(h1, '^section (\w+)$', '\g<1>') = p]//a/@href"),
    )
    assert values == ["bar"]


def test_table_mapped_keys_and_values() -> None:
    root = etree.fromstring(
        """
        <table>
            <tr>
                <td>foo</td>
                <th>bar</th>
            </tr>
            <tfoot>
                <tr>
                    <th>aaa</th>
                    <td>bbb</td>
                    <td>ccc</td>
                </tr>
                <tr><td>111</td></tr>
            </tfoot>
        </table>
        """
    )

    values = cast(List[str], root.xpath("table-mapped-keys(//table)"))
    assert len(values) == 2
    assert values == ["foo", "aaa"]

    values = cast(List[str], root.xpath("table-mapped-value(//table, 'foo')/text()"))
    assert len(values) == 1
    assert values[0] == "bar"

    values = cast(List[str], root.xpath("table-mapped-value(//table, 'aaa')/text()"))
    assert len(values) == 2
    assert values == ["bbb", "ccc"]

    root = etree.fromstring(
        """
        <dl>
            <dt>foo</dt>
            <dd>bar</dd>
            <dt>aaa</dt>
            <dd>bbb</dd>
            <dd>ccc</dd>
            <dt>111</dt>
        </dl>
        """
    )

    values = cast(List[str], root.xpath("table-mapped-keys(//dl)"))
    assert len(values) == 2
    assert values == ["foo", "aaa"]

    values = cast(List[str], root.xpath("table-mapped-value(//dl, 'foo')/text()"))
    assert len(values) == 1
    assert values[0] == "bar"

    values = cast(List[str], root.xpath("table-mapped-value(//dl, 'aaa')/text()"))
    assert len(values) == 2
    assert values == ["bbb", "ccc"]

    values = cast(List[str], root.xpath("table-mapped-value(//dl, '111')/text()"))
    assert len(values) == 0

    root = etree.fromstring("<b>foo</b>")
    with pytest.raises(ValueError):
        root.xpath("table-mapped-keys(//b)")

    with pytest.raises(ValueError):
        root.xpath("table-mapped-value(//b, 'foo')")


def test_fix_args() -> None:
    class DummyContext:
        context_node: _Element

        def __init__(self, context_node: _Element) -> None:
            self.context_node = context_node

    root_node = etree.fromstring("<div><p>foo</p></div>")
    inter_nodes = cast(List[_Element], root_node.xpath("//p"))
    assert 0 < len(inter_nodes)
    inter_node = inter_nodes[0]
    context = DummyContext(root_node)
    types = Tuple[bool, Optional[float], Optional[str], Optional[str]]

    context_node, fixed_args = fix_args(context, 1, 2, 3, 4, types=types)
    assert context_node == context.context_node
    assert fixed_args == (True, 2.0, "3", "4")

    context_node, fixed_args = fix_args(context, 1, 2, 3, types=types)
    assert context_node == context.context_node
    assert fixed_args == (True, 2.0, "3", None)

    context_node, fixed_args = fix_args(
        context, 1, 2, types=types, optional_context_node=True
    )
    assert context_node == context.context_node
    assert fixed_args == (True, 2.0, None, None)

    context_node, fixed_args = fix_args(
        context, [inter_node], True, types=types, optional_context_node=True
    )
    assert context_node == inter_node
    assert fixed_args == (True, None, None, None)

    with pytest.raises(ValueError):
        fix_args(context, 1, types=Tuple[Union[float, str]])

    with pytest.raises(ValueError):
        fix_args(context, 1, 1, types=Tuple[float, Union[float, str, bool]])

    with pytest.raises(ValueError):
        fix_args(context, 1, types=Tuple[float, Union[float, str, bool]])

    with pytest.raises(ValueError):
        fix_args(context, 1, 1, 1, types=Tuple[float, float])

    context_node, fixed_args = fix_args(
        context, 1, 1, [inter_node], types=Tuple[float, str, NodeSetType]
    )
    assert fixed_args == (1.0, "1", [inter_node])
    context_node, fixed_args = fix_args(
        context, 1, 1, ["foo", "bar"], types=Tuple[float, str, NodeSetType]
    )
    assert fixed_args == (1.0, "1", ["foo", "bar"])

    with pytest.raises(ValueError):
        fix_args(context, 1, 1, 1, types=Tuple[float, str, NodeSetType])

    context_node, fixed_args = fix_args(context, [inter_node], types=Tuple[bool])
    assert fixed_args == (True,)
    context_node, fixed_args = fix_args(context, ["foo"], types=Tuple[bool])
    assert fixed_args == (True,)
    context_node, fixed_args = fix_args(context, [], types=Tuple[bool])
    assert fixed_args == (False,)

    context_node, fixed_args = fix_args(context, [inter_node], types=Tuple[str])
    assert fixed_args == ("foo",)
    context_node, fixed_args = fix_args(context, ["bar"], types=Tuple[str])
    assert fixed_args == ("bar",)
    context_node, fixed_args = fix_args(context, [], types=Tuple[str])
    assert fixed_args == ("",)

    context_node, fixed_args = fix_args(context, [inter_node], types=Tuple[float])
    assert isnan(cast(float, fixed_args[0]))
    context_node, fixed_args = fix_args(context, ["bar"], types=Tuple[float])
    assert isnan(cast(float, fixed_args[0]))
    context_node, fixed_args = fix_args(context, ["1"], types=Tuple[float])
    assert fixed_args == (1.0,)
    context_node, fixed_args = fix_args(context, [], types=Tuple[float])
    assert isnan(cast(float, fixed_args[0]))
