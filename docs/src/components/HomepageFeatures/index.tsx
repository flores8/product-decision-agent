import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Powerful LLM integration',
    description: (
      <>
        Built-in support for 100+ LLM providers through LiteLLM, making it easy to integrate with your preferred language model.
      </>
    ),
  },
  {
    title: 'Custom tools',
    description: (
      <>
        Add custom capabilities with tools or connect with services like Slack and Notion out of the box.  Leverage async support for high performance.
      </>
    ),
  },
  {
    title: 'Persistent storage & file handling',
    description: (
      <>
        Choose between in-memory, SQLite, or PostgreSQL storage for threads. Process and store files with automatic content extraction.
      </>
    ),
  },
];

function Feature({title, description}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className={clsx('text--center padding-horiz--md', styles.featureItem)}>
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
