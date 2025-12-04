#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import os
import re
import sys
from datetime import datetime

# ==========================================
# CONFIG
# ==========================================
NODE_TYPES = [
    "node", "repr", "startNode", "endNode", "linkNode", "jointNode", "shaderNode",
    "rotateNode", "referencePoint", "referenceFrame", "index", "effectNode",
    "attachReferenceNode", "lightShaderNode", "driveNode", "realLightNode",
    "targetNode", "baseNode", "playerTriggerNode", "vehicleTriggerNode",
    "visibilityNode", "triggerNode", "activeNode", "inactiveNode", "numbers"
]

XPATH_I3D_MAPPING = ".//i3dMapping"
XPATH_I3D_MAPPINGS = ".//i3dMappings"

MEMORY_TAGS = [
    "vertexBufferMemoryUsage",
    "indexBufferMemoryUsage",
    "textureMemoryUsage",
    "audioMemoryUsage",
    "instanceVertexBufferMemoryUsage",
    "instanceIndexBufferMemoryUsage",
]

LOG_FILE_PATH = None  # will be set per mod


# ==========================================
# LOGGING
# ==========================================
def init_logger(mod_root: str):
    global LOG_FILE_PATH
    LOG_FILE_PATH = os.path.join(mod_root, "log.txt")
    header = f"I3D Mapper Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    header += "========================================\n"
    with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(header)
    print(header, end="")


def log(msg: str):
    print(msg)
    if LOG_FILE_PATH:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(msg + "\n")


def rename_logger(msg: str):
    # simple alias to go through same logger
    log(msg)


# ==========================================
# UTILS
# ==========================================
def is_numeric_node(value: str) -> bool:
    """Match paths like 0> or 0>0|1|2."""
    return re.fullmatch(r"\d>[0-9|]*", value or "") is not None


def xpath_attrib_find(attrib: str) -> str:
    return ".//*[@" + attrib + "]"


def clean_path(base_folder: str, filename: str) -> str:
    """
    Join a relative filename to a base folder.
    Example:
        base_folder = D:/mods/MyMod
        filename   = i3d/boxTank.i3d
        result     = D:/mods/MyMod/i3d/boxTank.i3d
    """
    filename = (filename or "").replace("\\", "/").strip()
    return os.path.normpath(os.path.join(base_folder, filename))


def node_maker(component: int, depth_list=None) -> str:
    this_node = f"{component}>"
    if depth_list is None:
        return this_node
    return this_node + "|".join([str(i) for i in depth_list])


def depth_iter(element, tag=None):
    """Yield (element, depth) for depth-first traversal."""
    stack = [iter([element])]
    while stack:
        e = next(stack[-1], None)
        if e is None:
            stack.pop()
        else:
            stack.append(iter(e))
            if tag is None or e.tag == tag:
                yield (e, len(stack) - 1)


def find_mod_root(start_path: str) -> str:
    """
    Walk up from a file or folder until we find a modDesc.xml / moddesc.xml.
    If not found, return the starting folder.
    """
    if os.path.isfile(start_path):
        current = os.path.dirname(start_path)
    else:
        current = start_path

    original = current
    while True:
        moddesc_upper = os.path.join(current, "modDesc.xml")
        moddesc_lower = os.path.join(current, "moddesc.xml")
        if os.path.isfile(moddesc_upper) or os.path.isfile(moddesc_lower):
            return current

        parent = os.path.dirname(current)
        if parent == current:
            # Reached drive root
            return original
        current = parent


# ==========================================
# CORE: I3D MAPPING
# ==========================================
def generate_i3d_mapping(i3d_file, unique_names):
    try:
        i3d_text = i3d_file.read()
        this_xml = ET.ElementTree(ET.fromstring(i3d_text))
    except Exception as e:
        log(f"[ERROR] Failed to parse i3d file: {str(e)}")
        return None, None

    this_scene = this_xml.find('Scene')
    if this_scene is None:
        log("[ERROR] No <Scene> node found in i3d.")
        return None, None

    print_names = []
    last_depth = 0
    count_depth = []
    current_component = -1
    renamed_nodes = []

    for xml_entry, depth in depth_iter(this_scene):
        this_node_name = xml_entry.get('name')
        original_name = this_node_name

        # Ensure unique names for depth > 1
        if depth > 1 and this_node_name:
            if this_node_name in unique_names:
                unique_names[this_node_name] += 1
                this_node_name = f"{this_node_name}_{unique_names[this_node_name]:0>3}"
                xml_entry.set('name', this_node_name)
                renamed_nodes.append((original_name, this_node_name))
            else:
                unique_names[this_node_name] = 1

        # Component level (depth == 2)
        if depth == 2:
            current_component += 1
            count_depth = []
            last_depth = 0
            node_path = node_maker(current_component)
            if this_node_name:
                print_names.append([this_node_name, node_path])

        # Deeper than component (depth > 2)
        elif depth > 2:
            last_map_index = depth - 2  # index starting below component
            if last_map_index > last_depth:
                count_depth.extend([0] * (last_map_index - last_depth))
            else:
                for _ in range(last_depth - last_map_index):
                    if count_depth:
                        count_depth.pop()
                if count_depth:
                    count_depth[last_map_index - 1] += 1
            last_depth = last_map_index
            node_path = node_maker(current_component, count_depth)
            if this_node_name:
                print_names.append([this_node_name, node_path])

    # Build <i3dMappings> as text
    output_queue = ["<i3dMappings>"]
    for name, node in print_names:
        output_queue.append(f'\t<i3dMapping id="{name}" node="{node}" />')
    output_queue.append("</i3dMappings>")

    if renamed_nodes:
        rename_logger(f"🧭 {len(renamed_nodes)} duplicate node name(s) were renamed:")
        for original, renamed in renamed_nodes:
            rename_logger(f'  • "{original}" -> "{renamed}"')
    else:
        rename_logger("✅ No duplicate node names found.")

    return "\n".join(output_queue), this_xml


# ==========================================
# CORE: PROCESS SINGLE VEHICLE XML
# ==========================================
def process_xml(xml_path: str, mod_root: str):
    try:
        rel_xml = os.path.relpath(xml_path, mod_root)
        log("")
        log("====================================")
        log(f"🔍 Processing XML: {rel_xml}")
        log("====================================")

        if not os.path.isfile(xml_path):
            log(f"❌ XML file not found: {xml_path}")
            return

        with open(xml_path, 'r', encoding='utf-8') as file:
            xml_content = file.read()

        shop_xml = ET.fromstring(xml_content)

        # Find the i3d filename
        i3d_tag = shop_xml.find(".//base/filename")
        if i3d_tag is None or not i3d_tag.text or not i3d_tag.text.strip():
            log("❌ <base><filename> tag missing or empty. Skipping.")
            return

        i3d_filename = i3d_tag.text.strip()

        # Skip $data references (base game)
        if i3d_filename.startswith("$data"):
            log(f"ℹ️ i3d file is in $data ({i3d_filename}). Skipping.")
            return

        # Resolve relative to MOD ROOT (important when XML is in /xml and i3d in /i3d)
        i3d_path = clean_path(mod_root, i3d_filename)
        log(f"📄 i3d path resolved to: {os.path.relpath(i3d_path, mod_root)}")

        if not os.path.isfile(i3d_path):
            log(f"❌ .i3d file not found: {i3d_path}")
            return

        # Generate new i3dMappings and updated i3d XML
        with open(i3d_path, 'r', encoding='utf-8') as i3d_file:
            unique_names = {}
            i3d_mapping_text, updated_i3d_xml = generate_i3d_mapping(
                i3d_file, unique_names
            )
            if not i3d_mapping_text:
                return

        # Build cache: numeric node -> name
        map_cache = {}
        i3d_mapping_root = ET.fromstring(i3d_mapping_text)
        for this_map in i3d_mapping_root.findall(XPATH_I3D_MAPPING):
            map_cache[this_map.attrib["node"]] = this_map.attrib["id"]

        # Replace numeric attributes in the XML with i3dMapping IDs
        replaced_count = 0
        for this_type in NODE_TYPES:
            for tag in shop_xml.findall(xpath_attrib_find(this_type)):
                if tag.tag != "i3dMapping":
                    my_node = tag.attrib.get(this_type)
                    if my_node and is_numeric_node(my_node) and my_node in map_cache:
                        tag.attrib[this_type] = map_cache[my_node]
                        replaced_count += 1
        log(f"🔁 Replaced {replaced_count} numeric node reference(s) with i3dMapping IDs.")

        # Handle <i3dMappings> section inside the XML
        existing_mappings = shop_xml.find(XPATH_I3D_MAPPINGS)
        if existing_mappings is not None:
            log("✏️ Found existing <i3dMappings> — replacing contents.")
            for child in list(existing_mappings):
                existing_mappings.remove(child)
            # Append new mappings
            for map_item in i3d_mapping_root.findall(XPATH_I3D_MAPPING):
                existing_mappings.append(map_item)
        else:
            log("➕ Adding new <i3dMappings> section.")
            shop_xml.append(i3d_mapping_root)

        # Fix any <i3dMapping index="0>0|1"> attributes (if they exist)
        fix_count = 0
        for this_tag in shop_xml.findall(XPATH_I3D_MAPPING):
            node_index = this_tag.attrib.get("index")
            if node_index and is_numeric_node(node_index) and node_index in map_cache:
                this_tag.attrib["index"] = map_cache[node_index]
                fix_count += 1
        if fix_count:
            log(f"🔧 Fixed {fix_count} i3dMapping index attribute(s).")

        # ==========================================
        # REMOVE MEMORY USAGE TAGS
        # ==========================================
        removed_memory_tags = 0
        for tag_name in MEMORY_TAGS:
            for elem in shop_xml.findall(f".//{tag_name}"):
                # Manual parent search since ElementTree has no getparent()
                for parent in shop_xml.iter():
                    for child in list(parent):
                        if child is elem:
                            parent.remove(child)
                            removed_memory_tags += 1
                            break

        if removed_memory_tags:
            log(f"🧹 Removed {removed_memory_tags} memory usage tag(s).")
        else:
            log("🧹 No memory usage tags found to remove.")

        # Write updated i3d
        i3d_output = ET.tostring(updated_i3d_xml.getroot(), encoding='unicode')
        i3d_output = "<?xml version='1.0' encoding='utf-8'?>\n" + i3d_output
        with open(i3d_path, "w", encoding='utf-8') as writer:
            writer.write(i3d_output)
        log(f"💾 Updated i3d file written: {os.path.relpath(i3d_path, mod_root)}")

        # Write updated vehicle XML
        try:
            ET.indent(shop_xml, space="    ")
        except AttributeError:
            # Python < 3.9 has no ET.indent
            pass

        xml_output = ET.tostring(shop_xml, encoding='unicode').replace("&gt;", ">")
        xml_output = "<?xml version='1.0' encoding='utf-8'?>\n" + xml_output
        with open(xml_path, "w", encoding='utf-8') as writer:
            writer.write(xml_output)
        log(f"💾 Updated XML file written: {rel_xml}")

        log("✅ Success. Mod XML and i3d updated.")

    except Exception as e:
        log(f"❌ ERROR while processing {xml_path}: {str(e)}")


# ==========================================
# CORE: PROCESS MODDESC.XML
# ==========================================
def process_moddesc(moddesc_path: str):
    mod_root = os.path.dirname(moddesc_path)
    init_logger(mod_root)

    log("")
    log("====================================")
    log(f"📦 Mod root: {mod_root}")
    log("====================================")

    with open(moddesc_path, 'r', encoding='utf-8') as file:
        content = file.read()

    try:
        moddesc_xml = ET.fromstring(content)
    except Exception as e:
        log(f"❌ Failed to parse modDesc: {str(e)}")
        return

    # Find all storeItems
    store_items = moddesc_xml.findall(".//storeItems/storeItem")
    if not store_items:
        log("⚠️ No <storeItems><storeItem> entries found in modDesc.")
        return

    log(f"🔎 Found {len(store_items)} storeItem entries.")

    for item in store_items:
        xml_filename = item.attrib.get("xmlFilename")
        if not xml_filename:
            continue

        xml_path = clean_path(mod_root, xml_filename)
        if not os.path.isfile(xml_path):
            log(f"❌ Vehicle XML not found: {xml_path}")
            continue

        process_xml(xml_path, mod_root)


def main():
    if len(sys.argv) < 2:
        print("Drag and drop a modDesc.xml or a vehicle XML onto this script.")
        print("Usage:")
        print("  python rmc_i3d_mapper.py <modDesc.xml>")
        print("  python rmc_i3d_mapper.py <vehicle.xml>")
        try:
            input("\nPress Enter to exit...")
        except EOFError:
            pass
        return

    input_path = sys.argv[1]
    input_path = os.path.abspath(input_path)

    if not os.path.isfile(input_path):
        print(f"❌ File not found: {input_path}")
        try:
            input("\nPress Enter to exit...")
        except EOFError:
            pass
        return

    filename_lower = os.path.basename(input_path).lower()

    # Case 1: modDesc.xml -> process all storeItems
    if filename_lower == "moddesc.xml":
        process_moddesc(input_path)

    # Case 2: single vehicle XML -> work out mod root and process only that XML
    else:
        mod_root = find_mod_root(input_path)
        init_logger(mod_root)
        log("")
        log(f"Detected mod root: {mod_root}")
        process_xml(input_path, mod_root)


if __name__ == "__main__":
    # Run main logic
    main()

    # Fancy banner shown AFTER work is done
    banner = r"""
***********************************************
*         Developed by GamerDesigns            *
*              as part of RMC                  *
*                                             *
*   If you enjoy this script and want to       *
*   support future development, feel free      *
*   to support the cause on Patreon:           *
*   https://www.patreon.com/roughneckmoddingcrew *
***********************************************
"""
    print(banner)
    if LOG_FILE_PATH:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(banner + "\n")

    # Always try to pause at the very end
    try:
        input("Press Enter to exit...")
    except EOFError:
        pass
