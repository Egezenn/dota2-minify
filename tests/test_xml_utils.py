import defusedxml.ElementTree as ET
import pytest
from patch import xml_utils


@pytest.fixture
def sample_xml():
    xml_data = """
    <root>
        <Panel id="Main" class="container active">
            <Button id="Submit" class="btn primary" hittest="true">Submit</Button>
            <DOTAXThing id="Thing" class="Thing" attrib="val">Special</DOTAXThing>
        </Panel>
        <Panel id="Footer" hittest="false">
            <Label class="text-muted">Copyright</Label>
        </Panel>
    </root>
    """
    return ET.fromstring(xml_data)


def test_find_by_selector_tag(sample_xml):
    elem = xml_utils.find_by_selector(sample_xml, "Button")
    assert elem is not None
    assert elem.get("id") == "Submit"


def test_find_by_selector_id(sample_xml):
    elem = xml_utils.find_by_selector(sample_xml, "#Main")
    assert elem is not None
    assert elem.tag == "Panel"


def test_find_by_selector_class(sample_xml):
    elem = xml_utils.find_by_selector(sample_xml, ".container")
    assert elem is not None
    assert elem.get("id") == "Main"


def test_find_by_selector_multiple_classes(sample_xml):
    elem = xml_utils.find_by_selector(sample_xml, ".container.active")
    assert elem is not None
    assert elem.get("id") == "Main"


def test_find_by_selector_attribute(sample_xml):
    elem = xml_utils.find_by_selector(sample_xml, "[hittest=true]")
    assert elem is not None
    assert elem.get("id") == "Submit"


def test_find_by_selector_complex(sample_xml):
    elem = xml_utils.find_by_selector(sample_xml, "DOTAXThing#Thing.Thing[attrib=val]")
    assert elem is not None
    assert elem.get("id") == "Thing"


def test_find_by_selector_root(sample_xml):
    elem = xml_utils.find_by_selector(sample_xml, "root")
    assert elem is not None
    assert elem == sample_xml


def test_find_with_parent_by_selector(sample_xml):
    elem, parent = xml_utils.find_with_parent_by_selector(sample_xml, "Button#Submit")
    assert elem is not None
    assert parent is not None
    assert parent.get("id") == "Main"


def test_find_with_parent_by_selector_root(sample_xml):
    elem, parent = xml_utils.find_with_parent_by_selector(sample_xml, "root")
    assert elem == sample_xml
    assert parent is None


def test_find_by_id(sample_xml):
    elem = xml_utils.find_by_id(sample_xml, "Submit")
    assert elem is not None
    assert elem.tag == "Button"


def test_apply_modifications_set_attribute(tmp_path):
    xml_file = tmp_path / "test.xml"
    xml_file.write_text("<root><Panel id='Main'></Panel></root>", encoding="utf-8")

    mods = [{"action": "set_attribute", "selector": "#Main", "attribute": "class", "value": "active"}]
    xml_utils.apply_modifications(str(xml_file), mods)

    tree = ET.parse(str(xml_file))
    root = tree.getroot()
    panel = root.find(".//Panel")
    assert panel.get("class") == "active"
