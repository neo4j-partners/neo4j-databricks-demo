---
marp: true
theme: default
paginate: true
---

<style>
section {
  font-size: 22px;
}
h1 { font-size: 36px; }
h2 { font-size: 28px; }
code { font-size: 18px; }
table { font-size: 20px; }
</style>

# Neo4j Graph Data Science (GDS)
## Algorithms and Analytics on Graph Data

---

## What is Graph Data Science?

**GDS** is Neo4j's library for running graph algorithms at scale.

**Why use GDS?**
- Run 65+ production-quality graph algorithms
- Optimized for performance with in-memory graph projections
- Scales to billions of nodes and relationships
- Integrates with machine learning pipelines

**Common use cases:**
- Fraud detection (community detection, centrality)
- Recommendations (similarity, node embeddings)
- Network analysis (path finding, influence scoring)
- Knowledge graphs (link prediction, entity resolution)

---

## GDS Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  1. Project Graph    →  Create in-memory graph projection   │
│  2. Run Algorithms   →  Execute algorithms on projection    │
│  3. Use Results      →  Stream, mutate, or write back       │
│  4. Drop Projection  →  Clean up memory when done           │
└─────────────────────────────────────────────────────────────┘
```

**Key concept:** Algorithms run on **projections**, not the live database.

This allows:
- Filtering to relevant subgraphs
- Adding computed properties
- Running multiple algorithms without affecting stored data

---

## Creating a Graph Projection

Project a subgraph into memory for algorithm execution:

```cypher
CALL gds.graph.project(
  'investment-graph',           // projection name
  ['Customer', 'Stock'],        // node labels to include
  ['HOLDS']                     // relationship types to include
)
```

**What it creates:** An in-memory copy of matching nodes and relationships.

Check existing projections:
```cypher
CALL gds.graph.list()
```

Drop a projection when done:
```cypher
CALL gds.graph.drop('investment-graph')
```

---

## Projection with Properties

Include node and relationship properties:

```cypher
CALL gds.graph.project(
  'weighted-graph',
  {
    Customer: { properties: ['risk_tolerance'] },
    Stock: { properties: ['price', 'market_cap'] }
  },
  {
    HOLDS: { properties: ['shares'] }
  }
)
```

**Why include properties?**
- Use as algorithm weights (e.g., weighted PageRank)
- Filter results based on node attributes
- Calculate weighted similarity scores

---

## Algorithm Execution Modes

GDS algorithms support four execution modes:

| Mode | Description | Use Case |
|------|-------------|----------|
| **stream** | Returns results as a stream | Ad-hoc analysis, exploration |
| **stats** | Returns summary statistics | Quick overview of results |
| **mutate** | Adds results to projection | Chain multiple algorithms |
| **write** | Writes results to database | Persist for queries |

**Example pattern:**
```cypher
CALL gds.pageRank.stream('my-graph')    // stream mode
CALL gds.pageRank.stats('my-graph')     // stats mode
CALL gds.pageRank.mutate('my-graph', {mutateProperty: 'pr'})
CALL gds.pageRank.write('my-graph', {writeProperty: 'pagerank'})
```

---

## Centrality: PageRank

**PageRank** measures node importance based on incoming connections.

```cypher
CALL gds.pageRank.stream('investment-graph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS name, score
ORDER BY score DESC
LIMIT 10
```

**What it measures:** Which nodes are most "influential" — connected to by other well-connected nodes.

**Use cases:**
- Find key customers in a network
- Identify important stocks (held by many portfolios)
- Rank influential entities

---

## Centrality: Degree Centrality

**Degree centrality** counts direct connections.

```cypher
CALL gds.degree.stream('investment-graph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).ticker AS stock, score AS holders
ORDER BY score DESC
LIMIT 5
```

**What it measures:** Simple connection count — how many relationships a node has.

| Stock | Holders |
|-------|---------|
| TCOR | 45 |
| SMTC | 38 |
| ECOP | 32 |

**Use case:** Find the most widely held stocks, most connected customers.

---

## Centrality: Betweenness

**Betweenness centrality** identifies bridge nodes.

```cypher
CALL gds.betweenness.stream('investment-graph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS entity, score
ORDER BY score DESC
LIMIT 10
```

**What it measures:** How often a node lies on shortest paths between others.

**Use cases:**
- Find brokers or intermediaries
- Identify single points of failure
- Detect gatekeepers in information flow

High betweenness = node connects otherwise disconnected parts of the graph.

---

## Community Detection: Louvain

**Louvain** finds communities by optimizing modularity.

```cypher
CALL gds.louvain.stream('investment-graph')
YIELD nodeId, communityId
RETURN communityId, collect(gds.util.asNode(nodeId).name) AS members
ORDER BY size(members) DESC
```

**What it finds:** Groups of densely connected nodes.

**Use cases:**
- Segment customers by investment behavior
- Find clusters of related stocks
- Detect fraud rings

---

## Community Detection: Label Propagation

**Label Propagation** is a fast community detection algorithm.

```cypher
CALL gds.labelPropagation.stream('investment-graph')
YIELD nodeId, communityId
RETURN communityId, count(*) AS size
ORDER BY size DESC
```

**How it works:** Nodes adopt the most common label among neighbors, iteratively.

**Comparison to Louvain:**
| Algorithm | Speed | Quality | Deterministic |
|-----------|-------|---------|---------------|
| Louvain | Slower | Higher | No |
| Label Propagation | Faster | Good | No |

Use Label Propagation for quick exploration, Louvain for final analysis.

---

## Similarity: Node Similarity

**Node Similarity** finds nodes with similar connection patterns.

```cypher
CALL gds.nodeSimilarity.stream('investment-graph')
YIELD node1, node2, similarity
RETURN gds.util.asNode(node1).name AS customer1,
       gds.util.asNode(node2).name AS customer2,
       similarity
ORDER BY similarity DESC
LIMIT 10
```

**What it measures:** Jaccard similarity based on shared neighbors.

**Use cases:**
- Find customers with similar portfolios
- Recommend stocks based on similar investors
- Identify potential duplicates

---

## Similarity: K-Nearest Neighbors (KNN)

**KNN** finds the k most similar nodes based on properties.

```cypher
CALL gds.knn.stream('investment-graph', {
  nodeProperties: ['risk_score', 'portfolio_value'],
  topK: 5
})
YIELD node1, node2, similarity
RETURN gds.util.asNode(node1).name AS customer,
       gds.util.asNode(node2).name AS similar_customer,
       similarity
```

**What it measures:** Similarity based on node property vectors.

**Use cases:**
- Find similar customers for recommendations
- Identify peer groups
- Cluster customers by attributes

---

## Path Finding: Shortest Path

**Dijkstra** finds the shortest weighted path between nodes.

```cypher
MATCH (source:Customer {name: 'James Anderson'})
MATCH (target:Stock {ticker: 'ECOP'})
CALL gds.shortestPath.dijkstra.stream('investment-graph', {
  sourceNode: source,
  targetNode: target
})
YIELD path
RETURN path
```

**What it finds:** The path with minimum total weight.

**Use cases:**
- Find connection paths between entities
- Calculate degrees of separation
- Trace transaction flows

---

## Path Finding: All Shortest Paths

Find all shortest paths of equal length:

```cypher
MATCH (source:Customer {name: 'James Anderson'})
MATCH (target:Sector {name: 'Renewable Energy'})
CALL gds.allShortestPaths.dijkstra.stream('investment-graph', {
  sourceNode: source,
  targetNode: target
})
YIELD path
RETURN [node IN nodes(path) | labels(node)[0]] AS path_labels
```

**Returns:** All paths that tie for shortest.

Useful when multiple equivalent routes exist.

---

## Node Embeddings: FastRP

**FastRP** generates vector embeddings for nodes.

```cypher
CALL gds.fastRP.stream('investment-graph', {
  embeddingDimension: 128,
  iterationWeights: [0.8, 1.0, 1.0]
})
YIELD nodeId, embedding
RETURN gds.util.asNode(nodeId).name AS name, embedding
LIMIT 5
```

**What it creates:** Dense vector representations capturing graph structure.

**Use cases:**
- Input features for ML models
- Similarity search via vector distance
- Cluster visualization (after dimensionality reduction)

---

## Writing Results Back

Persist algorithm results to the database:

```cypher
CALL gds.pageRank.write('investment-graph', {
  writeProperty: 'pagerank'
})
YIELD nodePropertiesWritten
```

Now query using the computed property:

```cypher
MATCH (c:Customer)
WHERE c.pagerank > 0.5
RETURN c.name, c.pagerank
ORDER BY c.pagerank DESC
```

**When to write:**
- Results needed for application queries
- Visualization tools need the data
- Sharing results with downstream systems

---

## Chaining Algorithms with Mutate

Run multiple algorithms on the same projection:

```cypher
// Step 1: Create projection
CALL gds.graph.project('analysis', ['Customer', 'Stock'], ['HOLDS'])

// Step 2: Add PageRank to projection
CALL gds.pageRank.mutate('analysis', {mutateProperty: 'pr'})

// Step 3: Add community to projection
CALL gds.louvain.mutate('analysis', {mutateProperty: 'community'})

// Step 4: Stream combined results
CALL gds.graph.nodeProperties.stream('analysis', ['pr', 'community'])
YIELD nodeId, propertyValue
RETURN gds.util.asNode(nodeId).name, propertyValue
```

**Benefit:** Run multiple algorithms without repeated projection.

---

## Centrality: Closeness

**Closeness centrality** measures how close a node is to all others.

```cypher
CALL gds.closeness.stream('investment-graph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS name, score
ORDER BY score DESC
LIMIT 10
```

**What it measures:** Average shortest path distance to all other nodes (inverted).

**Interpretation:**
- High closeness = can reach all nodes quickly
- Low closeness = on the periphery of the network

**Use cases:**
- Find nodes that can spread information fastest
- Identify central hubs for distribution
- Locate optimal service locations

---

## Centrality: Eigenvector

**Eigenvector centrality** measures influence based on neighbor importance.

```cypher
CALL gds.eigenvector.stream('investment-graph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS name, score
ORDER BY score DESC
LIMIT 10
```

**What it measures:** A node is important if connected to other important nodes.

**Comparison to PageRank:**
| Algorithm | Damping | Convergence | Use Case |
|-----------|---------|-------------|----------|
| PageRank | Yes (0.85) | Always | Web ranking, general |
| Eigenvector | No | May not converge | Tight-knit networks |

**Use case:** Social influence, prestige in citation networks.

---

## Centrality: ArticleRank

**ArticleRank** is a PageRank variant that reduces bias toward low-degree nodes.

```cypher
CALL gds.articleRank.stream('investment-graph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS name, score
ORDER BY score DESC
LIMIT 10
```

**How it differs:** Distributes rank more evenly, accounting for average degree.

**When to use:**
- When PageRank over-emphasizes nodes with few but important connections
- Academic citation networks
- Graphs where low-degree nodes shouldn't rank too high

---

## Community: Weakly Connected Components (WCC)

**WCC** finds disconnected subgraphs (islands) in the data.

```cypher
CALL gds.wcc.stream('investment-graph')
YIELD nodeId, componentId
RETURN componentId, count(*) AS size
ORDER BY size DESC
```

**What it finds:** Groups of nodes that can reach each other (ignoring direction).

| Component | Size | Description |
|-----------|------|-------------|
| 0 | 45,230 | Main connected graph |
| 1 | 15 | Isolated customer group |
| 2 | 3 | Data quality issue |

**Use cases:**
- Data quality checks (why are nodes disconnected?)
- Find isolated subgraphs for separate analysis
- Pre-processing before other algorithms

---

## Community: Strongly Connected Components (SCC)

**SCC** finds components where all nodes can reach each other following direction.

```cypher
CALL gds.scc.stream('directed-graph')
YIELD nodeId, componentId
RETURN componentId, count(*) AS size
ORDER BY size DESC
```

**Difference from WCC:**
```
WCC: A -- B -- C  (all connected, ignoring arrows)
SCC: A -> B -> C  (only connected if paths go both ways)
```

**Use cases:**
- Analyze directed networks (transactions, citations)
- Find circular dependencies
- Identify feedback loops

---

## Community: Triangle Count

**Triangle Count** counts triangles each node participates in.

```cypher
CALL gds.triangleCount.stream('investment-graph')
YIELD nodeId, triangleCount
RETURN gds.util.asNode(nodeId).name AS name, triangleCount
ORDER BY triangleCount DESC
LIMIT 10
```

**What it measures:** How many closed triads include this node.

```
Triangle: A -- B
           \  /
            C
```

**Use cases:**
- Measure network cohesion
- Identify tightly-knit groups
- Fraud detection (fraudsters often form triangles)

---

## Community: Local Clustering Coefficient

**Local Clustering Coefficient** measures how connected a node's neighbors are.

```cypher
CALL gds.localClusteringCoefficient.stream('investment-graph')
YIELD nodeId, localClusteringCoefficient
RETURN gds.util.asNode(nodeId).name AS name,
       localClusteringCoefficient AS clustering
ORDER BY clustering DESC
LIMIT 10
```

**What it measures:** Ratio of actual triangles to possible triangles.

**Interpretation:**
- 1.0 = all neighbors connected to each other
- 0.0 = no neighbors connected to each other

**Use cases:**
- Identify brokers (low clustering, high betweenness)
- Find clique-like structures
- Network topology analysis

---

## Path Finding: A* Shortest Path

**A*** finds shortest paths using a heuristic for better performance.

```cypher
MATCH (source:Location {name: 'New York'})
MATCH (target:Location {name: 'Los Angeles'})
CALL gds.shortestPath.astar.stream('locations-graph', {
  sourceNode: source,
  targetNode: target,
  latitudeProperty: 'latitude',
  longitudeProperty: 'longitude'
})
YIELD path, totalCost
RETURN totalCost, [n IN nodes(path) | n.name] AS route
```

**How it differs from Dijkstra:**
- Uses geographic coordinates as heuristic
- Faster for spatial/geographic graphs
- Requires latitude/longitude properties

**Use case:** Route planning, geographic networks.

---

## Path Finding: Yen's K-Shortest Paths

**Yen's algorithm** finds multiple alternative shortest paths.

```cypher
MATCH (source:Customer {name: 'James Anderson'})
MATCH (target:Sector {name: 'Healthcare'})
CALL gds.shortestPath.yens.stream('investment-graph', {
  sourceNode: source,
  targetNode: target,
  k: 3
})
YIELD index, path, totalCost
RETURN index, totalCost, [n IN nodes(path) | labels(n)[0]] AS route
```

**What it returns:** The k shortest paths, not just the single best.

| Index | Cost | Route |
|-------|------|-------|
| 0 | 2 | Customer → Stock → Sector |
| 1 | 3 | Customer → Account → Stock → Sector |
| 2 | 4 | Customer → Stock → Stock → Sector |

**Use case:** Alternative routes, redundancy analysis.

---

## Path Finding: Single Source Shortest Path

**SSSP** finds shortest paths from one node to ALL other nodes.

```cypher
MATCH (source:Customer {name: 'James Anderson'})
CALL gds.allShortestPaths.dijkstra.stream('investment-graph', {
  sourceNode: source
})
YIELD targetNodeId, totalCost, path
RETURN gds.util.asNode(targetNodeId).name AS target,
       totalCost AS distance
ORDER BY distance
LIMIT 20
```

**What it computes:** Distance from source to every reachable node.

**Use cases:**
- Network reach analysis
- Find all nodes within N hops
- Calculate average path length from a node

---

## Path Finding: Breadth-First Search (BFS)

**BFS** explores the graph level by level from a source.

```cypher
MATCH (source:Customer {name: 'James Anderson'})
CALL gds.bfs.stream('investment-graph', {
  sourceNode: source,
  maxDepth: 3
})
YIELD path
RETURN [n IN nodes(path) | n.name] AS traversal
LIMIT 10
```

**How it works:** Visits all nodes at distance 1, then distance 2, etc.

**Use cases:**
- Find all nodes within N hops
- Level-based exploration
- Shortest unweighted paths

---

## Path Finding: Depth-First Search (DFS)

**DFS** explores as deep as possible before backtracking.

```cypher
MATCH (source:Customer {name: 'James Anderson'})
CALL gds.dfs.stream('investment-graph', {
  sourceNode: source,
  maxDepth: 5
})
YIELD path
RETURN [n IN nodes(path) | n.name] AS traversal
LIMIT 10
```

**Comparison:**
| Algorithm | Exploration | Memory | Use Case |
|-----------|-------------|--------|----------|
| BFS | Level by level | Higher | Shortest paths |
| DFS | Deep first | Lower | Connectivity, cycles |

---

## Embeddings: Node2Vec

**Node2Vec** creates embeddings using biased random walks.

```cypher
CALL gds.node2vec.stream('investment-graph', {
  embeddingDimension: 64,
  walkLength: 80,
  walksPerNode: 10,
  returnFactor: 1.0,
  inOutFactor: 1.0
})
YIELD nodeId, embedding
RETURN gds.util.asNode(nodeId).name AS name, embedding
LIMIT 5
```

**Parameters:**
- `returnFactor` (p): Likelihood to return to previous node
- `inOutFactor` (q): Inward vs outward exploration bias

**Use cases:**
- Capture both local structure (high p) and global structure (high q)
- Link prediction features
- Node classification

---

## Embeddings: GraphSAGE

**GraphSAGE** learns embeddings by aggregating neighbor features.

```cypher
CALL gds.beta.graphSage.stream('investment-graph', {
  modelName: 'customer-embeddings',
  featureProperties: ['risk_score', 'tenure', 'portfolio_value']
})
YIELD nodeId, embedding
RETURN gds.util.asNode(nodeId).name AS name, embedding
LIMIT 5
```

**How it differs:**
| Algorithm | Input | Inductive |
|-----------|-------|-----------|
| FastRP | Structure only | No |
| Node2Vec | Structure only | No |
| GraphSAGE | Structure + Features | Yes |

**Use case:** When node properties are important, new nodes need embeddings.

---

## Embeddings: HashGNN

**HashGNN** creates embeddings using efficient hashing.

```cypher
CALL gds.hashgnn.stream('investment-graph', {
  featureProperties: ['risk_score'],
  embeddingDensity: 128,
  iterations: 3
})
YIELD nodeId, embedding
RETURN gds.util.asNode(nodeId).name AS name, embedding
LIMIT 5
```

**Advantages:**
- Very fast computation
- Low memory usage
- Good for large graphs

**Trade-off:** Less expressive than neural approaches like GraphSAGE.

---

## Link Prediction: Common Neighbors

**Common Neighbors** predicts links based on shared connections.

```cypher
MATCH (a:Customer {name: 'James Anderson'})
MATCH (b:Customer) WHERE a <> b
CALL gds.linkprediction.commonNeighbors.stream({
  node1: a,
  node2: b
})
YIELD score
RETURN b.name AS candidate, score
ORDER BY score DESC
LIMIT 5
```

**Intuition:** Two nodes sharing many neighbors are likely to connect.

**Score:** Count of shared neighbors.

---

## Link Prediction: Adamic-Adar

**Adamic-Adar** weights common neighbors by their rarity.

```cypher
MATCH (a:Customer {name: 'James Anderson'})
MATCH (b:Customer) WHERE a <> b
CALL gds.linkprediction.adamicAdar.stream({
  node1: a,
  node2: b
})
YIELD score
RETURN b.name AS candidate, score
ORDER BY score DESC
LIMIT 5
```

**Formula:** Sum of 1/log(degree) for each common neighbor.

**Intuition:** Shared rare neighbors are more significant than shared popular ones.

---

## Link Prediction: Preferential Attachment

**Preferential Attachment** predicts links between high-degree nodes.

```cypher
MATCH (a:Customer {name: 'James Anderson'})
MATCH (b:Customer) WHERE a <> b
CALL gds.linkprediction.preferentialAttachment.stream({
  node1: a,
  node2: b
})
YIELD score
RETURN b.name AS candidate, score
ORDER BY score DESC
LIMIT 5
```

**Formula:** degree(a) × degree(b)

**Intuition:** Well-connected nodes tend to form new connections (rich get richer).

---

## Link Prediction: Total Neighbors

**Total Neighbors** uses the union of neighbors.

```cypher
MATCH (a:Customer {name: 'James Anderson'})
MATCH (b:Customer) WHERE a <> b
CALL gds.linkprediction.totalNeighbors.stream({
  node1: a,
  node2: b
})
YIELD score
RETURN b.name AS candidate, score
ORDER BY score DESC
LIMIT 5
```

**Formula:** |neighbors(a) ∪ neighbors(b)|

**Use case:** When network reach matters more than overlap.

---

## Link Prediction Pipeline

Build a complete link prediction ML pipeline:

```cypher
// 1. Create pipeline
CALL gds.beta.pipeline.linkPrediction.create('lp-pipeline')

// 2. Add node properties as features
CALL gds.beta.pipeline.linkPrediction.addNodeProperty('lp-pipeline', 'fastRP', {
  embeddingDimension: 64,
  mutateProperty: 'embedding'
})

// 3. Add link features
CALL gds.beta.pipeline.linkPrediction.addFeature('lp-pipeline', 'hadamard', {
  nodeProperties: ['embedding']
})

// 4. Configure model
CALL gds.beta.pipeline.linkPrediction.configureSplit('lp-pipeline', {
  testFraction: 0.2,
  trainFraction: 0.8
})

// 5. Train
CALL gds.beta.pipeline.linkPrediction.train('investment-graph', {
  pipeline: 'lp-pipeline',
  modelName: 'lp-model',
  targetRelationshipType: 'WILL_CONNECT'
})
```

---

## Algorithm Summary

| Category | Algorithms | Purpose |
|----------|------------|---------|
| **Centrality** | PageRank, Degree, Betweenness, Closeness, Eigenvector, ArticleRank | Find important nodes |
| **Community** | Louvain, Label Propagation, WCC, SCC, Triangle Count, Clustering Coefficient | Find clusters |
| **Similarity** | Node Similarity, KNN | Find similar nodes |
| **Path Finding** | Dijkstra, A*, Yen's K, BFS, DFS, SSSP | Find routes |
| **Embeddings** | FastRP, Node2Vec, GraphSAGE, HashGNN | Create ML features |
| **Link Prediction** | Common Neighbors, Adamic-Adar, Preferential Attachment, Total Neighbors | Predict new edges |

**Full catalog:** 65+ algorithms in production GDS library.

---

## Best Practices

**Memory Management:**
- Estimate memory before projecting: `gds.graph.project.estimate()`
- Drop projections when done
- Use native projections for best performance

**Performance:**
- Start with smaller subgraphs for exploration
- Use `stats` mode to check algorithm behavior
- Set appropriate concurrency for your hardware

**Production:**
- Write results for frequently-needed scores
- Cache projections for repeated analysis
- Monitor memory usage in GDS catalog

---

## Example: Customer Segmentation Pipeline

```cypher
// 1. Project customer-stock relationships
CALL gds.graph.project('customers',
  ['Customer', 'Stock'],
  {HOLDS: {properties: 'shares'}})

// 2. Find customer communities
CALL gds.louvain.write('customers', {writeProperty: 'segment'})

// 3. Calculate influence within segments
CALL gds.pageRank.write('customers', {writeProperty: 'influence'})

// 4. Query segmented customers
MATCH (c:Customer)
RETURN c.segment, count(*) AS size, avg(c.influence) AS avg_influence
ORDER BY avg_influence DESC

// 5. Clean up
CALL gds.graph.drop('customers')
```
