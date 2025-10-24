import base64
import mimetypes
import os
from typing import List

from PIL import Image
from agents.tool import ToolOutputImage, function_tool, ToolOutputText
from ad_creator_agent.tools.utils import compress_image_for_base64, REFERENCE_FOLDER

@function_tool
def load_templates() -> List[ToolOutputImage]:
    """
    Load image files from local filesystem and return them as data URLs.
    Supports both absolute and relative paths. Only image/* MIME types are allowed.
    """
    results = []
    file_paths = []

    if REFERENCE_FOLDER and os.path.isdir(REFERENCE_FOLDER):
        supported_exts = {".png", ".jpg", ".jpeg", ".webp"}
        try:
            files = sorted(os.listdir(REFERENCE_FOLDER))
        except Exception:
            files = []
        for name in files:
            _, ext = os.path.splitext(name.lower())
            if ext not in supported_exts:
                continue
            file_path = os.path.join(REFERENCE_FOLDER, name)
            try:
                file_paths.append(file_path)
            except Exception:
                continue
    
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

        # Open image and compress to reduce size for transport
        try:
            image = Image.open(full_path)
            compressed_b64 = compress_image_for_base64(image)
            # We compress to JPEG in compress_image_for_base64
            data_url = f"data:image/jpeg;base64,{compressed_b64}"
            results.append(ToolOutputText(type="text", text=f"{full_path}:"))
            results.append(ToolOutputImage(type="image", image_url=data_url, detail="auto"))
        except Exception:
            # Fallback to raw file bytes if compression fails
            with open(full_path, 'rb') as f:
                file_content = f.read()
                base64_content = base64.b64encode(file_content).decode('utf-8')
            data_url = f"data:{mime_type};base64,{base64_content}"
            results.append(ToolOutputText(type="text", text=f"{full_path}:"))
            results.append(ToolOutputImage(type="image", image_url=data_url, detail="auto"))
    
    return results


if __name__ == "__main__":
    import asyncio
    import json
    from agency_swarm import MasterContext, RunContextWrapper

    ctx = MasterContext(user_context={}, thread_manager=None, agents={})
    run_ctx = RunContextWrapper(context=ctx)
    result = asyncio.run(load_templates.on_invoke_tool(run_ctx, json.dumps({})))
    print(result)