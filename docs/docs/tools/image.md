# Image Tools

The image module provides tools for generating and manipulating images using DALL-E 3. These tools allow you to create high-quality images from text descriptions.

## Configuration

Before using image tools, you need to set up your OpenAI API key:

```bash
OPENAI_API_KEY=your-api-key
```

You can get an API key from the [OpenAI platform](https://platform.openai.com/api-keys).

## Available Tools

### image-generate

Generates images based on text descriptions using DALL-E 3.

#### Parameters

- `prompt` (string, required)
  - Text description of the desired image
  - Maximum 4000 characters
  - Should be detailed and specific
  - Can include:
    - Style descriptions
    - Composition details
    - Color preferences
    - Lighting information
    - Artistic references

- `size` (string, optional)
  - Size of the generated image
  - Default: "1024x1024"
  - Options:
    - "1024x1024": Square format
    - "1792x1024": Landscape format
    - "1024x1792": Portrait format
  - Choose based on intended use

- `quality` (string, optional)
  - Quality level of the generated image
  - Default: "standard"
  - Options:
    - "standard": Normal quality, faster generation
    - "hd": Higher quality with finer details
  - HD is recommended for:
    - Professional use
    - Detailed images
    - When quality is critical

- `style` (string, optional)
  - Visual style of the generated image
  - Default: "vivid"
  - Options:
    - "vivid": Hyper-real and dramatic
    - "natural": More photorealistic
  - Choose based on desired aesthetic

#### Response Format

The tool returns a dictionary with:
- `success`: Boolean indicating success
- `description`: Revised prompt used for generation
- `details`: Generation metadata
  - `filename`: Generated image filename
  - `size`: Image dimensions
  - `quality`: Quality setting used
  - `style`: Style setting used
  - `created`: Timestamp
- Files array containing:
  - `content`: Image data
  - `filename`: Image filename
  - `mime_type`: Image format
  - `description`: Image description

#### Example Usage

```python
from tyler.models import Agent, Thread, Message

# Create an agent with image tools
agent = Agent(
    model_name="gpt-4o",
    purpose="To help generate images",
    tools=["image"]
)

# Create a thread with an image generation request
thread = Thread()
message = Message(
    role="user",
    content=(
        "Generate a beautiful image of a serene Japanese garden "
        "with a traditional wooden bridge over a koi pond, "
        "cherry blossoms in full bloom, and a small tea house "
        "in the background. Make it look like a wood block print."
    )
)
thread.add_message(message)

# Process the thread - agent will use image-generate tool
processed_thread, new_messages = await agent.go(thread)

# The generated image will be attached to the tool response message
```

## Best Practices

1. **Prompt Engineering**
   - Be specific and detailed
   - Include style preferences
   - Specify important elements
   - Consider composition

2. **Size Selection**
   - Choose appropriate aspect ratio
   - Consider intended use
   - Account for resolution needs

3. **Quality Settings**
   - Use HD for important images
   - Balance quality vs. speed
   - Consider cost implications

4. **Style Guidance**
   - Match style to content
   - Consider end use
   - Be consistent across sets

## Common Use Cases

1. **Creative Projects**
   - Artwork generation
   - Design inspiration
   - Visual concepts

2. **Content Creation**
   - Blog illustrations
   - Social media content
   - Presentation visuals

3. **Prototyping**
   - Design mockups
   - Visual concepts
   - Style exploration

4. **Educational Content**
   - Visual explanations
   - Teaching materials
   - Concept illustrations

## Limitations

1. **Content Restrictions**
   - No explicit content
   - No harmful content
   - No copyrighted material
   - No real person generation

2. **Technical Limits**
   - Maximum prompt length
   - Fixed size options
   - Generation time varies
   - Cost per image

3. **Quality Considerations**
   - Style consistency
   - Detail accuracy
   - Text rendering
   - Complex scenes

## Cost Considerations

DALL-E 3 pricing varies by:
- Image size
- Quality setting
- Number of images
- Usage volume

Consider:
- Budget allocation
- Quality requirements
- Usage patterns
- Batch processing

## Error Handling

Common errors and solutions:

1. **API Errors**
   - Check API key
   - Verify quota
   - Handle rate limits

2. **Content Filters**
   - Review prompt guidelines
   - Adjust content description
   - Check restricted terms

3. **Generation Issues**
   - Refine prompts
   - Adjust parameters
   - Try alternative descriptions

## Tips for Better Results

1. **Prompt Structure**
   ```
   [Subject] in [Style] with [Details],
   featuring [Elements] and [Atmosphere].
   [Additional style guidance].
   ```

2. **Style Keywords**
   - Artistic: "oil painting", "watercolor", "digital art"
   - Lighting: "soft light", "dramatic shadows", "golden hour"
   - Mood: "serene", "dramatic", "whimsical"
   - Composition: "close-up", "wide angle", "bird's eye view"

3. **Detail Enhancement**
   - Specify colors
   - Describe textures
   - Include lighting
   - Note important elements

4. **Quality Optimization**
   - Use HD for detailed scenes
   - Match size to purpose
   - Consider style impact
   - Test different approaches 