"""Example custom tools file for Tyler Chat CLI.

This file demonstrates how to create custom tools that can be loaded
by the Tyler Chat CLI using the custom_tools configuration option.
"""

async def get_weather(location: str, unit: str = "celsius") -> str:
    """Example async weather tool implementation."""
    # In a real implementation, this would make an async API call
    mock_weather = {
        "new york": {"temp": 20, "condition": "sunny", "humidity": 45},
        "london": {"temp": 15, "condition": "rainy", "humidity": 80},
        "tokyo": {"temp": 25, "condition": "cloudy", "humidity": 60},
        "sydney": {"temp": 22, "condition": "clear", "humidity": 55},
    }
    
    location = location.lower()
    if location not in mock_weather:
        return f"Error: Weather data not available for {location}"
    
    weather = mock_weather[location]
    temp = weather["temp"]
    
    # Convert temperature if needed
    if unit.lower() == "fahrenheit":
        temp = (temp * 9/5) + 32
    
    return f"Current weather in {location.title()}:\n" \
           f"Temperature: {temp}°{'F' if unit.lower() == 'fahrenheit' else 'C'}\n" \
           f"Condition: {weather['condition'].title()}\n" \
           f"Humidity: {weather['humidity']}%"

def calculate(expression: str) -> str:
    """Example calculator tool implementation."""
    try:
        # WARNING: eval is used here for demonstration only
        # In a real implementation, use a safe expression evaluator
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Error calculating: {str(e)}"

# List of tool definitions that will be loaded by the CLI
TOOLS = [
    {
        "definition": {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name (e.g., New York, London, Tokyo, Sydney)"
                        },
                        "unit": {
                            "type": "string",
                            "description": "Temperature unit",
                            "enum": ["celsius", "fahrenheit"],
                            "default": "celsius"
                        }
                    },
                    "required": ["location"]
                }
            }
        },
        "implementation": get_weather,
        "attributes": {
            "category": "weather",
            "version": "1.0",
            "is_async": True
        }
    },
    {
        "definition": {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "Perform a calculation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "The mathematical expression to evaluate"
                        }
                    },
                    "required": ["expression"]
                }
            }
        },
        "implementation": calculate,
        "attributes": {
            "category": "math",
            "version": "1.0"
        }
    }
] 