import os

v3d_file = "scenery.v3d" # name of the file you want to convert
obj_file = "scenery.obj" # name of the exported .obj file 
mtl_file = "scenery.mtl" # name of the exported .mtl file

scale = 0.001
uv_scale = 1024.0

materials = []
vertices = []
uvs = []
faces_by_material = {}

def safe_split(line: str):
    return [p.strip() for p in line.strip().split(",")]

with open(v3d_file, "r", encoding="utf-8", errors="ignore") as f:
    for raw_line in f:
        line = raw_line.strip()

        if not line or line.startswith("//"):
            continue

        if line.startswith("[") and line.endswith("]"):
            continue

        parts = safe_split(line)
        if not parts:
            continue

        tag = parts[0]

        if tag == "SRF":
            mat_name = parts[1] if len(parts) > 1 else f"material_{len(materials)+1}"
            tex_path = parts[5].replace("\\", "/") if len(parts) > 5 else ""
            materials.append((mat_name, tex_path))
            faces_by_material.setdefault(mat_name, [])

        elif tag == "D":
            # Erwartet: D, x, y, z, u, v, ...
            if len(parts) < 6:
                continue

            try:
                x = float(parts[1]) * scale
                y = float(parts[2]) * scale
                z = float(parts[3]) * scale
                u = float(parts[4])
                v = float(parts[5])
            except ValueError:
                continue

            # mirror X axis, invert Y axis, use Z axis as height
            vertices.append((-x, -y, z))

            # scale UVs, invert V
            uvs.append((u / uv_scale, 1.0 - (v / uv_scale)))

        elif tag == "TLS":
            # TLS, count, idx1, idx2, ... idxN, meta1..meta13
            if len(parts) < 2:
                continue

            try:
                count = int(parts[1])
            except ValueError:
                continue

            if len(parts) < 2 + count + 13:
                continue

            try:
                indices = [int(p) for p in parts[2:2 + count] if p != ""]
            except ValueError:
                continue

            meta = parts[2 + count:2 + count + 13]

            try:
                material_id = int(meta[4])
            except (ValueError, IndexError):
                continue

            if material_id < 1 or material_id > len(materials):
                continue

            mat_name = materials[material_id - 1][0]

            for i in range(0, len(indices), 3):
                tri = indices[i:i+3]
                if len(tri) != 3:
                    continue

                a, b, c = tri

                if 1 <= a <= len(vertices) and 1 <= b <= len(vertices) and 1 <= c <= len(vertices):
                    faces_by_material[mat_name].append((a, b, c))

# Write MTL
with open(mtl_file, "w", encoding="utf-8") as mtl:
    for mat_name, tex_path in materials:
        mtl.write(f"newmtl {mat_name}\n")
        mtl.write("Ka 1.000 1.000 1.000\n")
        mtl.write("Kd 1.000 1.000 1.000\n")
        mtl.write("Ks 0.000 0.000 0.000\n")
        if tex_path:
            mtl.write(f"map_Kd {tex_path}\n")
        mtl.write("\n")

# Write OBJ
with open(obj_file, "w", encoding="utf-8") as obj:
    obj.write(f"mtllib {os.path.basename(mtl_file)}\n\n")

    for x, y, z in vertices:
        obj.write(f"v {x} {y} {z}\n")

    for u, v in uvs:
        obj.write(f"vt {u} {v}\n")

    obj.write("\n")

    for mat_name, faces in faces_by_material.items():
        if not faces:
            continue

        obj.write(f"usemtl {mat_name}\n")
        obj.write(f"g {mat_name}\n")

        for a, b, c in faces:
            # Change order because of X axis mirroring
            obj.write(f"f {c}/{c} {b}/{b} {a}/{a}\n")

        obj.write("\n")

print(f"Vertices: {len(vertices)}")
print(f"UVs: {len(uvs)}")
print(f"Materialien: {len(materials)}")
print(f"Faces gesamt: {sum(len(v) for v in faces_by_material.values())}")
print(f"OBJ geschrieben: {obj_file}")
print(f"MTL geschrieben: {mtl_file}")