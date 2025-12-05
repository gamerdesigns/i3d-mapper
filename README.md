# I3D Mapper Tool  
Advanced Automatic I3D Mapping and XML Cleaner for Farming Simulator Mods

## Overview
The **I3D Mapper Tool** is a standalone drag and drop Python utility designed to automate i3d mapping and XML cleanup for Farming Simulator modders. It scans your vehicle XML files and i3d files, generates accurate `<i3dMappings>`, renames duplicate nodes inside the i3d, fixes numeric node references, and cleans unnecessary memory usage tags. It works no matter how your mod folders are organized, as long as the XML correctly references the i3d.

Created by **GamerDesigns** and **Roughneck Modding Crew**.

---

## Requirements

You only need:

### ✔ Python 3.9 or newer  
Download here:  
https://www.python.org/downloads/

**Important for beginners:**  
During installation:
1. Check the box: **Add Python to PATH**
2. Click **Install Now**

No additional modules are required.

---

## Key Features
### ✔ Auto i3d Node Mapping  
Reads the entire `<Scene>` structure from the i3d and builds complete `<i3dMappings>`.

### ✔ Duplicate Node Renaming  
Detects duplicate node names inside the i3d and renames them automatically with numeric suffixes.

### ✔ XML Node Fixing  
Converts numeric node references (like `0>0|1|2`) into valid `id` references using the generated mappings.

### ✔ Cleans Memory Tags  
Automatically removes unused internal FS debug tags:
- `<vertexBufferMemoryUsage>`
- `<indexBufferMemoryUsage>`
- `<textureMemoryUsage>`
- `<audioMemoryUsage>`
- `<instanceVertexBufferMemoryUsage>`
- `<instanceIndexBufferMemoryUsage>`

### ✔ Multi-file Support  
- Drag in **modDesc.xml** to process every vehicle XML listed under `<storeItems>`.
- Drag in **a single vehicle XML** to process only that vehicle.

### ✔ Flexible Path Resolution  
The tool now handles any mod folder layout including:
```
MyMod/
│ modDesc.xml
│ log.txt
├─ xml/
│   ├─ item1.xml
│   ├─ item2.xml
└─ i3d/
    ├─ item1.i3d
    ├─ item2.i3d
```
and:
```
MyMod/
│ modDesc.xml
│ item1.xml
│ item2.xml
│ item1.i3d
│ item2.i3d
```

The script resolves i3d paths relative to:
1. The XML file folder  
2. The mod root folder  
3. Absolute paths  

This ensures compatibility with virtually any mod structure.

---

## Requirements
- **Python 3.9 or newer**  
Download: https://www.python.org/downloads/

During installation:
1. Enable **Add Python to PATH**
2. Click **Install**

No extra modules are required.

---

## How to Use

### **Option A: Drag & Drop**
Drop one of the following onto the script:
- `modDesc.xml`  
- Any vehicle `.xml`

### **Option B: Use Command Line**
```
python rmc_i3d_mapper.py vehicle.xml
```

---

## What Happens When You Run It

### 1. Reads the XML and detects the linked i3d  
The tool locates the i3d file using smart path resolution.

### 2. Builds a complete i3d map  
It scans the entire Scene tree, generating deterministic node paths.

### 3. Renames duplicate nodes  
If an i3d has repeated names (common issue), they become:
```
"Light" → "Light_001"
"Light" → "Light_002"
```

### 4. Generates new `<i3dMappings>`  
Creates a fresh mapping block with the correct IDs.

### 5. Updates all XML references  
Replaces numeric paths inside attributes like:
```
node=""
index=""
jointNode=""
realLightNode=""
triggerNode=""
```

### 6. Cleans memory usage tags  
Removes unnecessary debug tags to keep XML files clean.

### 7. Writes changes back to both XML and i3d  
Both files are saved with updated IDs and node names.

### 8. Creates a log file  
A `log.txt` is created in the mod root documenting:
- Renamed nodes  
- Replaced references  
- Files processed  
- Errors or warnings  

---

## Recommended Folder Structure
The script works with any layout, but these two are most common:

### Standard Layout
```
MyMod/
│ modDesc.xml
├─ xml/
│   ├─ vehicle.xml
└─ i3d/
    ├─ vehicle.i3d
```

### Flat Layout
```
MyMod/
│ modDesc.xml
│ vehicle.xml
│ vehicle.i3d
```

---

## Troubleshooting

### Script closes immediately  
Run from terminal:
```
python rmc_i3d_mapper.py
```

### Python not recognized  
Reinstall Python using the official installer and enable
**Add Python to PATH**.

### i3d not found  
Check that `<base><filename>` in the vehicle XML correctly describes the path to the i3d file.

---

## Credits
Developed by **GamerDesigns** as part of the **RMC Toolkit**.  
If you’d like to support future tools and updates:  
https://www.patreon.com/roughneckmoddingcrew

---

## License
You are free to use, edit, or redistribute this tool or any portion of its code. Any public or redistributed version must include visible credit to GamerDesigns and Roughneck Modding Crew (RMC).
