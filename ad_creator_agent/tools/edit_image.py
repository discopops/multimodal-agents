import os
from pydantic import BaseModel
from pydantic import Field
from google import genai
from ad_creator_agent.tools.utils import (
    IMAGES_DIR,
    REFERENCE_FOLDER,
    validate_num_variants,
    get_api_key,
    load_image_by_name,
    extract_image_from_response,
    process_variant_result,
    run_parallel_variants,
    create_result_summary,
    create_image_urls,
    compress_image_for_base64
)
from typing import Optional, Literal
from agents.tool import ToolOutputImage, function_tool

# Constants
MODEL_NAME = "gemini-2.5-flash-image-preview"


class EditImage(BaseModel):
    """
    Edit existing images using Google's Gemini 2.5 Flash Image (Nano Banana) model.
    """

    input_image_name: str = Field(
        ...,
        description="Name of the existing image file to edit (without extension).",
    )
    
    edit_prompt: str = Field(
        ...,
        description="Text prompt describing the edits to make to the image",
    )
    
    output_image_name: str = Field(
        ...,
        description="The name for the generated edited image file (without extension)",
    )
    
    num_variants: Optional[int] = Field(
        default=1,
        description="Number of image variants to generate (1-4, default is 1)",
    )

    aspect_ratio: Optional[
        Literal["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]
    ] = Field(
        default="1:1",
        description="The aspect ratio of the generated image (default is 1:1)",
    )

@function_tool
def edit_image(args: EditImage) -> ToolOutputImage:
    try:
        # Validate num_variants
        validation_error = validate_num_variants(args.num_variants)
        if validation_error:
            return validation_error
        
        # Get API key from environment
        api_key, api_error = get_api_key()
        if api_error:
            return api_error
        
        print(f"Editing image with prompt: {args.edit_prompt}")
        print(f"Generating {args.num_variants} variant(s)")
        
        # Initialize the Google AI client
        client = genai.Client(api_key=api_key)
        
        # Load input image
        image, image_path, load_error = load_image_by_name(args.input_image_name, IMAGES_DIR)
        if load_error:
            image, image_path, load_error = load_image_by_name(args.input_image_name, REFERENCE_FOLDER, ['.png', '.jpg', '.jpeg'])
        if load_error:
            return load_error
        print(f"Loaded image: {image_path}")
        
        # Create output directory if it doesn't exist
        os.makedirs(IMAGES_DIR, exist_ok=True)
        
        def edit_single_variant(variant_num):
            """Generate a single edited image variant"""
            try:
                print(f"Generating variant {variant_num}/{args.num_variants}")
                
                # Prepare contents for the API call
                contents = [args.edit_prompt, image]
                
                # Generate edited image using Gemini 2.5 Flash Image
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=contents,
                    config=genai.types.GenerateContentConfig(
                        image_config=genai.types.ImageConfig(
                            aspect_ratio=args.aspect_ratio,
                        )
                    ),
                )
                
                # Extract the generated image and any text output
                edited_image, text_output = extract_image_from_response(response)
                
                if edited_image is None:
                    print(f"Warning: No image was generated for variant {variant_num}. Text output: {text_output}")
                    return None
                
                # Process variant result
                return process_variant_result(
                    variant_num, edited_image, args.output_image_name, args.num_variants, 
                    compress_image_for_base64
                )
            except Exception as e:
                print(f"Error generating variant {variant_num}: {str(e)}")
                return None
        
        # Run variants in parallel
        results = run_parallel_variants(edit_single_variant, args.num_variants)
        
        if not results:
            return "Error: No variants were successfully generated."
        
        # Create and print result summary
        result_text = create_result_summary(results, "Generated")
        print(result_text)
        
        # Return array of image URLs
        return create_image_urls(results, include_text_labels=False)
            
    except Exception as e:
        return f"Error editing image: {str(e)}"



# Create alias for Agency Swarm tool loading
# edit_image = EditImage

if __name__ == "__main__":
    import asyncio
    import json
    from agency_swarm import MasterContext, RunContextWrapper

    ctx = MasterContext(user_context={}, thread_manager=None, agents={})
    run_ctx = RunContextWrapper(context=ctx)
    result = asyncio.run(
        edit_image.on_invoke_tool(
            run_ctx,
            json.dumps({
                "args": {
                    "input_image_name": "agents-swarms-V3.2",
                    "edit_prompt": "Change the text to 'Are image generation models good now?",
                    "output_image_name": "logo_image_edited",
                    "num_variants": 1
                }
            })
        )
    )
    print(result)
