# Tools

The Tools API in Tyler provides a way to define and use custom tools that your agent can interact with.

## Tool Interface

```typescript
interface Tool {
  name: string;
  description: string;
  parameters: {
    type: 'object';
    properties: Record<string, {
      type: string;
      description: string;
      [key: string]: any;
    }>;
    required?: string[];
  };
  execute: (params: any) => Promise<any>;
}
```

## Properties

- `name` (string): The unique identifier for the tool
- `description` (string): A detailed description of what the tool does
- `parameters` (object): JSON Schema definition of the tool's parameters
- `execute` (function): The function that implements the tool's functionality

## Creating a Custom Tool

```typescript
import { Tool } from 'tyler';

const myTool: Tool = {
  name: 'searchDatabase',
  description: 'Search the database for specific records',
  parameters: {
    type: 'object',
    properties: {
      query: {
        type: 'string',
        description: 'The search query'
      },
      limit: {
        type: 'number',
        description: 'Maximum number of results to return'
      }
    },
    required: ['query']
  },
  execute: async (params) => {
    // Implementation of the tool
    const { query, limit = 10 } = params;
    // ... search logic ...
    return results;
  }
};
```

## Registering Tools

Tools can be registered when creating an agent:

```typescript
import { Agent } from 'tyler';

const agent = new Agent({
  tools: [myTool],
  // ... other configuration
});
```

## Built-in Tools

Tyler comes with several built-in tools:

- File Operations
- Web Requests
- Database Queries
- System Commands

See the [Examples](../examples/using-tools.md) section for more details on using tools. 