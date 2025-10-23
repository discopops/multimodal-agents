import os
import io
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
from agents.tool import ToolOutputImage, ToolOutputText

# Constants
IMAGES_DIR = "./generated_images"
OUTPUT_FORMAT = "png"


def validate_num_variants(num_variants):
    """Validate num_variants parameter"""
    if num_variants < 1 or num_variants > 4:
        return "Error: num_variants must be between 1 and 4."
    return None


def get_api_key():
    """Get Google AI API key from environment"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None, "Error: Google AI API key not provided. Set GOOGLE_API_KEY environment variable."
    return api_key, None


def create_filename(file_name, variant_num, num_variants, output_format):
    """Create filename for image variant"""
    if num_variants == 1:
        image_name = file_name
    else:
        image_name = f"{file_name}_variant_{variant_num}"
    filename = f"{image_name}.{output_format}"
    return image_name, filename


def load_image_by_name(image_name, images_dir, extensions=None):
    """Load image by name, trying different extensions"""
    if extensions is None:
        extensions = ['.png', '.jpg', '.jpeg', '.webp']
    
    for ext in extensions:
        potential_path = os.path.join(images_dir, f"{image_name}{ext}")
        if os.path.exists(potential_path):
            try:
                image = Image.open(potential_path)
                return image, potential_path, None
            except Exception as e:
                return None, None, f"Error loading image {potential_path}: {str(e)}"
    
    return None, None, f"Error: Image file not found: {image_name} (tried {', '.join(extensions)})"


def extract_image_from_response(response):
    """Extract image from Gemini API response"""
    image = None
    text_output = ""
    
    for part in response.candidates[0].content.parts:
        if part.text is not None:
            text_output += part.text
        elif part.inline_data is not None:
            image = Image.open(io.BytesIO(part.inline_data.data))
    
    return image, text_output


def extract_image_parts_from_response(response):
    """Extract image parts from Gemini API response (for combine_images)"""
    image_parts = [
        part.inline_data.data
        for part in response.candidates[0].content.parts
        if part.inline_data
    ]
    return image_parts


def process_variant_result(variant_num, image, file_name, num_variants, compress_func):
    """Process a single variant result - save image and create result dict"""
    # Create filename for this variant
    image_name, filename = create_filename(file_name, variant_num, num_variants, OUTPUT_FORMAT)
    filepath = os.path.join(IMAGES_DIR, filename)
    
    # Save the image
    image.save(filepath, OUTPUT_FORMAT)
    
    # Convert image to compressed base64 for agent output
    compressed_b64 = compress_func(image)
    
    print(f"Variant {variant_num} saved to: {filepath}")
    
    return {
        "variant": variant_num,
        "file_path": filepath,
        "image_name": image_name,
        "base64": compressed_b64,
    }


def run_parallel_variants(variant_func, num_variants):
    """Run multiple variants in parallel using ThreadPoolExecutor"""
    results = []
    
    with ThreadPoolExecutor(max_workers=min(num_variants, 4)) as executor:
        # Submit all tasks
        future_to_variant = {
            executor.submit(variant_func, i + 1): i + 1 
            for i in range(num_variants)
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_variant):
            result = future.result()
            if result is not None:
                results.append(result)
    
    return results


def create_result_summary(results, operation_name):
    """Create result summary text"""
    result_text = f"Generated {len(results)} variant(s) successfully!\n"
    for result in results:
        result_text += f"Variant {result['variant']}: {result['file_path']}\n"
    return result_text


def create_image_urls(results, include_text_labels=False):
    """Create image URLs array for agent output"""
    image_urls = []
    for result in results:
        if include_text_labels:
            image_urls.append(ToolOutputText(type="text", text=f"{result['image_name']}:\n"))
        image_urls.append(ToolOutputImage(type="image", image_url=f"data:image/png;base64,{result['base64']}", detail="auto"))
    return image_urls


def image_to_base64(image, output_format='PNG'):
    """Convert image to base64 string"""
    buffer = io.BytesIO()
    image.save(buffer, format=output_format)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    return image_base64


def compress_image_for_base64(image, max_size=(800, 800), quality=65):
    """Compress image for base64 output while keeping original uncompressed and aspect ratio"""
    # Create a copy to avoid modifying the original
    compressed_image = image.copy()
    
    # Calculate new size while maintaining aspect ratio
    original_width, original_height = compressed_image.size
    max_width, max_height = max_size
    
    # Calculate scaling factor to fit within max_size while maintaining aspect ratio
    width_ratio = max_width / original_width
    height_ratio = max_height / original_height
    scale_factor = min(width_ratio, height_ratio, 1.0)  # Don't upscale
    
    # Only resize if the image is larger than max_size
    if scale_factor < 1.0:
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        compressed_image = compressed_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Convert to RGB if necessary (for JPEG compression)
    if compressed_image.mode in ('RGBA', 'LA', 'P'):
        # Create a white background
        background = Image.new('RGB', compressed_image.size, (255, 255, 255))
        if compressed_image.mode == 'P':
            compressed_image = compressed_image.convert('RGBA')
        background.paste(compressed_image, mask=compressed_image.split()[-1] if compressed_image.mode == 'RGBA' else None)
        compressed_image = background
    
    # Save as JPEG with compression
    buffer = io.BytesIO()
    compressed_image.save(buffer, format='JPEG', quality=quality, optimize=True)
    buffer.seek(0)
    compressed_base64 = base64.b64encode(buffer.getvalue()).decode()
    return compressed_base64
