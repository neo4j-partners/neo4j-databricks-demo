# Background Concepts: Understanding Agent-Augmented Knowledge Graphs

## Introduction

This document provides foundational background on the key technologies and concepts used in the [Agent-Augmented Knowledge Graphs](GRAPH_AUGMENTATION.md) blog post. If you're new to Databricks lakehouse architecture, AI agents, knowledge graphs, or Neo4j Graph Data Science, this guide will help you understand these technologies before diving into how they work together to create intelligent, continuously-enriched data systems.

We recommend reading this document first if you're unfamiliar with any of these concepts, then proceeding to the main blog post to see how they integrate into a powerful pattern for bridging structured and unstructured data.

## Databricks Lakehouse Architecture

The Databricks Lakehouse represents a fundamental shift in enterprise data architecture, combining the best aspects of data lakes and data warehouses into a unified platform. Unlike traditional approaches where organizations maintained separate systems for raw data storage (data lakes) and structured analytics (data warehouses), the lakehouse provides a single platform that handles both with equal effectiveness.

At its core, a lakehouse stores data in open, cloud-based object storage using formats like Parquet, making it cost-effective and scalable like a data lake. However, it adds a sophisticated transaction layer on top of this storage that provides data warehouse capabilities: ACID transactions, schema enforcement, time travel, and efficient query processing. This means you can run both large-scale machine learning workloads and business intelligence queries against the same data, without duplicating it or maintaining separate systems.

Two key technologies enable this architecture. **Delta Lake** provides the transaction layer that turns raw object storage into a reliable database system. It handles concurrent reads and writes, ensures data consistency, and enables versioning so you can query historical snapshots of your data. **Unity Catalog** serves as the unified governance layer, providing a single place to manage permissions, discover datasets, and track data lineage across the entire lakehouse. It catalogs tables, files, machine learning models, and even unstructured documents in volumes, making all organizational data discoverable and accessible with proper governance.

The lakehouse architecture excels at handling both structured and unstructured data because it doesn't force everything into tables. Structured data lives in Delta Lake tables with schemas, perfect for SQL queries and analytics. Unstructured data—documents, images, audio files, PDFs—lives in Unity Catalog volumes as files, accessible to AI systems for analysis. This dual capability makes lakehouses ideal for modern AI applications that need to combine insights from transactional data with context from documents, creating a foundation for the agent-augmented knowledge graph pattern.

## Databricks AI Agents

Databricks AI agents represent specialized artificial intelligence systems designed to interact with enterprise data and answer natural language questions. Rather than requiring users to write SQL queries or code, agents understand business questions posed in plain English and automatically determine how to retrieve and analyze the relevant data. Each agent type specializes in different data modalities and query patterns.

### Genie Agent

The **Genie Agent** focuses on structured data residing in lakehouse tables. When you ask Genie a question like "Which customers have investment accounts with balances exceeding ten thousand dollars?", it analyzes the natural language, understands the intent, examines the schema of available tables in Unity Catalog, and automatically generates the appropriate SQL query. It executes this query against Delta Lake tables and returns results in a conversational format. Genie excels at quantitative analysis—aggregations, filtering, joins, and calculations across structured records. It understands business terminology, can interpret complex questions involving multiple tables, and handles temporal queries like "show me trends over the last quarter." The agent learns from table metadata, column descriptions, and sample queries to improve its SQL generation accuracy over time.

### Knowledge Assistant Agent

The **Knowledge Assistant Agent** specializes in unstructured data stored in Unity Catalog volumes. Unlike Genie's focus on tables with rows and columns, the Knowledge Assistant reads documents, PDFs, text files, and other free-form content to extract semantic meaning and answer questions about narrative information. When you ask "What investment interests has Maria Rodriguez expressed in her profile that are not reflected in her current portfolio?", the Knowledge Assistant searches relevant documents, uses natural language understanding to extract key information about Maria's stated preferences, and synthesizes an answer based on document content.

This agent employs vector search and semantic understanding to find relevant passages across large document collections. It can identify themes, extract entities, compare information across multiple documents, and surface insights that would require a human analyst to read through hundreds of pages. The Knowledge Assistant bridges the gap between the unstructured narrative context that humans naturally produce—customer profiles, research reports, meeting notes—and the structured queries that traditional databases handle.

### Multi-Agent Orchestration

The real power emerges when multiple agents work together through **Multi-Agent Orchestration**. A supervisor agent coordinates between specialized agents, understanding when to invoke each one and how to synthesize their responses. Consider the question: "Find customers interested in renewable energy stocks and show me their current holdings." This requires two distinct operations: identifying customers who mentioned renewable energy interests in profile documents (Knowledge Assistant's domain) and retrieving their actual portfolio holdings from structured tables (Genie's domain).

The Multi-Agent Supervisor recognizes this complexity, breaks the question into subtasks, routes each subtask to the appropriate agent, and combines the results into a coherent answer. This orchestration follows a supervisor pattern where the coordinating agent has visibility into the capabilities of each subordinate agent and can plan multi-step workflows. The supervisor might first ask the Knowledge Assistant to extract a list of customer IDs who mentioned renewable energy, then pass those IDs to Genie to query their holdings, and finally synthesize both results to identify gaps between interests and actual investments.

This orchestration enables a new class of analytics that spans the structured-unstructured divide. Organizations can ask questions that require both database precision and document comprehension, getting answers that would have previously required manual coordination between business analysts and data scientists.

## Knowledge Graphs

A knowledge graph is a structured representation of information that models entities and the relationships between them as a network of nodes and edges. Unlike traditional databases that store information in rows and columns, knowledge graphs capture the semantic connections that make data meaningful. This graph structure mirrors how humans naturally think about interconnected information—customers know banks, accounts hold positions, stocks represent companies—making the data model intuitive and the relationships queryable.

### Nodes: Entities in the Graph

**Nodes** represent the entities in your domain—the "things" that matter to your business. In a retail investment platform, nodes include customers (representing individual investors), accounts (representing financial accounts), banks (representing financial institutions), stocks (representing tradable securities), companies (representing corporations that issue stocks), positions (representing portfolio holdings), and transactions (representing money movements). Each node has a label indicating its type and properties that store attributes specific to that entity. A Customer node might have properties like firstName, lastName, email, annualIncome, and riskProfile. A Stock node might have ticker, currentPrice, and sector properties.

Nodes serve as the anchors of knowledge in the graph. They represent the concrete entities you want to track, analyze, and understand. When you query a knowledge graph, you're typically starting from nodes that match certain criteria—finding all Customer nodes with high income, or all Stock nodes in the technology sector—and then traversing relationships to discover connected information.

### Edges: Relationships Between Entities

**Edges** (also called relationships) connect nodes and represent meaningful associations between entities. These relationships are first-class citizens in a graph database, not mere join keys as in relational databases. Each edge has a type that expresses its semantic meaning: HAS_ACCOUNT connects a Customer to an Account they own, AT_BANK connects an Account to the Bank where it's held, HOLDS_POSITION connects an Account to a Position in its portfolio, and OF_SECURITY connects a Position to the Stock it represents.

Edges have directionality, pointing from a source node to a target node, which captures the nature of the relationship. A Customer HAS_ACCOUNT pointing to an Account expresses ownership. Edges can also carry properties that describe characteristics of the relationship. A transaction relationship might include the transaction amount, date, and type as properties on the edge itself.

The power of edges lies in enabling traversal queries. You can ask questions like "Find all customers who have accounts at the same bank as customers holding renewable energy stocks" by starting at renewable energy Stock nodes, traversing OF_SECURITY edges backwards to Position nodes, then to Account nodes, then to Bank nodes, then back to other Account nodes at the same bank, and finally to their Customer owners. This multi-hop traversal, which would require complex joins in SQL, becomes a natural graph pattern.

### Benefits of Graph Representation

Knowledge graphs excel in domains where relationships are as important as the entities themselves. Financial services, social networks, recommendation systems, fraud detection, and supply chain management all benefit from graph representation because understanding connections reveals insights invisible in traditional table-based views. Graphs make relationship queries natural and performant—finding patterns, paths, communities, and influences becomes straightforward rather than requiring expensive recursive SQL.

The graph structure also evolves gracefully. Adding new relationship types or node types doesn't require altering existing tables or migrating data. If you discover that customers have interests in investment sectors, you can add INTERESTED_IN relationships pointing to new Sector nodes without touching existing Customer or Stock data. This flexibility makes graphs ideal for domains where the data model evolves as business understanding deepens—exactly the scenario in agent-augmented systems where agents discover new relationships in unstructured documents.

## Ontology Tables

An ontology table is a schema-level artifact that catalogs and defines the types of entities and relationships that exist (or could exist) in a knowledge graph. While the knowledge graph itself stores actual data instances—specific customers, particular accounts, individual transactions—the ontology table describes the templates and rules for what kinds of data the graph can contain. Think of it as the metadata layer that defines the vocabulary of the knowledge graph.

In the context of an evolving, agent-enriched system, the ontology table serves several critical purposes. It maintains a registry of all known node labels (Customer, Account, Stock, etc.) and relationship types (HAS_ACCOUNT, INTERESTED_IN, etc.), along with their semantic meanings. When an AI agent analyzing customer profiles discovers that customers frequently mention investment interests, the agent consults the ontology to determine whether an INTERESTED_IN relationship type already exists or whether a new relationship concept needs to be proposed.

The ontology differs from the knowledge graph itself in that it describes structure rather than data. The knowledge graph might contain a million Customer nodes and specific HAS_ACCOUNT relationships connecting them to Account nodes. The ontology table describes what it means to be a Customer (what properties are expected, which relationships are valid), what HAS_ACCOUNT signifies, and what rules govern how these concepts relate. It's the difference between a database schema and the data in the database, elevated to the graph context.

Ontology tables are crucial for maintaining semantic consistency as the graph evolves. Without an ontology, agents might create redundant relationship types—one agent creates INTERESTED_IN while another creates HAS_INTEREST_IN for the same concept, fragmenting the graph. The ontology provides a controlled vocabulary and change management process. When agents propose new relationship types based on insights from documents, these proposals go through an ontology validation step. Does a similar concept already exist? Does this new relationship type make semantic sense? How should it integrate with existing patterns?

As the system discovers new patterns in unstructured data, the ontology evolves in a managed way. Agents don't just add arbitrary relationships; they follow ontology guidelines to ensure that graph enrichment maintains coherence. This governance layer enables the knowledge graph to grow smarter without becoming chaotic, supporting the continuous enrichment loop while preserving the semantic integrity that makes the graph valuable for querying and analysis.

## Neo4j Graph Data Science (GDS)

Neo4j Graph Data Science (GDS) is a library of graph algorithms designed to uncover patterns, predict relationships, and extract insights from the structure of connected data. While traditional analytics focuses on aggregating and filtering rows in tables, graph algorithms analyze the topology of relationships—finding communities of densely connected nodes, identifying the most influential nodes, discovering hidden paths, and measuring similarity based on connection patterns. These algorithms transform a knowledge graph from a queryable data structure into an analytical engine for discovering non-obvious insights.

### Community Detection: Finding Clusters and Groups

**Community Detection** algorithms identify clusters of nodes that are more densely connected to each other than to the rest of the graph. In a retail investment context, community detection might discover that certain customers form tight clusters based on shared banks, similar investment portfolios, or common transaction patterns. These clusters often represent meaningful business segments—perhaps young professionals with similar risk profiles and technology stock interests, or retirees who favor dividend-paying utilities.

The **Louvain** algorithm is a popular community detection method that optimizes for modularity, repeatedly grouping nodes to maximize the density of connections within communities while minimizing connections between communities. **Label Propagation** works differently, starting with each node in its own community and iteratively updating each node's community based on its neighbors' labels until stable communities emerge. These algorithms reveal natural groupings that might not be apparent from attribute data alone, enabling targeted marketing campaigns, peer-based recommendations, and segment-specific strategies.

### Path Finding: Discovering Connections

**Path Finding** algorithms discover how nodes connect through the graph, revealing relationships that aren't immediately obvious. Finding the shortest path between two customers might expose unexpected connections—both bank at institutions that share a correspondent bank, creating an indirect relationship through multiple hops. **Shortest Path** algorithms (like Dijkstra's) find the minimum-cost route between nodes, useful for understanding transaction flows or tracing influence chains. **A*** (A-star) extends this with heuristics to guide path finding more efficiently.

In financial applications, path finding helps identify risk concentrations. If multiple customer accounts all connect to the same investment positions through various intermediary accounts, a single stock's poor performance might affect more customers than obvious direct holdings suggest. Path algorithms also support compliance use cases, detecting undisclosed relationships or potential conflicts of interest by discovering unexpected connection paths.

### Centrality Algorithms: Identifying Important Nodes

**Centrality** algorithms measure node importance based on their position in the graph's topology. **PageRank**, famous for its use in Google's search algorithm, identifies influential nodes by considering both the number of incoming relationships and the importance of the nodes those relationships come from. In a customer referral network, PageRank finds customers who are well-connected to other influential customers, making them valuable advocates.

**Betweenness Centrality** identifies nodes that frequently appear on shortest paths between other nodes, serving as bridges or gatekeepers. In a transaction network, high betweenness centrality accounts might represent clearing accounts or intermediary points where transaction flows converge. **Degree Centrality** simply counts direct connections, while **Closeness Centrality** measures how quickly a node can reach all others, useful for identifying central customers in communication networks.

These centrality measures enable sophisticated analytics—identifying systemically important accounts, finding key influencers for marketing, or detecting potential bottlenecks in transaction processing. They quantify concepts like "importance" and "influence" that are difficult to capture with traditional database queries.

### Similarity Algorithms: Finding Similar Nodes

**Similarity** algorithms identify nodes that are alike based on their relationship patterns rather than their direct attributes. **Node Similarity** compares nodes based on their neighborhoods—two customers who have accounts at the same banks, hold similar stocks, and perform comparable transaction patterns are considered similar even if their demographic attributes differ. **K-Nearest Neighbors** (kNN) finds the most similar nodes to a given node, enabling recommendations and clustering.

These algorithms power recommendation engines: customers similar to you invested in these opportunities. They enable gap analysis: similar customers have these products that you lack. They support risk modeling: customers with similar graph patterns exhibited these behaviors. Similarity based on graph structure captures an intuitive notion of "alike" that pure attribute-based similarity misses—two customers might have different ages and incomes but identical investment philosophies revealed through their portfolio structures.

### Value for Enterprise Analytics

These graph algorithms are valuable for enterprise analytics because they reveal insights that don't exist in the raw data—they're emergent properties of the relationship structure. Community detection finds segments that weren't defined in advance. Centrality identifies influence that isn't captured in any attribute. Similarity discovers patterns that transcend explicit features. When combined with the enriched relationships that agents extract from unstructured documents, these algorithms become even more powerful. The INTERESTED_IN relationships that agents create by analyzing customer profiles become inputs to community detection (finding customers with shared interests) and similarity algorithms (finding customers with compatible investment preferences), unlocking insights that neither structured data alone nor document analysis alone could provide.

## How These Technologies Work Together

The agent-augmented knowledge graph pattern emerges from the synergistic integration of these technologies, each contributing its strengths to create a system more powerful than any single component. The knowledge graph in Neo4j provides the foundational data structure, representing customers, accounts, investments, and their relationships with semantic clarity. This graph captures the structured reality of financial relationships—who owns what, where accounts are held, which stocks comprise portfolios.

The Databricks lakehouse receives data extracted from this graph, making it available in a format suitable for large-scale analytics and AI processing. Structured graph data flows into Delta Lake tables where the Genie agent can query it with SQL-like efficiency, answering questions about balances, positions, and transaction patterns. Simultaneously, unstructured documents—customer profiles, market research, investment strategies—reside in Unity Catalog volumes where the Knowledge Assistant agent analyzes them to extract narrative insights about preferences, interests, and goals.

The Multi-Agent Supervisor orchestrates the collaboration between Genie and the Knowledge Assistant, enabling questions that span both data types. When analysis reveals gaps between customer interests expressed in documents and actual portfolio holdings in structured data, agents propose new relationships to capture these insights explicitly in the graph. The ontology table governs this enrichment process, ensuring that new relationship types maintain semantic consistency and don't fragment the graph's coherence.

These agent-discovered relationships flow back into Neo4j, enriching the knowledge graph with insights extracted from unstructured sources. Now the graph captures not just transactional facts but also expressed interests, discovered preferences, and contextual information that was previously trapped in prose. With this enriched graph, Neo4j GDS algorithms unlock deeper insights—community detection finds clusters of customers with shared interests, similarity algorithms match customers with compatible investment philosophies, centrality measures identify influential customer advocates, and path finding reveals unexpected connection patterns.

The entire system operates as a continuous enrichment loop. Graph data flows to the lakehouse for AI-driven analysis. Agents examine both structured and unstructured data to discover enhancement opportunities. Proposed enrichments validate against the ontology. Approved relationships write back to the graph. The newly enriched graph provides even richer data for the next cycle. Over time, the knowledge graph evolves from a static model of transactional relationships into a living, learning representation of the organization's domain, combining the precision of structured data with the context of unstructured insights, all governed by ontologies and analyzable with sophisticated graph algorithms.

This architectural pattern transforms how organizations leverage their data, moving beyond the limitations of either pure databases or pure document repositories to create hybrid intelligence systems where AI agents continuously mine insights and enrich semantic models that serve increasingly sophisticated analytics.
