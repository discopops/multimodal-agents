import os
from pydantic import BaseModel
from pydantic import Field
from google import genai
from ad_creator_agent.tools.utils import (
    IMAGES_DIR,
    validate_num_variants,
    get_api_key,
    extract_image_from_response,
    process_variant_result,
    run_parallel_variants,
    create_result_summary,
    create_image_urls,
    compress_image_for_base64,
)
from agents.tool import ToolOutputImage, function_tool
from typing import Literal, Optional, List
from PIL import Image

# Constants
# Use the stable image model that supports multimodal contents (images + text)
MODEL_NAME = "gemini-2.5-flash-image"
# Hardcoded reference images folder (relative to this file)
REFERENCE_FOLDER = os.path.join(os.path.dirname(__file__), "thumbnail_examples")


class GenerateImage(BaseModel):
    """
    Generate thumbnail images using Google's Gemini 2.5 Flash Image model.

    Designed for YouTube where bold composition, high contrast,
    and strong subject separation are desired. Uses reference images from the
    hardcoded folder `ad_creator_agent/tools/photos` (if present) to steer
    style/composition.
    """

    prompt: str = Field(
        ...,
        description=(
            "Describe the thumbnail subject and style. Keep it concise and outcome-focused."
        ),
    )

    file_name: str = Field(
        ...,
        description="The name for the generated image file (without extension)",
    )

    num_variants: Optional[int] = Field(
        default=1,
        description="Number of image variants to generate (1-4, default is 1)",
    )

    aspect_ratio: Optional[
        Literal["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]
    ] = Field(
        default="16:9",
        description="Aspect ratio. Thumbnails typically use 16:9 (default)",
    )
    include_reference_images: Optional[bool] = Field(
        default=False,
        description="Provides image generation with reference images. Set to true if you want to show user on the image or copy styling from existing thumbnails",
    )


def _prepare_contents(prompt: str) -> list:
    """Build the multimodal contents list: hardcoded folder images then the prompt string.

    Loads up to 8 images from REFERENCE_FOLDER with supported extensions
    (png, jpg, jpeg, webp) in sorted filename order. Missing/unreadable files
    are skipped silently.
    """
    contents: List[object] = []
    reference_folder = REFERENCE_FOLDER
    if reference_folder and os.path.isdir(reference_folder):
        supported_exts = {".png", ".jpg", ".jpeg", ".webp"}
        try:
            files = sorted(os.listdir(reference_folder))
        except Exception:
            files = []
        loaded = 0
        for name in files:
            if loaded >= 8:
                break
            _, ext = os.path.splitext(name.lower())
            if ext not in supported_exts:
                continue
            file_path = os.path.join(reference_folder, name)
            try:
                image = Image.open(file_path)
                contents.append(image)
                loaded += 1
            except Exception:
                continue
    contents.append(prompt)
    return contents


@function_tool
def generate_image(args: GenerateImage) -> ToolOutputImage:
    try:
        # Validate num_variants
        validation_error = validate_num_variants(args.num_variants)
        if validation_error:
            return validation_error

        # Get API key from environment
        api_key, api_error = get_api_key()
        if api_error:
            return api_error

        print(f"Generating thumbnail with prompt: {args.prompt}")
        print(f"Generating {args.num_variants} variant(s)")

        # Initialize the Google AI client
        client = genai.Client(api_key=api_key)

        # Create output directory if it doesn't exist
        os.makedirs(IMAGES_DIR, exist_ok=True)

        def generate_single_variant(variant_num):
            """Generate a single image variant"""
            try:
                print(f"Generating variant {variant_num}/{args.num_variants}")

                if args.include_reference_images:
                    prompt = "I provided 5 thumbnail photos which I used in my previous videos, use them as a reference for how me and my thumbnails look like." \
                            "Now, generate a new thumbnail for my next video, following the instructions below: " + args.prompt
                    contents = _prepare_contents(prompt)
                else:
                    contents = [args.prompt]

                # Generate image using Gemini 2.5 Flash Image with optional references
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=contents,
                    config=genai.types.GenerateContentConfig(
                        image_config=genai.types.ImageConfig(
                            aspect_ratio=args.aspect_ratio,
                        )
                    ),
                )

                # Extract the generated image
                image, text_output = extract_image_from_response(response)

                if image is None:
                    print(
                        f"Warning: No image was generated for variant {variant_num}. Text output: {text_output}"
                    )
                    return None

                # Process variant result
                return process_variant_result(
                    variant_num,
                    image,
                    args.file_name,
                    args.num_variants,
                    compress_image_for_base64,
                )
            except Exception as e:
                print(f"Error generating variant {variant_num}: {str(e)}")
                return None

        # Run variants in parallel
        results = run_parallel_variants(generate_single_variant, args.num_variants)

        if not results:
            return "Error: No variants were successfully generated."

        # Create and print result summary
        result_text = create_result_summary(results, "Generated")
        print(result_text)

        # Return array of image URLs
        # return ToolOutputImage(type="image", image_url=f"data:image/png;base64,{results[0]['base64']}", detail="auto")
        return create_image_urls(results, include_text_labels=True)

    except Exception as e:
        return f"Error generating image: {str(e)}"


# Create alias for Agency Swarm tool loading
# generate_image = GenerateImage

if __name__ == "__main__":
    import asyncio
    import json
    from agency_swarm import MasterContext, RunContextWrapper

    ctx = MasterContext(user_context={}, thread_manager=None, agents={})
    run_ctx = RunContextWrapper(context=ctx)
    result = asyncio.run(
        generate_image.on_invoke_tool(
            run_ctx,
            json.dumps({
                "args": {
                    "prompt": "I provided a few photos which I used in my previous videos. Generate a new thumbnail for my next video. I should be sitting at the desk. On the top left there should be a banner saying 'Build your own AI Agent'",
                    "file_name": "test_image",
                    "num_variants": 4,
                    "aspect_ratio": "16:9",
                }
            })
        )
    )
    print(result)
