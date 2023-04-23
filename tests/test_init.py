from lxml import etree
from lxml.etree import _Element
import personal_xpath_functions
import pytest
from typing import cast, List


def test_misc() -> None:
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

    with pytest.raises(TypeError):
        root.xpath("//a[has-class()]")

    with pytest.raises(ValueError):
        root.xpath("has-class(//a)")
