import os
import weave
from typing import Dict, List, Optional, Any
from litellm import image_generation

@weave.op(name="image-generate")
async def generate_image(*, 
    prompt: str,
    size: str = "1024x1024",
    quality: str = "standard",
    style: str = "vivid",
    response_format: str = "url"
) -> Dict[str, Any]:
    """
    Generate an image using DALL-E 3 via LiteLLM.

    Args:
        prompt (str): Text description of the desired image (max 4000 characters)
        size (str, optional): Size of the generated image. Defaults to "1024x1024"
        quality (str, optional): Quality of the image. Defaults to "standard"
        style (str, optional): Style of the generated image. Defaults to "vivid"
        response_format (str, optional): Format of the response. Defaults to "url"

    Returns:
        Dict[str, Any]: Response containing the generated image information
    """
    try:
        # Validate size
        valid_sizes = ["1024x1024", "1792x1024", "1024x1792"]
        if size not in valid_sizes:
            raise ValueError(f"Size {size} not supported. Choose from: {valid_sizes}")

        response = image_generation(
            prompt=prompt,
            model="dall-e-3",
            n=1,
            size=size,
            quality=quality,
            style=style,
            response_format=response_format
        )

        # Extract the URL from the first image in the data array
        result = {
            "success": True,
            "images": response["data"],
            "created": response["created"],
            "usage": response["usage"]
        }

        if response["data"]:
            first_image = response["data"][0]
            result["image_url"] = first_image.get("url")

        return result

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Define the tools list in the same format as other tool modules
TOOLS = [
    {
        "definition": {
            "type": "function",
            "function": {
                "name": "image-generate",
                "description": "Generates images based on text descriptions using DALL-E 3. Use this for creating images from text descriptions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Text description of the desired image (max 4000 characters)"
                        },
                        "size": {
                            "type": "string",
                            "description": "Size of the generated image",
                            "enum": ["1024x1024", "1792x1024", "1024x1792"],
                            "default": "1024x1024"
                        },
                        "quality": {
                            "type": "string",
                            "description": "Quality of the image. 'hd' creates images with finer details and greater consistency",
                            "enum": ["standard", "hd"],
                            "default": "standard"
                        },
                        "style": {
                            "type": "string",
                            "description": "Style of the generated image. 'vivid' is hyper-real and dramatic, 'natural' is less hyper-real",
                            "enum": ["vivid", "natural"],
                            "default": "vivid"
                        }
                    },
                    "required": ["prompt"]
                }
            }
        },
        "implementation": generate_image,
        "attributes": {
            "type": "image_generator",
            "model": "dall-e-3",
            "capabilities": {
                "sizes": ["1024x1024", "1792x1024", "1024x1792"],
                "qualities": ["standard", "hd"],
                "styles": ["vivid", "natural"]
            }
        }
    }
] 