import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */
const sidebars: SidebarsConfig = {
  // Documentation sidebar
  documentationSidebar: [
    'intro',
    'installation',
    'quick-start',
    'configuration',
    'chat-with-tyler',
    'core-concepts',
    {
      type: 'category',
      label: 'Examples',
      items: [
        'examples/using-tools',
        'examples/streaming',
        'examples/tools-streaming',
        'examples/full-configuration',
        'examples/database-storage',
        'examples/interrupt-tools',
        'examples/message-attachments'
      ],
    }
  ],

  // API Reference sidebar
  apiSidebar: [
    {
      type: 'category',
      label: 'API Reference',
      items: [
        'api-reference/agent',
        'api-reference/thread',
        'api-reference/message',
        'api-reference/attachment',
        'api-reference/thread-store'
      ],
    },
  ],
};

export default sidebars;
