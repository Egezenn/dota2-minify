import ast
import os
import re
import shutil


def get_slug(text, seen_slugs):
    # Standard GitHub heading algorithm:
    # 1. Convert text to lowercase
    text = text.lower()
    # 2. Remove punctuation characters (keeping letters, numbers, hyphens, spaces, and underscores)
    # Most punctuation is removed, but underscores and hyphens are kept.
    text = re.sub(r"[^a-z0-9\s_-]", "", text)
    # 3. Convert spaces to dashes
    text = re.sub(r"\s+", "-", text)
    # 4. Remove leading/trailing dashes
    base_slug = text.strip("-")

    # Handle empty slug
    if not base_slug:
        base_slug = "section"

    # 5. Handle uniqueness (GitHub appends -1, -2, etc. for duplicate slugs)
    slug = base_slug
    counter = 1
    while slug in seen_slugs:
        slug = f"{base_slug}-{counter}"
        counter += 1

    seen_slugs.add(slug)
    return slug


def get_symbols(file_path, include_vars=False):
    with open(file_path, "r", encoding="utf-8") as f:
        source_text = f.read()
        try:
            tree = ast.parse(source_text)
        except:
            return {"module_doc": "", "symbols": [], "vars": []}

    module_doc = ast.get_docstring(tree) or ""
    symbols = []
    variables = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node) or "No docstring"
            # Get function arguments
            args = ""
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = ", ".join(a.arg for a in node.args.args)

            source_segment = ast.get_source_segment(source_text, node) or ""
            symbols.append({"name": node.name, "args": args, "doc": doc, "source": source_segment})

        elif include_vars and isinstance(node, (ast.Assign, ast.AnnAssign)):
            source_segment = ast.get_source_segment(source_text, node) or ""
            names = []
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        names.append(target.id)
                    elif isinstance(target, ast.Attribute):
                        names.append(target.attr)
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    names.append(node.target.id)
                elif isinstance(node.target, ast.Attribute):
                    names.append(node.target.attr)

            if names:
                variables.append({"names": names, "source": source_segment})

    return {"module_doc": module_doc, "symbols": symbols, "vars": variables}


def format_docstring(doc):
    if not doc or doc == "No docstring":
        return "*No documentation available.*"
    # Ensure lists starting with '-' have a blank line above them if preceded by text
    lines = doc.splitlines()
    formatted = []
    for i, line in enumerate(lines):
        if (
            i > 0
            and line.strip().startswith("- ")
            and lines[i - 1].strip()
            and not lines[i - 1].strip().startswith("- ")
        ):
            formatted.append("")
        formatted.append(line)
    return "\n".join(formatted)


def main():
    modules = []
    target_dirs = ["Minify", os.path.join("Minify", "core"), os.path.join("Minify", "ui")]

    for d in target_dirs:
        if not os.path.isdir(d):
            continue

        for f in sorted(os.listdir(d)):
            if f.endswith(".py") and not f.startswith("__"):
                path = os.path.join(d, f)
                rel_path = os.path.relpath(path, "Minify")

                # Only include variables for base.py and constants.py
                include_vars = f in ["base.py", "constants.py"]

                result = get_symbols(path, include_vars=include_vars)
                if result["symbols"] or result.get("vars"):
                    modules.append(
                        {
                            "path": rel_path,
                            "symbols": result["symbols"],
                            "vars": result.get("vars", []),
                            "module_doc": result["module_doc"],
                        }
                    )

    symbols_dir = os.path.join("docs", "wiki", "development", "symbols")

    # Cleanup previous generation results
    if os.path.exists(symbols_dir):
        shutil.rmtree(symbols_dir)
    os.makedirs(symbols_dir, exist_ok=True)

    index_content = [
        "# Minify API Symbols Index",
        "",
        "> [!NOTE]",
        "> Module-level variables and constants are only dumped for [core.base](/development/symbols/core.base) and [core.constants](/development/symbols/core.constants). Other modules only contain functions and classes to keep the documentation focused.",
        "",
    ]

    for mod in modules:
        # Format module path with dots and no extension
        mod_name = os.path.splitext(mod["path"].replace(os.sep, "."))[0]

        # Link in the index file (absolute from wiki root)
        index_line = f"- [{mod_name}](/development/symbols/{mod_name})"
        if mod.get("module_doc"):
            # Include the first line of the module docstring as a summary
            summary = mod["module_doc"].strip().splitlines()[0]
            index_line += f" - {summary}"
        index_content.append(index_line)

        # Prepare the individual module file content
        mod_details = [f"# {mod_name}", ""]

        # Include module-level docstring if available
        if mod.get("module_doc"):
            mod_details.append(format_docstring(mod["module_doc"]))
            mod_details.append("")

        for s in mod["symbols"]:
            display_name = f"{s['name']}({s['args']})" if s["args"] else f"{s['name']}()"
            # Simplify header: only the symbol name
            header_text = display_name

            doc_content = format_docstring(s["doc"])
            mod_details.append(f"## `{header_text}`\n\n{doc_content}\n")

            # Sub-summary and source code in a details block with proper spacing (MD031)
            source_block = (
                f"\n<details open><summary>Source</summary>\n\n"
                f"```python\n{s['source'].strip()}\n\n```\n\n"
                f"</details>\n"
            )
            mod_details.append(source_block)

        # Include variables if present
        if mod.get("vars"):
            mod_details.append("## Variables\n")
            for v in mod["vars"]:
                var_names = ", ".join(v["names"])
                mod_details.append(f"### `{var_names}`\n")
                source_block = (
                    f"\n<details open><summary>Source</summary>\n\n"
                    f"```python\n{v['source'].strip()}\n\n```\n\n"
                    f"</details>\n"
                )
                mod_details.append(source_block)

        # Write individual module file
        mod_file_path = os.path.join(symbols_dir, f"{mod_name}.md")
        with open(mod_file_path, "w", encoding="utf-8") as f:
            content = "\n".join(mod_details).strip()
            content = re.sub(r"\n{3,}", "\n\n", content)
            f.write(content + "\n")

    # Write the index file to symbols/README.md
    index_file_path = os.path.join(symbols_dir, "README.md")
    with open(index_file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(index_content).strip() + "\n")

    # Update _sidebar.md
    sidebar_path = os.path.join("docs", "wiki", "_sidebar.md")
    if os.path.exists(sidebar_path):
        with open(sidebar_path, "r", encoding="utf-8") as f:
            sidebar_lines = f.readlines()

        new_sidebar = []
        in_symbols = False
        symbols_found = False

        for line in sidebar_lines:
            if "[Symbols]" in line:
                new_sidebar.append("* [Symbols](/development/symbols/)\n")
                # Sort modules alphabetically
                sorted_modules = sorted(modules, key=lambda x: os.path.splitext(x["path"].replace(os.sep, "."))[0])
                for m in sorted_modules:
                    m_name = os.path.splitext(m["path"].replace(os.sep, "."))[0]
                    new_sidebar.append(f"  * [{m_name}](/development/symbols/{m_name})\n")
                in_symbols = True
                symbols_found = True
            elif in_symbols and line.strip().startswith("* [") and "development/symbols/" in line:
                continue  # Skip existing sub-items
            else:
                in_symbols = False
                new_sidebar.append(line)

        if not symbols_found:
            new_sidebar.append("\n* [Symbols](/development/symbols/)\n")
            sorted_modules = sorted(modules, key=lambda x: os.path.splitext(x["path"].replace(os.sep, "."))[0])
            for m in sorted_modules:
                m_name = os.path.splitext(m["path"].replace(os.sep, "."))[0]
                new_sidebar.append(f"  * [{m_name}](/development/symbols/{m_name})\n")

        with open(sidebar_path, "w", encoding="utf-8") as f:
            f.writelines(new_sidebar)

    print(f"Successfully generated multi-file symbol dump and updated sidebar.")


if __name__ == "__main__":
    main()
