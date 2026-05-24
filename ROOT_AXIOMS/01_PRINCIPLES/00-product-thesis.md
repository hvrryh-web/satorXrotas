[Ver001.000]

# PR-00 — Product Thesis

> "Productivity and wellness are not opposing forces; they are complementary states of one neural system."

## What This Means

NJZ RAT-OS exists because the dominant pattern in the digital wellness + productivity market is **fragmentation**: users juggle 5+ apps with separate subscriptions, separate data, separate UIs. Each app optimises one cognitive state in isolation. The user pays $200-370/year for tools that don't talk to each other.

We bet on **integration**: a single platform where every action in every module feeds into a unified progression system. The whole is exponentially more engaging than the sum of its parts because progress in one mode (focus, writing, learning) materially changes the experience in another (the metaverse).

## Why This Matters For Engineering

- Cross-module state is a feature, not an accident. Domain types in `@njz-os/core` are designed for it.
- Persistence must be unified (one vaultbrain) — never let two modules invent their own store.
- The metaverse is not a "nice to have" — it's the connective tissue. PolyCo.World is privileged in architecture, not deferred.
- We do not compete with Lumosity at brain training, Endel at audio, Freedom at blocking, or Imprint at micro-learning *on their own terms*. We compete by being *the only product where they live together*.

## What This Forbids

- Standalone module roadmaps that don't account for cross-module effects.
- Per-module persistence layers.
- UI patterns that hide the metaverse instead of integrating it.
- "Pivot to standalone product" thinking. If we ship a standalone, we've lost the thesis.
