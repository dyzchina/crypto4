"""step1_mnop_probe.py — MNOP-analog dual counting on 20 clean multi-coin clusters."""
from __future__ import annotations
import pandas as pd, numpy as np, itertools
from collections import Counter
from scipy.stats import binomtest

# Coin subsystem lattice (Pardon-style: each coin = subsystem alpha = (C, O, R, reflexive))
COIN_SUBSYSTEM = {
    'usd-coin':             {'C':'fiat',        'O':'multi',   'R':'open', 'reflexive':False},
    'tether':               {'C':'fiat',        'O':'multi',   'R':'open', 'reflexive':False},
    'true-usd':             {'C':'fiat',        'O':'multi',   'R':'open', 'reflexive':False},
    'binance-usd':          {'C':'fiat',        'O':'multi',   'R':'open', 'reflexive':False},
    'first-digital-usd':    {'C':'fiat',        'O':'multi',   'R':'open', 'reflexive':False},
    'paxos-standard':       {'C':'fiat',        'O':'multi',   'R':'open', 'reflexive':False},
    'gemini-dollar':        {'C':'fiat',        'O':'multi',   'R':'open', 'reflexive':False},
    'euro-coin':            {'C':'fiat_eur',    'O':'multi',   'R':'open', 'reflexive':False},
    'stasis-eurs':          {'C':'fiat_eur',    'O':'multi',   'R':'open', 'reflexive':False},
    'dai':                  {'C':'crypto',      'O':'onchain', 'R':'psm',  'reflexive':False},
    'liquity-usd':          {'C':'crypto_eth',  'O':'onchain', 'R':'open', 'reflexive':False},
    'magic-internet-money': {'C':'crypto',      'O':'onchain', 'R':'open', 'reflexive':True },
    'usdd':                 {'C':'crypto',      'O':'onchain', 'R':'open', 'reflexive':True },
    'gho':                  {'C':'crypto',      'O':'onchain', 'R':'psm',  'reflexive':False},
    'crvusd':               {'C':'crypto',      'O':'onchain', 'R':'open', 'reflexive':False},
    'frax':                 {'C':'hybrid',      'O':'onchain', 'R':'open', 'reflexive':True },
    'vai':                  {'C':'crypto',      'O':'onchain', 'R':'open', 'reflexive':True },
    'fei-usd':              {'C':'crypto',      'O':'onchain', 'R':'open', 'reflexive':True },
    'terrausd':             {'C':'algo',        'O':'onchain', 'R':'open', 'reflexive':True },
    'husd':                 {'C':'fiat',        'O':'multi',   'R':'open', 'reflexive':False},
    'ethena-usde':          {'C':'delta_neutral','O':'onchain','R':'open', 'reflexive':False},
}

def shared_attribute(coins):
    """Return the multiset of subsystem attributes shared by ALL coins in the block."""
    subs = [COIN_SUBSYSTEM.get(c, {}) for c in coins]
    if not subs:
        return 'empty'
    shared = []
    for attr in ('C','O','R','reflexive'):
        vals = set(s.get(attr) for s in subs)
        if len(vals) == 1:
            shared.append(f'{attr}={list(vals)[0]}')
    return '|'.join(shared) if shared else 'no_shared_attr'


def main():
    clusters = pd.read_csv('data/clusters_clean.csv')
    clusters['coin_list'] = clusters['coins'].str.split('+')
    clusters['shared'] = clusters['coin_list'].apply(shared_attribute)

    # === Method 1: observed distribution ===
    obs_dist = Counter(clusters['shared'])
    N = sum(obs_dist.values())
    print(f'=== Method 1: OBSERVED sharing distribution (n={N} clean clusters) ===')
    for k, v in sorted(obs_dist.items(), key=lambda x: -x[1]):
        print(f'  {v:3d} ({v/N*100:5.1f}%)  {k}')

    obs_shared = N - obs_dist.get('no_shared_attr', 0)
    print(f'\n  clusters sharing >=1 attribute:  {obs_shared}/{N} = {obs_shared/N*100:.1f}%')

    # === Method 2: random-pair null ===
    coins_list = list(COIN_SUBSYSTEM.keys())
    n_pairs = 0
    null_shared = 0
    null_dist = Counter()
    for c1, c2 in itertools.combinations(coins_list, 2):
        n_pairs += 1
        k = shared_attribute([c1, c2])
        null_dist[k] += 1
        if k != 'no_shared_attr':
            null_shared += 1
    p_null = null_shared / n_pairs
    print(f'\n=== Method 2: RANDOM-PAIR NULL ({n_pairs} pairs) ===')
    print(f'  P(random pair shares >=1 attribute) = {p_null:.3f}')
    for k, v in sorted(null_dist.items(), key=lambda x: -x[1])[:8]:
        print(f'  {v:3d} ({v/n_pairs*100:5.1f}%)  {k}')

    # === MNOP-analog: binomial test ===
    print(f'\n=== MNOP-analog test: is cluster-sharing beyond random? ===')
    res = binomtest(obs_shared, N, p=p_null, alternative='greater')
    print(f'  H0: cluster block-sharing frequency = random-pair sharing frequency ({p_null:.3f})')
    print(f'  Observed: {obs_shared}/{N} ({obs_shared/N*100:.1f}%)')
    print(f'  One-sided binomial p = {res.pvalue:.6f}')

    # === Attribute-level dual counting ===
    print(f'\n=== Attribute-level dual counting (which attribute drives clustering?) ===')
    # For each single attribute, count how many observed clusters share it,
    # vs. null probability.
    attr_labels = ['C','O','R','reflexive']
    for attr in attr_labels:
        # Method 1: fraction of observed clusters sharing this attribute
        obs_share_attr = 0
        for _, row in clusters.iterrows():
            subs = [COIN_SUBSYSTEM.get(c, {}) for c in row['coin_list']]
            if len(set(s.get(attr) for s in subs)) == 1:
                obs_share_attr += 1
        # Method 2: null probability
        null_share_attr = 0
        for c1, c2 in itertools.combinations(coins_list, 2):
            if COIN_SUBSYSTEM[c1][attr] == COIN_SUBSYSTEM[c2][attr]:
                null_share_attr += 1
        p_null_attr = null_share_attr / n_pairs
        res_attr = binomtest(obs_share_attr, N, p=p_null_attr, alternative='greater')
        print(f'  attr={attr:12s}  observed {obs_share_attr}/{N} ({obs_share_attr/N*100:5.1f}%)  '
              f'null {p_null_attr*100:5.1f}%  p = {res_attr.pvalue:.4f}')

    # === Per-cluster detail (audit trail) ===
    clusters.to_csv('data/mnop_probe_clusters.csv', index=False)
    print(f'\nsaved per-cluster shared-attribute audit -> data/mnop_probe_clusters.csv')


if __name__ == '__main__':
    main()
