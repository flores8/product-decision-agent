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
    'quickstart',
    'how-it-works',
    'configuration',
    'chat-with-tyler',
    'core-concepts',
    {
      type: 'category',
      label: 'Tools',
      items: [
        'tools/overview',
        'tools/custom-tools',
        'tools/web',
        'tools/slack',
        'tools/notion',
        'tools/image',
        'tools/command-line',
      ],
    },
    {
      type: 'category',
      label: 'Examples',
      items: [
        'examples/index',
        'examples/using-tools',
        'examples/tools-streaming',
        'examples/streaming',
        'examples/database-storage',
        'examples/file-storage',
        'examples/message-attachments',
        'examples/interrupt-tools',
        'examples/full-configuration',
      ],
    },
  ],

  // API Reference sidebar
  apiSidebar: [
    {
      type: 'category',
      label: 'API reference',
      items: [
        'api-reference/index',
        'api-reference/agent',
        'api-reference/thread',
        'api-reference/message',
        'api-reference/attachment',
        'api-reference/thread-store',
        'api-reference/tools',
      ],
    },
  ],
};

export default sidebars;
