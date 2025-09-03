from itertools import combinations

def create_from_combinations(vars_list, outfile):
    # Generate 2D combinations
    vars2d = list(combinations(vars_list, 2))

    # Generate 3D combinations  
    vars3d = list(combinations(vars_list, 3))

    # Create YAML content
    yaml_content = "var2d:\n"
    for combo in vars2d:
        name = "_vs_".join(combo)
        vars_str = ", ".join(combo)
        yaml_content += f"  - {{ name: {name}, vars: [{vars_str}] }}\n"

    yaml_content += "\nvar3d:\n"
    for combo in vars3d:
        name = "_vs_".join(combo)
        vars_str = ", ".join(combo)
        yaml_content += f"  - {{ name: {name}, vars: [{vars_str}] }}\n"

    # Save to file
    with open(outfile, 'w') as f:
        f.write(yaml_content)

    print(f"Generated YAML with {len(vars2d)} 2D and {len(vars3d)} 3D combinations")
    print(f"Saved to {outfile}")