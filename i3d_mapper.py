#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import os
import re
import sys
from datetime import datetime


NODE_TYPES = [
    "node", "repr", "startNode", "endNode", "linkNode", "jointNode", "shaderNode",
    "rotateNode", "referencePoint", "referenceFrame", "index", "effectNode",
    "attachReferenceNode", "lightShaderNode", "driveNode", "realLightNode",
    "targetNode", "baseNode", "playerTriggerNode", "vehicleTriggerNode",
    "visibilityNode", "triggerNode", "activeNode", "inactiveNode", "numbers", "realLight"
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

LOG_FILE_PATH = None
CURRENT_MOD_ROOT = None


def init_logger(mod_root: str):
    """
    Initialize logger for a given mod root.

    Each time the script is run, the log for that mod is reset.
    If multiple files from the same mod are processed in one run,
    they will all share this single fresh log file.
    """
    global LOG_FILE_PATH, CURRENT_MOD_ROOT
    CURRENT_MOD_ROOT = mod_root
    LOG_FILE_PATH = os.path.join(mod_root, "log.txt")

    header = (
        f"I3D Mapper Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        "========================================\n"
    )


    with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(header)

    print(header, end="")



def log(msg: str):
    print(msg)
    if LOG_FILE_PATH:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(msg + "\n")


def rename_logger(msg: str):
    log(msg)


def is_numeric_node(value: str) -> bool:
    """Match paths like 0> or 0>0|1|2."""
    return re.fullmatch(r"\d>[0-9|]*", value or "") is not None


def xpath_attrib_find(attrib: str) -> str:
    return ".//*[@" + attrib + "]"


def clean_path(base_folder: str, filename: str) -> str:
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
            return original
        current = parent


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

        if depth > 1 and this_node_name:
            if this_node_name in unique_names:
                unique_names[this_node_name] += 1
                this_node_name = f"{this_node_name}_{unique_names[this_node_name]:0>3}"
                xml_entry.set('name', this_node_name)
                renamed_nodes.append((original_name, this_node_name))
            else:
                unique_names[this_node_name] = 1

        if depth == 2:
            current_component += 1
            count_depth = []
            last_depth = 0
            node_path = node_maker(current_component)
            if this_node_name:
                print_names.append([this_node_name, node_path])

        elif depth > 2:
            last_map_index = depth - 2
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

        i3d_tag = shop_xml.find(".//base/filename")
        if i3d_tag is None or not i3d_tag.text or not i3d_tag.text.strip():
            log("❌ <base><filename> tag missing or empty. Skipping.")
            return

        i3d_filename = i3d_tag.text.strip()

        if i3d_filename.startswith("$data"):
            log(f"ℹ️ i3d file is in $data ({i3d_filename}). Skipping.")
            return

        i3d_path = clean_path(mod_root, i3d_filename)
        log(f"📄 i3d path resolved to: {os.path.relpath(i3d_path, mod_root)}")

        if not os.path.isfile(i3d_path):
            log(f"❌ .i3d file not found: {i3d_path}")
            return

        with open(i3d_path, 'r', encoding='utf-8') as i3d_file:
            unique_names = {}
            i3d_mapping_text, updated_i3d_xml = generate_i3d_mapping(
                i3d_file, unique_names
            )
            if not i3d_mapping_text:
                return

        map_cache = {}
        i3d_mapping_root = ET.fromstring(i3d_mapping_text)
        for this_map in i3d_mapping_root.findall(XPATH_I3D_MAPPING):
            map_cache[this_map.attrib["node"]] = this_map.attrib["id"]

        replaced_count = 0
        for this_type in NODE_TYPES:
            for tag in shop_xml.findall(xpath_attrib_find(this_type)):
                if tag.tag != "i3dMapping":
                    my_node = tag.attrib.get(this_type)
                    if my_node and is_numeric_node(my_node) and my_node in map_cache:
                        tag.attrib[this_type] = map_cache[my_node]
                        replaced_count += 1
        log(f"🔁 Replaced {replaced_count} numeric node reference(s) with i3dMapping IDs.")

        existing_mappings = shop_xml.find(XPATH_I3D_MAPPINGS)
        if existing_mappings is not None:
            log("✏️ Found existing <i3dMappings> — replacing contents.")
            for child in list(existing_mappings):
                existing_mappings.remove(child)
            for map_item in i3d_mapping_root.findall(XPATH_I3D_MAPPING):
                existing_mappings.append(map_item)
        else:
            log("➕ Adding new <i3dMappings> section.")
            shop_xml.append(i3d_mapping_root)

        fix_count = 0
        for this_tag in shop_xml.findall(XPATH_I3D_MAPPING):
            node_index = this_tag.attrib.get("index")
            if node_index and is_numeric_node(node_index) and node_index in map_cache:
                this_tag.attrib["index"] = map_cache[node_index]
                fix_count += 1
        if fix_count:
            log(f"🔧 Fixed {fix_count} i3dMapping index attribute(s).")

        removed_memory_tags = 0
        for tag_name in MEMORY_TAGS:
            for elem in shop_xml.findall(f".//{tag_name}"):
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


        i3d_output = ET.tostring(updated_i3d_xml.getroot(), encoding='unicode')
        i3d_output = "<?xml version='1.0' encoding='utf-8'?>\n" + i3d_output
        with open(i3d_path, "w", encoding='utf-8') as writer:
            writer.write(i3d_output)
        log(f"💾 Updated i3d file written: {os.path.relpath(i3d_path, mod_root)}")


        try:
            ET.indent(shop_xml, space="    ")
        except AttributeError:
            pass

        xml_output = ET.tostring(shop_xml, encoding='unicode').replace("&gt;", ">")
        xml_output = "<?xml version='1.0' encoding='utf-8'?>\n" + xml_output
        with open(xml_path, "w", encoding='utf-8') as writer:
            writer.write(xml_output)
        log(f"💾 Updated XML file written: {rel_xml}")

        log("✅ Success. Mod XML and i3d updated.")

    except Exception as e:
        log(f"❌ ERROR while processing {xml_path}: {str(e)}")


def process_moddesc(moddesc_path: str):
    mod_root = os.path.dirname(moddesc_path)

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
    global CURRENT_MOD_ROOT

    if len(sys.argv) < 2:
        print("Drag and drop one or more XML files onto this script.")
        print("Usage:")
        print("  python rmc_i3d_mapper.py <file1.xml> <file2.xml> ...")
        try:
            input("\nPress Enter to exit...")
        except EOFError:
            pass
        return

    processed_any = False

    for input_path in sys.argv[1:]:
        input_path = os.path.abspath(input_path)

        if not os.path.isfile(input_path):
            print(f"❌ File not found: {input_path}")
            continue

        filename_lower = os.path.basename(input_path).lower()
        mod_root = find_mod_root(input_path)

        if mod_root != CURRENT_MOD_ROOT:
            init_logger(mod_root)
            log(f"Detected mod root: {mod_root}")

        if filename_lower == "moddesc.xml":
            log(f"Processing modDesc: {input_path}")
            process_moddesc(input_path)
            processed_any = True
        else:
            log(f"Processing vehicle XML: {input_path}")
            process_xml(input_path, mod_root)
            processed_any = True

    if not processed_any:
        print("No valid XML files processed.")
        try:
            input("\nPress Enter to exit...")
        except EOFError:
            pass
        return


if __name__ == "__main__":
    main()

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

    try:
        input("Press Enter to exit...")
    except EOFError:
        pass

