import os
import weave
import base64
from typing import Dict, List, Optional, Any, Tuple
from litellm import image_generation
import httpx

@weave.op(name="image-generate")
async def generate_image(*, 
    prompt: str,
    size: str = "1024x1024",
    quality: str = "standard",
    style: str = "vivid",
    response_format: str = "url"
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Generate an image using DALL-E 3 via LiteLLM.

    Args:
        prompt (str): Text description of the desired image (max 4000 characters)
        size (str, optional): Size of the generated image. Defaults to "1024x1024"
        quality (str, optional): Quality of the image. Defaults to "standard"
        style (str, optional): Style of the generated image. Defaults to "vivid"
        response_format (str, optional): Format of the response. Defaults to "url"

    Returns:
        Tuple[Dict[str, Any], List[Dict[str, Any]]]: Tuple containing:
            - Dict with success status and metadata
            - List of file dictionaries with base64 encoded content and metadata
    """
    try:
        # Validate size
        valid_sizes = ["1024x1024", "1792x1024", "1024x1792"]
        if size not in valid_sizes:
            return (
                {
                    "success": False,
                    "error": f"Size {size} not supported. Choose from: {valid_sizes}"
                },
                []  # Empty files list for error case
            )

        response = image_generation(
            prompt=prompt,
            model="dall-e-3",
            n=1,
            size=size,
            quality=quality,
            style=style,
            response_format=response_format
        )

        if not response["data"]:
            return (
                {
                    "success": False,
                    "error": "No image data received"
                },
                []
            )

        # Get the first image URL
        image_url = response["data"][0].get("url")
        if not image_url:
            return (
                {
                    "success": False,
                    "error": "No image URL in response"
                },
                []
            )

        # Fetch the image bytes
        async with httpx.AsyncClient() as client:
            img_response = await client.get(image_url)
            img_response.raise_for_status()
            image_bytes = img_response.content

        # Create a unique filename based on timestamp
        filename = f"generated_image_{response['created']}.png"
        description = response["data"][0].get("revised_prompt", prompt)

        # Base64 encode the image bytes
        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        # Return tuple with content dict and files list
        return (
            {
                "success": True,
                "description": description,
                "details": {
                    "filename": filename,
                    "size": size,
                    "quality": quality,
                    "style": style,
                    "created": response["created"]
                }
            },
            [{
                "content": base64_image,  # Now base64 encoded
                "filename": filename,
                "mime_type": "image/png",
                "description": description
            }]
        )

    except Exception as e:
        return (
            {
                "success": False,
                "error": str(e)
            },
            []  # Empty files list for error case
        )

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
        "implementation": generate_image
    }
] 