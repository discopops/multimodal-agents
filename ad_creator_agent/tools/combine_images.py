import os
import io
from pydantic import BaseModel
from pydantic import Field
from google import genai
from PIL import Image
from ad_creator_agent.tools.utils import (
    IMAGES_DIR,
    REFERENCE_FOLDER,
    validate_num_variants,
    get_api_key,
    load_image_by_name,
    extract_image_parts_from_response,
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

class CombineImages(BaseModel):
    """
    Combine multiple images using Google's Gemini 2.5 Flash Image (Nano Banana) model.
    """

    image_names: list[str] = Field(
        ...,
        description="List of image file names (without extension) to combine.",
    )
    
    text_instruction: str = Field(
        ...,
        description="Text instruction describing how to combine the images",
    )
    
    file_name: str = Field(
        ...,
        description="The name for the generated combined image file (without extension)",
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
def combine_images(args: CombineImages) -> ToolOutputImage:
    try:
        # Validate num_variants
        validation_error = validate_num_variants(args.num_variants)
        if validation_error:
            return validation_error
        
        # Get API key from environment
        api_key, api_error = get_api_key()
        if api_error:
            return api_error
        
        print(f"Combining images with instruction: {args.text_instruction}")
        print(f"Generating {args.num_variants} variant(s)")
        
        # Initialize the Google AI client
        client = genai.Client(api_key=api_key)
        
        # Load images using image names
        images = []
        for image_name in args.image_names:
            image, image_path, load_error = load_image_by_name(image_name, IMAGES_DIR, ['.png', '.jpg', '.jpeg'])
            if load_error:
                image, image_path, load_error = load_image_by_name(image_name, REFERENCE_FOLDER, ['.png', '.jpg', '.jpeg'])
            if load_error:
                return load_error
            images.append(image)
            print(f"Loaded image: {image_path}")
        
        # Create output directory if it doesn't exist
        os.makedirs(IMAGES_DIR, exist_ok=True)
        
        def combine_single_variant(variant_num):
            """Generate a single combined image variant"""
            try:
                print(f"Generating variant {variant_num}/{args.num_variants}")
                
                # Prepare contents for the API call
                contents = images + [args.text_instruction]
                
                # Generate combined image using Gemini 2.5 Flash Image
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
                image_parts = extract_image_parts_from_response(response)
                
                if not image_parts:
                    print(f"Warning: No image was generated for variant {variant_num}.")
                    return None
                
                # Create the combined image
                combined_image = Image.open(io.BytesIO(image_parts[0]))
                
                # Process variant result
                return process_variant_result(
                    variant_num, combined_image, args.file_name, args.num_variants, 
                    compress_image_for_base64
                )
            except Exception as e:
                print(f"Error generating variant {variant_num}: {str(e)}")
                return None
        
        # Run variants in parallel
        results = run_parallel_variants(combine_single_variant, args.num_variants)
        
        if not results:
            return "Error: No variants were successfully generated."
        
        # Create and print result summary
        result_text = create_result_summary(results, "Generated")
        print(result_text)
        
        # Return array of image URLs
        return create_image_urls(results, include_text_labels=False)
            
    except Exception as e:
        return f"Error combining images: {str(e)}"



# Create alias for Agency Swarm tool loading
# combine_images = CombineImages

if __name__ == "__main__":
    # Example usage with Google Gemini 2.5 Flash Image
    tool = CombineImages(
        image_names=["laptop_image_variant_2", "logo_image_variant_2"],
        text_instruction="Take the first image of a laptop on a table. Add the logo from the second image into the middle of the laptop. Remove the background of the logo and make it transparent. Ensure the laptop and features remain completely unchanged. The logo should look like it's naturally attached.",
        file_name="laptop_with_logo",
        num_variants=2
    )
    result = tool.run()
    print(result)
