import os
import shutil


file_management_instructions="""**START BY SETTING A BASE_DIR USING `set_base_dir` first**

## Objective
- Keep all operations inside the active base directory set by `set_base_dir`.
- Treat relative paths as trusted workspace paths and reject anything that attempts to escape the allowed directory.
- Prefer precise, minimal operations over broad or destructive changes.

## Safe Operating Rules
- Avoid overwriting user data unless the task clearly requires it.
- Validate every path before creating, reading, writing, renaming, or deleting anything.
- Reject traversal attempts such as `..` or other path escapes before execution.
- Always check whether a target exists before rename, deletion, or patching.
- Ensure parent directories exist before creating files or nested folders.

## Reliability and Performance
- Keep outputs concise but informative: describe the action, target path, and final result.
- Prefer targeted operations over full-file rewrites or recursive deletes unless explicitly needed.
- Surface the real error clearly when a tool fails, instead of hiding the cause.
- Confirm the final path before returning success.

## Execution Pattern
1. Validate the target path.
2. Perform the file or directory action.
3. Confirm the result clearly and briefly.
"""

BASE_DIR = None
#Helper Functions
def check_path(path:str):
    if not BASE_DIR:
        return {"status":False,"message":"BASE DIRECTORY not set, please set_base_dir first."}
    if path.startswith('..'):
        return {"status":False,"message":"BASE DIRECTORY escaping detected!"}
    return {"status":True,"message":None}

def resolve_path(path:str):
    return os.path.join(BASE_DIR,path)

#Directory Management
def make_dir(path:str,exist_ok:bool=True):
    full_path=resolve_path(path)
    check=check_path(path)
    if not check["status"]:
        return {"role":"tool","name":"make_dir","content":check["message"]}
    try:
        os.makedirs(full_path,exist_ok=exist_ok)
        return {"role":"tool","name":"make_dir","content":f"Successfully made directory: {path}"}
    except Exception as e:
        #utils.log(line=f"Error in making dir; {e}",level="WARN")
        return {"role":"tool","name":"make_dir","content":f"An error occured while making directory; {e}"}

def delete_dir(path:str,recursive:bool=False):
    check=check_path(path)
    if not check["status"]:
        return {"role":"tool","name":"delete_dir","content":check["message"]}
    full_path = resolve_path(path)
    if not os.path.exists(full_path):
        return {"role":"tool","name":"delete_dir","content":f"Path does not exist: {full_path}"}
    try:
        if recursive:
            shutil.rmtree(full_path)
        else:
            os.rmdir(full_path)
        return {"role":"tool","name":"delete_dir","content":f"Successfully deleted directory: {path}"}
    except Exception as e:
        return {"role":"tool","name":"delete_dir","content":f"An error occurred while deleting directory; {e}"}

def list_dir(path:str):
    check=check_path(path)
    if not check["status"]:
        return {"role":"tool","name":"make_dir","content":check["message"]}
    full_path=resolve_path(path)
    if not os.path.exists(full_path):
        return {"role":"tool","name":"list_dir","content":f"Path does not exist: {full_path}"}
    l=os.listdir(full_path)
    return {"role":"tool","name":"list_dir","content":f"Items in Directory: {l}"}

def rename_dir(path:str, new_path:str):
    check_old=check_path(path)
    check_new=check_path(new_path)
    if not check_old["status"]:
        return {"role":"tool","name":"rename_dir","content":check_old["message"]}
    if not check_new["status"]:
        return {"role":"tool","name":"rename_dir","content":check_new["message"]}
    full_old_path = resolve_path(path)
    full_new_path = resolve_path(new_path)
    if not os.path.exists(full_old_path):
        return {"role":"tool","name":"rename_dir","content":f"Path does not exist: {full_old_path}"}
    try:
        os.rename(full_old_path, full_new_path)
        return {"role":"tool","name":"rename_dir","content":f"Successfully renamed directory: {path} -> {new_path}"}
    except Exception as e:
        return {"role":"tool","name":"rename_dir","content":f"An error occurred while renaming directory; {e}"}

def set_base_dir(abs_path:str):
    global BASE_DIR
    BASE_DIR = abs_path
    return {"role":"tool","name":"set_base_dir","content":f"Base Directory set to {BASE_DIR}"}

def search_dir(path:str, pattern:str=None):
    check=check_path(path)
    if not check["status"]:
        return {"role":"tool","name":"search_dir","content":check["message"]}
    full_path=resolve_path(path)
    if not os.path.exists(full_path):
        return {"role":"tool","name":"search_dir","content":f"Path does not exist: {full_path}"}
    matches=[]
    for root, dirs, files in os.walk(full_path):
        for name in dirs + files:
            if pattern is None or pattern.lower() in name.lower():
                matches.append(os.path.relpath(os.path.join(root, name), full_path))
    return {"role":"tool","name":"search_dir","content":f"Search results: {matches}"}

#File management
def create_file(path:str, content:str=""):
    check=check_path(path)
    if not check["status"]:
        return {"role":"tool","name":"create_file","content":check["message"]}
    full_path=resolve_path(path)
    parent_dir = os.path.dirname(full_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)
    try:
        with open(full_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return {"role":"tool","name":"create_file","content":f"Successfully created file: {path}"}
    except Exception as e:
        return {"role":"tool","name":"create_file","content":f"An error occurred while creating file; {e}"}

def patch_file(path:str, old_text:str, new_text:str):
    check=check_path(path)
    if not check["status"]:
        return {"role":"tool","name":"patch_file","content":check["message"]}
    full_path=resolve_path(path)
    if not os.path.exists(full_path):
        return {"role":"tool","name":"patch_file","content":f"Path does not exist: {full_path}"}
    try:
        with open(full_path, 'r', encoding='utf-8') as file:
            content = file.read()
        if old_text not in content:
            return {"role":"tool","name":"patch_file","content":f"The specified text was not found in file: {path}"}
        updated_content = content.replace(old_text, new_text, 1)
        with open(full_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
        return {"role":"tool","name":"patch_file","content":f"Successfully patched file: {path}"}
    except Exception as e:
        return {"role":"tool","name":"patch_file","content":f"An error occurred while patching file; {e}"}

def write_file(path:str, content:str=""):
    check=check_path(path)
    if not check["status"]:
        return {"role":"tool","name":"write_file","content":check["message"]}
    full_path=resolve_path(path)
    parent_dir = os.path.dirname(full_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)
    try:
        with open(full_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return {"role":"tool","name":"write_file","content":f"Successfully wrote file: {path}"}
    except Exception as e:
        return {"role":"tool","name":"write_file","content":f"An error occurred while writing file; {e}"}

def read_file(path:str, start:int=1, end:int=100):
    check=check_path(path)
    if not check["status"]:
        return {"role":"tool","name":"read_file","content":check["message"]}
    full_path=resolve_path(path)
    if not os.path.exists(full_path):
        return {"role":"tool","name":"read_file","content":f"Path does not exist: {full_path}"}
    if start < 0 or end < start:
        return {"role":"tool","name":"read_file","content":"Invalid line range: start must be non-negative and end must be greater than or equal to start."}
    try:
        with open(full_path, 'r', encoding='utf-8') as file:
            content = ''.join(file.readlines()[start-1:end])
        return {"role":"tool","name":"read_file","content":content}
    except UnicodeDecodeError:
        return {"role":"tool","name":"read_file","content":f"Cannot read binary file as UTF-8 text: {path}. Use a file-type-specific reader for PDF or other binary files."}
    except Exception as e:
        return {"role":"tool","name":"read_file","content":f"An error occurred while reading file; {e}"}

def read_metadata(path:str):
    check=check_path(path)
    if not check["status"]:
        return {"role":"tool","name":"read_metadata","content":check["message"]}
    full_path=resolve_path(path)
    if not os.path.exists(full_path):
        return {"role":"tool","name":"read_metadata","content":f"Path does not exist: {full_path}"}
    try:
        metadata = os.stat(full_path)
        return {"role":"tool","name":"read_metadata","content":{
            "path": full_path,
            "type": "directory" if os.path.isdir(full_path) else "file",
            "size_bytes": metadata.st_size,
            "created_timestamp": metadata.st_ctime,
            "modified_timestamp": metadata.st_mtime,
            "accessed_timestamp": metadata.st_atime,
            "permissions": metadata.st_mode
        }}
    except Exception as e:
        return {"role":"tool","name":"read_metadata","content":f"An error occurred while reading metadata; {e}"}

def rename_file(path:str, new_path:str):
    check_old=check_path(path)
    check_new=check_path(new_path)
    if not check_old["status"]:
        return {"role":"tool","name":"rename_file","content":check_old["message"]}
    if not check_new["status"]:
        return {"role":"tool","name":"rename_file","content":check_new["message"]}
    full_old_path = resolve_path(path)
    full_new_path = resolve_path(new_path)
    if not os.path.exists(full_old_path):
        return {"role":"tool","name":"rename_file","content":f"Path does not exist: {full_old_path}"}
    try:
        os.rename(full_old_path, full_new_path)
        return {"role":"tool","name":"rename_file","content":f"Successfully renamed file: {path} -> {new_path}"}
    except Exception as e:
        return {"role":"tool","name":"rename_file","content":f"An error occurred while renaming file; {e}"}

def delete_file(path:str):
    check=check_path(path)
    if not check["status"]:
        return {"role":"tool","name":"delete_file","content":check["message"]}
    full_path=resolve_path(path)
    if not os.path.exists(full_path):
        return {"role":"tool","name":"delete_file","content":f"Path does not exist: {full_path}"}
    try:
        os.remove(full_path)
        return {"role":"tool","name":"delete_file","content":f"Successfully deleted file: {path}"}
    except Exception as e:
        return {"role":"tool","name":"delete_file","content":f"An error occurred while deleting file; {e}"}


file_management_tool_map={
    "make_dir": make_dir,
    "delete_dir": delete_dir,
    "list_dir": list_dir,
    "rename_dir": rename_dir,
    "set_base_dir": set_base_dir,
    "search_dir": search_dir,
    "create_file": create_file,
    "patch_file": patch_file,
    "write_file": write_file,
    "read_file": read_file,
    "read_metadata": read_metadata,
    "rename_file": rename_file,
    "delete_file": delete_file,
}
if __name__=="__main__":
    print(set_base_dir(r"D:\\"))
    input()
    print(make_dir(r'\moda'))
    input()
    print(make_dir(r'\moda\a\b'))
    input()
    print(delete_dir(r'\moda\a',recursive=True))
    input()
    print(list_dir(r'\\'))
    input()
    print(rename_dir(r'\moda',r'\modassir'))
    input()
    print(create_file(r'\modassir\1.txt',"Hello, Test123"))
    input()
    print(delete_file(r"moda\1.txt"))
    input()
    print(patch_file(r'modassir/1.txt','Test','It works!!'))
    input()
    print(rename_file(r'modassir/1.txt',r'modassir/2.txt'))
    input()
    print("End")
    #print(make_dir(r'moda\1'))
