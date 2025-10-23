import base64
import mimetypes
import os
from typing import List

from agents.tool import ToolOutputImage, function_tool


@function_tool
def load_images(file_paths: List[str]) -> List[ToolOutputImage]:
    """
    Load image files from local filesystem and return them as data URLs.
    Supports both absolute and relative paths. Only image/* MIME types are allowed.
    """
    results = []
    
    for file_path in file_paths:
        # Determine if path is absolute or relative
        if os.path.isabs(file_path):
            full_path = file_path
        else:
            # Convert relative path to absolute
            full_path = os.path.abspath(file_path)

        # Check if path exists
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check if it's a file (not a directory)
        if not os.path.isfile(full_path):
            raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")
        
        # Determine the MIME type
        mime_type, _ = mimetypes.guess_type(full_path)
        if not (mime_type and mime_type.startswith('image/')):
            raise ValueError(f"Unsupported file type: {mime_type or 'unknown'}. Only image files are allowed.")

        # Return as ToolOutputImage with data URL
        with open(full_path, 'rb') as f:
            file_content = f.read()
            base64_content = base64.b64encode(file_content).decode('utf-8')
        data_url = f"data:{mime_type};base64,{base64_content}"
        results.append(ToolOutputImage(image_url=data_url))
    
    return results


if __name__ == "__main__":
    import asyncio
    import json
    from agency_swarm import MasterContext, RunContextWrapper

    ctx = MasterContext(user_context={}, thread_manager=None, agents={})
    run_ctx = RunContextWrapper(context=ctx)
    result = asyncio.run(load_images.on_invoke_tool(run_ctx, json.dumps({"file_paths": ["test_files/test_file.png"]})))
    print(result)