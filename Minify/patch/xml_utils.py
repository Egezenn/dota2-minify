import os
import re
import xml.etree.ElementTree as ET

import defusedxml.ElementTree as dET
from core import log

SELECTOR_PATTERN = (
    r"^([a-zA-Z0-9_-]+)?(?:#([a-zA-Z0-9_-]+))?((?:\.[a-zA-Z0-9_-]+)*)((?:\[[a-zA-Z0-9_-]+=['\"]?[^'\"\]]+['\"]?\])*)$"
)
ATTRIBUTE_PATTERN = r"\[([a-zA-Z0-9_-]+)=['\"]?([^'\"\]]+)['\"]?\]"


SELECTOR_RE = re.compile(SELECTOR_PATTERN)
ATTRIBUTE_RE = re.compile(ATTRIBUTE_PATTERN)


def find_by_selector(root, selector):
    if not selector:
        return None
    match = SELECTOR_RE.match(selector)
    if not match:
        return None

    tag_name, element_id, classes_str, attrs_str = match.groups()
    target_classes = classes_str.replace(".", " ").split()
    target_attrs = {}
    if attrs_str:
        attr_matches = ATTRIBUTE_RE.findall(attrs_str)
        for k, v in attr_matches:
            target_attrs[k] = v

    def matches(elem):
        if tag_name and elem.tag != tag_name:
            return False
        if element_id and elem.get("id") != element_id:
            return False
        if target_classes:
            elem_classes = (elem.get("class") or "").split()
            if not all(cls in elem_classes for cls in target_classes):
                return False
        if target_attrs:
            if not all(elem.get(k) == v for k, v in target_attrs.items()):
                return False
        return True

    if matches(root):
        return root
    for elem in root.iter():
        if elem == root:
            continue
        if matches(elem):
            return elem
    return None


def find_with_parent_by_selector(root, selector):
    if not selector:
        return None, None
    match = SELECTOR_RE.match(selector)
    if not match:
        return None, None

    tag_name, element_id, classes_str, attrs_str = match.groups()
    target_classes = classes_str.replace(".", " ").split()
    target_attrs = {}
    if attrs_str:
        attr_matches = ATTRIBUTE_RE.findall(attrs_str)
        for k, v in attr_matches:
            target_attrs[k] = v

    def matches(elem):
        if tag_name and elem.tag != tag_name:
            return False
        if element_id and elem.get("id") != element_id:
            return False
        if target_classes:
            elem_classes = (elem.get("class") or "").split()
            if not all(cls in elem_classes for cls in target_classes):
                return False
        if target_attrs:
            if not all(elem.get(k) == v for k, v in target_attrs.items()):
                return False
        return True

    if matches(root):
        return root, None
    for parent in root.iter():
        for child in parent:
            if matches(child):
                return child, parent
    return None, None


def find_by_id(root, node_id):
    if root.get("id") == node_id:
        return root
    return root.find(f".//*[@id='{node_id}']")


def find_with_parent_by_id(root, node_id):
    # Returns (element, parent) or (None, None)
    for parent in root.iter():
        for child in parent:
            if child.get("id") == node_id:
                return child, parent
    # root itself
    if root.get("id") == node_id:
        return root, None
    return None, None


def ensure_unique_include(root, container_tag, src_value):
    container = root.find(container_tag)
    if container is None:
        container = ET.Element(container_tag)
        # put styles/scripts at the top for readability
        root.insert(0, container)
    # de-duplicate
    for inc in container.findall("include"):
        if inc.get("src") == src_value:
            return  # already present
    include = ET.SubElement(container, "include")
    include.set("src", src_value)


def apply_modifications(xml_file, modifications):
    if not os.path.exists(xml_file):
        log.write_warning(f"[Missing XML] '{xml_file}' not found; skipping modifications")
        return
    try:
        tree = dET.parse(xml_file)
        root = tree.getroot()
    except Exception:
        log.write_warning(f"[XML ParseError] Could not parse {xml_file}")
        return

    for mod in modifications:
        action = mod.get("action")

        if action == "add_script":
            src = mod.get("src", "")
            ensure_unique_include(root, "scripts", src)

        elif action == "add_style_include":
            src = mod.get("src", "")
            ensure_unique_include(root, "styles", src)

        elif action == "set_attribute":
            selector = mod.get("selector")
            if selector:
                element = find_by_selector(root, selector)
            else:
                tag = mod.get("tag")
                if root.tag == tag or root.get("id") == tag:
                    element = root
                else:
                    element = root.find(f".//{tag}")
                    if element is None:
                        element = root.find(f".//*[@id='{tag}']")

            if element is not None:
                attr = mod.get("attribute")
                val = mod.get("value")
                if attr is not None and val is not None:
                    element.set(attr, val)

        elif action == "add_child":
            selector = mod.get("selector")
            parent_id = mod.get("parent_id")
            parent_elem = find_by_selector(root, selector) if selector else find_by_id(root, parent_id)
            xml_snippet = mod.get("xml", "")
            if parent_elem is not None and xml_snippet:
                try:
                    child = dET.fromstring(xml_snippet)
                    parent_elem.append(child)
                except ET.ParseError:
                    log.write_warning("[XML ParseError] add_child")
            elif parent_elem is None:
                log.write_warning(
                    f"[add_child] target '{selector or parent_id}' not found in {os.path.basename(xml_file)}"
                )

        elif action == "move_into":
            selector = mod.get("selector")
            target_id = mod.get("target_id")
            new_parent_selector = mod.get("new_parent_selector")
            new_parent_id = mod.get("new_parent_id")

            elem, old_parent = (
                find_with_parent_by_selector(root, selector) if selector else find_with_parent_by_id(root, target_id)
            )
            new_parent = (
                find_by_selector(root, new_parent_selector) if new_parent_selector else find_by_id(root, new_parent_id)
            )

            if elem is not None and new_parent is not None:
                if old_parent is not None:
                    old_parent.remove(elem)
                new_parent.append(elem)
            else:
                if elem is None:
                    log.write_warning(
                        f"[move_into] target '{selector or target_id}' not found in {os.path.basename(xml_file)}"
                    )
                if new_parent is None:
                    log.write_warning(
                        f"[move_into] new_parent '{new_parent_selector or new_parent_id}' not found in {os.path.basename(xml_file)}"
                    )

        elif action == "insert_after":
            selector = mod.get("selector")
            target_id = mod.get("target_id")
            xml_snippet = mod.get("xml", "")

            target, parent = (
                find_with_parent_by_selector(root, selector) if selector else find_with_parent_by_id(root, target_id)
            )

            if target is not None and parent is not None and xml_snippet:
                try:
                    new_elem = ET.fromstring(xml_snippet)
                    idx = list(parent).index(target)
                    parent.insert(idx + 1, new_elem)
                except ET.ParseError:
                    log.write_warning("[XML ParseError] insert_after")
            elif target is None:
                log.write_warning(
                    f"[insert_after] target '{selector or target_id}' not found in {os.path.basename(xml_file)}"
                )
            elif parent is None:
                log.write_warning(
                    f"[insert_after] target '{selector or target_id}' has no parent (is root?) in {os.path.basename(xml_file)}"
                )

        elif action == "insert_before":
            selector = mod.get("selector")
            target_id = mod.get("target_id")
            xml_snippet = mod.get("xml", "")

            target, parent = (
                find_with_parent_by_selector(root, selector) if selector else find_with_parent_by_id(root, target_id)
            )

            if target is not None and parent is not None and xml_snippet:
                try:
                    new_elem = ET.fromstring(xml_snippet)
                    idx = list(parent).index(target)
                    parent.insert(idx, new_elem)
                except ET.ParseError:
                    log.write_warning("[XML ParseError] insert_before")
            elif target is None:
                log.write_warning(
                    f"[insert_before] target '{selector or target_id}' not found in {os.path.basename(xml_file)}"
                )
            elif parent is None:
                log.write_warning(
                    f"[insert_before] target '{selector or target_id}' has no parent (is root?) in {os.path.basename(xml_file)}"
                )

    if hasattr(ET, "indent"):
        ET.indent(tree, space="\t", level=0)

    try:
        tree.write(xml_file, encoding="utf-8", xml_declaration=False)
    except TypeError:
        tree.write(xml_file)
