
# RMC I3D Mapper Tool – README

## Overview

The **RMC I3D Mapper Tool** is a standalone drag and drop Python script developed for Farming Simulator modders.  
It automatically:

- Reads and maps the **.i3d** node structure
- Renames **duplicate node names**
- Generates clean `<i3dMappings>`
- Updates all **vehicle XML files**
- Cleans unnecessary **memory usage lines**
- Writes all actions into a `log.txt`
- Supports **drag and drop**
- Works with single XML or full modDesc processing

Created by **GamerDesigns**, built for **Roughneck Modding Crew (RMC)**.

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

## How to Use

### Option 1: Drag & Drop

You can drop either:

### A) `modDesc.xml`  
Processes:
- All `<storeItem>` entries
- All vehicle XML files
- All linked i3d files
- Writes updates automatically

### B) A single vehicle XML  
Processes:
- Only that XML
- Its i3d file
- Updates both

### Command Line Use:
```
python rmc_i3d_mapper.py yourfile.xml
```

---

## What the Script Does

### ✔ Builds a full i3d node map  
### ✔ Renames duplicate nodes  
### ✔ Creates or replaces `<i3dMappings>`
### ✔ Updates all XML node references  
### ✔ Removes FS memory usage tags  
### ✔ Writes renamed nodes back into the i3d  
### ✔ Creates a `log.txt` with all actions  

### Automatically removed tags:
```
<vertexBufferMemoryUsage>
<indexBufferMemoryUsage>
<textureMemoryUsage>
<audioMemoryUsage>
<instanceVertexBufferMemoryUsage>
<instanceIndexBufferMemoryUsage>
```

---

## Example Mod Folder

```
MyMod/
│ modDesc.xml
│ log.txt
├─ xml/
│   ├─ item1.xml
│   ├─ item2.xml
│   └─ ...
└─ i3d/
    ├─ item1.i3d
    ├─ item2.i3d
    └─ ...
```

---

## Troubleshooting

### Script closes instantly  
Run manually:
```
python rmc_i3d_mapper.py
```

### Python not recognized  
Reinstall Python and enable:
✔ Add Python to PATH

### Missing i3d file  
Verify `<base><filename>` paths.

---

## Credits

**Developed for Roughneck Modding Crew  
by GamerDesigns**

Need a GUI version? Installer? Batch mapper?  
Just ask!

