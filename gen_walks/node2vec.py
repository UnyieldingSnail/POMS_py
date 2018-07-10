# -*- encoding:utf-8 -*-
import numpy as np
from collections import defaultdict


class Graph:
    def __init__(self, nx_G, is_directed, p, q):
        self.G = nx_G
        self.is_directed = is_directed
        self.p = p
        self.q = q
        self.sampled_edges = defaultdict(set)

    def node2vec_walk(self, walk_length, start_node):
        '''
        从指定定点执行随机游走
        '''
        G = self.G
        alias_nodes = self.alias_nodes
        alias_edges = self.alias_edges
        sampled_edges = self.sampled_edges

        walk = [start_node]
        while len(walk) < walk_length:
            cur = walk[-1]
            cur_nbrs = sorted(G.neighbors(cur))
            if len(cur_nbrs) > 0:
                if len(walk) == 1:
                    next = cur_nbrs[alias_draw(alias_nodes[cur][0], alias_nodes[cur][1])]
                    walk.append(next)
                else:
                    prev = walk[-2]
                    next = cur_nbrs[alias_draw(alias_edges[(prev, cur)][0], alias_edges[(prev, cur)][1])]
                    walk.append(next)
            else:
                break

        return walk

    def simulate_walks(self, num_walks, walk_length, start_nodes):
        '''
        对每个顶点执行随游走。
        '''
        walks = []
        # print 'Walk iteration:'
        walk_cnt = 0
        for walk_iter in range(num_walks):
            # print str(walk_iter + 1), '/', str(num_walks)
            for node in start_nodes:
                walks.append(self.node2vec_walk(walk_length=walk_length, start_node=node))
                walk_cnt += 1
                if walk_cnt % 5000 == 0:
                    print("Current walks: ", walk_cnt)
                if walk_cnt >= num_walks: break
            if walk_cnt >= num_walks: break

        return walks

    def get_alias_edge(self, src, dst):

        G = self.G
        p = self.p
        q = self.q

        unnormalized_probs = []
        for dst_nbr in sorted(G.neighbors(dst)):
            if dst_nbr == src:
                # 如果是双向关系，调整权重，有参数p影响
                unnormalized_probs.append(G[dst][dst_nbr]['weight'] / p)
            elif G.has_edge(dst_nbr, src):
                # 如果是三者关系，权重不变
                unnormalized_probs.append(G[dst][dst_nbr]['weight'])
            else:
                # 其他关系，调整权重，有参数q影响
                unnormalized_probs.append(G[dst][dst_nbr]['weight'] / q)
        norm_const = sum(unnormalized_probs)
        normalized_probs = [float(u_prob) / norm_const for u_prob in unnormalized_probs]

        return alias_setup(normalized_probs)

    def preprocess_transition_probs(self):
        '''
        用于指导随机游走的转移概率预处理。
        '''
        G = self.G
        is_directed = self.is_directed

        alias_nodes = {}
        node_cnt = 0
        for node in G.nodes():
            # 邻居的抽样概率与邻居权重成正比。
            unnormalized_probs = [G[node][nbr]['weight'] for nbr in sorted(G.neighbors(node))]
            norm_const = sum(unnormalized_probs)
            normalized_probs = [float(u_prob) / norm_const for u_prob in unnormalized_probs]
            # 用于从多项分布有效采样的预处理。
            alias_nodes[node] = alias_setup(normalized_probs)
            node_cnt += 1
            if node_cnt % 10000 == 0:
                print("Processed transitions for nodes: ", node_cnt)

        alias_edges = {}
        triads = {}

        edge_cnt = 0
        num_edges = len(G.edges())
        if is_directed:
            # 有向图
            for edge in G.edges():
                alias_edges[edge] = self.get_alias_edge(edge[0], edge[1])
                edge_cnt += 1
                if edge_cnt % 10000 == 0:
                    print("Processed transitions for edges: " + str(edge_cnt) + "/" + str(num_edges))
        else:
            # 无向图
            for edge in G.edges():
                alias_edges[edge] = self.get_alias_edge(edge[0], edge[1])
                alias_edges[(edge[1], edge[0])] = self.get_alias_edge(edge[1], edge[0])

        self.alias_nodes = alias_nodes
        self.alias_edges = alias_edges

        return


def alias_setup(probs):
    '''
    离散分布非均匀采样（别名采样法）
    '''
    K = len(probs)
    J = np.zeros(K, dtype=np.int)
    q = np.zeros(K)

    smaller = []
    larger = []
    for kk, prob in enumerate(probs):
        q[kk] = K * prob
        if q[kk] < 1.0:
            smaller.append(kk)
        else:
            larger.append(kk)

    while len(smaller) > 0 and len(larger) > 0:
        small = smaller.pop()
        large = larger.pop()

        J[small] = large
        q[large] = q[large] + q[small] - 1.0
        if q[large] < 1.0:
            smaller.append(large)
        else:
            larger.append(large)

    return J, q


def alias_draw(J, q):
    K = len(J)

    kk = int(np.floor(np.random.rand() * K))
    if np.random.rand() < q[kk]:
        return kk
    else:
        return J[kk]
