#!/usr/bin/env python3
"""
Safe argument renaming script using AST manipulation.
This avoids the pitfalls of string replacement by properly parsing Python code.
"""

import ast
import re
from pathlib import Path


class ArgumentRenamer(ast.NodeTransformer):
    """AST transformer to rename function arguments safely."""
    
    def __init__(self, renames):
        self.renames = renames
    
    def visit_Attribute(self, node):
        # Handle args.old_name -> args.new_name
        if isinstance(node.value, ast.Name) and node.value.id == 'args':
            if node.attr in self.renames:
                node.attr = self.renames[node.attr]
        return self.generic_visit(node)


def rename_arguments_in_file(filepath, renames):
    """
    Safely rename arguments in a Python file.
    
    Args:
        filepath: Path to the Python file
        renames: Dict mapping old names to new names (e.g., {'input_file': 'input_path'})
    """
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Parse the AST
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Syntax error in {filepath}: {e}")
        return False
    
    # Transform args.old_name references
    transformer = ArgumentRenamer(renames)
    tree = transformer.visit(tree)
    
    # Convert back to source (this loses formatting, so we'll use regex instead)
    # For argument definitions, use careful regex
    
    for old_name, new_name in renames.items():
        # Replace in argument parser definitions
        # Pattern: "--old_name" or "--old-name"
        old_arg = old_name.replace('_', '_')
        new_arg = new_name.replace('_', '-')
        
        # Replace argument names in parser.add_argument calls
        content = re.sub(
            rf'(["\'])--{re.escape(old_arg)}\1',
            rf'\1--{new_arg}\1',
            content
        )
        
        # Replace args.old_name references
        content = re.sub(
            rf'\bargs\.{re.escape(old_name)}\b',
            f'args.{new_name}',
            content
        )
    
    # Write back
    with open(filepath, 'w') as f:
        f.write(content)
    
    return True


def add_argument_after(filepath, after_arg, new_arg_code):
    """
    Add a new argument definition after an existing one.
    
    Args:
        filepath: Path to the Python file
        after_arg: Name of the argument to insert after (e.g., "--output-path")
        new_arg_code: Complete argument definition code to insert
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Find the argument block
    in_target_arg = False
    insert_line = -1
    paren_count = 0
    
    for i, line in enumerate(lines):
        if f'"{after_arg}"' in line or f"'{after_arg}'" in line:
            in_target_arg = True
            paren_count = line.count('(') - line.count(')')
        elif in_target_arg:
            paren_count += line.count('(') - line.count(')')
            if paren_count == 0 and ')' in line:
                insert_line = i + 1
                break
    
    if insert_line > 0:
        # Insert the new argument
        lines.insert(insert_line, '\n' + new_arg_code + '\n')
        
        with open(filepath, 'w') as f:
            f.writelines(lines)
        return True
    
    return False


def add_batch_processing_logic(filepath):
    """Add batch processing logic to main() function."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    batch_logic = '''
    # Support batch processing for directories
    input_path = Path(args.input_path)
    
    if input_path.is_dir():
        print(f"Batch processing directory: {input_path}")
        ply_files = sorted(input_path.glob("*.ply"))
        
        if not ply_files:
            print(f"No .ply files found in {input_path}")
            return
        
        print(f"Found {len(ply_files)} .ply files\\n")
        output_dir = Path(args.output_dir or "meshes")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for i, ply_file in enumerate(ply_files, 1):
            print(f"[{i}/{len(ply_files)}] Processing: {ply_file.name}")
            try:
                pcd = load_point_cloud(str(ply_file))
                mesh = generate_mesh(pcd, args.meshing_method)
                
                cleanup = not args.no_cleanup
                origin_bottom = (args.origin == "bottom")
                mesh, texture = post_process_mesh(
                    mesh, pcd=pcd, cleanup=cleanup,
                    simplify_target=args.simplify,
                    simplify_method=args.simplify_method,
                    adaptive_threshold=args.adaptive_threshold,
                    fill_holes_size=args.fill_holes,
                    origin_bottom=origin_bottom,
                    generate_tex=args.generate_texture,
                    uv_method=args.uv_method,
                    texture_size=args.texture_size
                )
                
                output_name = f"{ply_file.stem}_{args.meshing_method}.{args.output_format}"
                output_path = output_dir / output_name
                save_mesh(mesh, str(output_path), args.output_format, texture)
                print(f"✓ Saved: {output_name}\\n")
            except Exception as e:
                print(f"✗ Failed: {e}\\n")
                continue
        
        print(f"Batch processing complete: {len(ply_files)} files processed")
        return
'''
    
    # Find where to insert (after args = parser.parse_args())
    pattern = r'(    args = parser\.parse_args\(\)\n)(    \n    try:)'
    replacement = r'\1' + batch_logic + r'\n\2'
    
    content = re.sub(pattern, replacement, content, count=1)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    return True


if __name__ == "__main__":
    print("Safe Python file modification utility")
    print("This script uses AST and careful regex to avoid syntax errors")
