/**
 * Lane D — Block-list category catalogue (per PS-003 §3.3.2).
 *
 * Seven categories with curated host glob patterns. Users opt in per
 * category and can add custom URLs. When the SW (Task D2) goes live it
 * compiles these into a deny-list at session-start time; until then the
 * UI demonstrates the contract.
 */

export interface BlockCategory {
  id: string;
  label: string;
  description: string;
  hosts: readonly string[];
}

export const BLOCK_CATEGORIES: readonly BlockCategory[] = [
  {
    id: 'social',
    label: 'Social',
    description: 'Feeds engineered to drag attention back to the device.',
    hosts: ['twitter.com', 'x.com', 'facebook.com', 'instagram.com', 'tiktok.com', 'reddit.com'],
  },
  {
    id: 'entertainment',
    label: 'Entertainment',
    description: 'Endless-scroll video + content discovery.',
    hosts: ['youtube.com', 'netflix.com', 'hulu.com', 'disneyplus.com', 'twitch.tv'],
  },
  {
    id: 'messaging',
    label: 'Messaging',
    description: 'Chat apps that pull you into asynchronous loops.',
    hosts: ['discord.com', 'slack.com', 'whatsapp.com', 'messenger.com'],
  },
  {
    id: 'shopping',
    label: 'Shopping',
    description: 'Marketplaces optimised for impulse browsing.',
    hosts: ['amazon.com', 'ebay.com', 'aliexpress.com', 'shein.com'],
  },
  {
    id: 'news',
    label: 'News',
    description: 'Refresh-rewarded news feeds.',
    hosts: ['cnn.com', 'bbc.com', 'nytimes.com', 'theguardian.com', 'foxnews.com'],
  },
  {
    id: 'games',
    label: 'Games',
    description: 'In-browser games + companion sites.',
    hosts: ['miniclip.com', 'kongregate.com', 'agar.io'],
  },
  {
    id: 'forums',
    label: 'Forums',
    description: 'Long-tail discussion sites that fragment attention.',
    hosts: ['hackernews.com', 'news.ycombinator.com', 'lobste.rs'],
  },
] as const;

export function categoryById(id: string): BlockCategory | null {
  return BLOCK_CATEGORIES.find((c) => c.id === id) ?? null;
}

export function compileBlockHosts(
  enabledIds: ReadonlySet<string>,
  customHosts: readonly string[] = []
): string[] {
  const set = new Set<string>(customHosts);
  for (const c of BLOCK_CATEGORIES) {
    if (!enabledIds.has(c.id)) continue;
    for (const h of c.hosts) set.add(h);
  }
  return Array.from(set).sort();
}
