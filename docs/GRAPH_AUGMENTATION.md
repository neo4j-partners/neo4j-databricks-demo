# When Your Graph Database Knows Less Than Your Documents

James Anderson's customer profile mentions renewable energy stocks. His portfolio contains zero renewable energy holdings. This gap exists in thousands of organizations: structured databases store what customers *have*, while unstructured documents describe what they *want*. Traditional ETL pipelines never bridge this divide.

This post demonstrates how AI agents can continuously enrich a Neo4j knowledge graph by analyzing documents stored in a Databricks lakehouse. The pattern creates a feedback loop where agents read graph data, compare it against unstructured sources, and propose new relationships that capture insights no schema designer anticipated.

> **Prerequisites:** This post assumes familiarity with Neo4j's property graph model, Databricks Unity Catalog, and basic Cypher. If terms like "Delta Lake" or "graph traversal" need explanation, start with the [Background Concepts](BACKGROUND_CONCEPTS.md) guide.

## The Problem: Structured Data Captures Facts, Not Intent

A retail investment platform stores customer portfolios in Neo4j. The graph models seven node types and seven relationships:

```
┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│   Customer   │────▶│    Account    │────▶│     Bank     │
└──────────────┘     └───────────────┘     └──────────────┘
                            │
                            ▼
                     ┌───────────────┐     ┌──────────────┐
                     │   Position    │────▶│    Stock     │────▶ Company
                     └───────────────┘     └──────────────┘
```

This structure captures transactional reality with precision. The graph knows that customer C0001 holds 50 shares of TCOR purchased at $142.50, that the position sits in an investment account at First National Trust, and that TCOR represents TechCore Solutions in the technology sector. Cypher queries traverse these relationships in milliseconds, answering questions like "show me all customers holding technology stocks worth over $10,000" without breaking a sweat.

What the graph cannot answer: which customers *want* renewable energy exposure but don't have it?

That information lives in customer profile documents stored separately, never connected to the graph structure. Here's an excerpt from James Anderson's profile (customer C0001):

> James is particularly interested in emerging technologies and has expressed interest in expanding his portfolio to include renewable energy stocks and retail investment companies.

The structured database knows James holds TCOR, SMTC, and MOBD (all technology stocks). It has no idea he wants renewable energy exposure. A financial advisor reading the profile would spot this gap immediately and start a conversation about solar ETFs or wind power companies. The graph remains oblivious, and so does any application built on top of it.

This disconnect isn't a data quality problem. The profile information exists; it simply lives in a format that traditional ETL processes ignore. Customer service representatives write these profiles during onboarding calls. Relationship managers update them after quarterly reviews. The insights accumulate in prose form, rich with context and nuance, while the graph database maintains its rigid schema of nodes and relationships.

## The Architecture: Agents as Analytical Intermediaries

The solution introduces AI agents that operate between the graph database and the document store. These agents read both sources, identify discrepancies, and propose graph enrichments that capture insights from unstructured text.

```
                              ┌─────────────────────────────────────┐
                              │         DATABRICKS LAKEHOUSE        │
                              │                                     │
┌─────────────────┐           │  ┌─────────────┐  ┌─────────────┐  │
│                 │  Extract  │  │ Delta Lake  │  │   Unity     │  │
│   Neo4j Graph   │──────────▶│  │   Tables    │  │  Catalog    │  │
│                 │           │  │ (14 tables) │  │  Volumes    │  │
│  7 node types   │           │  └──────┬──────┘  └──────┬──────┘  │
│  7 rel types    │           │         │                │         │
│                 │           │         ▼                ▼         │
│                 │           │  ┌─────────────┐  ┌─────────────┐  │
│                 │           │  │   Genie     │  │  Knowledge  │  │
│                 │           │  │   Agent     │  │  Assistant  │  │
│                 │           │  └──────┬──────┘  └──────┬──────┘  │
│                 │           │         └───────┬────────┘         │
│                 │           │                 ▼                  │
│                 │  Enrich   │  ┌───────────────────────────────┐ │
│                 │◀──────────│  │   Multi-Agent Supervisor      │ │
└─────────────────┘           └──┴───────────────────────────────┴─┘
```

The bidirectional flow distinguishes this architecture from traditional ETL. Data doesn't just move from source to destination; it cycles back. Extraction populates the lakehouse with structured graph data that agents can query. Enrichment returns agent-discovered relationships to Neo4j, where they become first-class citizens available for graph traversal and algorithms.

This cycling matters because insights compound. An agent discovers that James wants renewable energy stocks. That enrichment creates an INTERESTED_IN relationship in the graph. The next analysis cycle might find other customers with similar interest patterns, enabling community detection algorithms to cluster customers by shared preferences. Those clusters inform marketing campaigns, which generate new customer interactions, which produce new profile updates, which feed back into the enrichment loop.

The lakehouse serves as the analytical staging ground where this synthesis happens. Neo4j excels at storing and traversing relationships, but it wasn't designed for the kind of cross-referencing analysis that compares document contents against graph structure. Databricks provides the compute environment where agents can join tabular extracts with vector-searched document chunks, run SQL aggregations alongside LLM inference, and produce enrichment proposals that would be awkward to generate inside the graph database itself.

## Step 1: Extract Graph Data to the Lakehouse

The Neo4j Spark Connector extracts nodes and relationships into Delta Lake tables. Each node type becomes a table; each relationship type becomes an edge table. The connector handles the translation from Neo4j's property graph model to Spark's columnar format automatically.

```python
# Core extraction pattern (requires neo4j-connector-apache-spark_2.12:5.3.1_for_spark_3)
df = (spark.read.format("org.neo4j.spark.DataSource")
      .option("url", neo4j_url)
      .option("labels", "Customer")  # Extracts all Customer node properties
      .load())

df.write.format("delta").saveAsTable("retail_investment.customer")
```

The `labels` option tells the connector to extract all nodes with the Customer label, automatically including every property defined on those nodes. No need to enumerate fields manually; the connector introspects the graph schema and creates corresponding Spark columns. Relationship extraction follows a similar pattern, specifying the relationship type and the labels of connected nodes.

After extraction, Unity Catalog contains 14 tables: 7 node tables (Customer, Account, Position, Stock, Company, Bank, Transaction) and 7 edge tables representing relationships like HAS_ACCOUNT and HAS_POSITION. The schema preserves Neo4j's property structure while enabling SQL-based analytics. A financial analyst can now run standard SQL queries against graph data without learning Cypher, which opens the data to a broader audience of business users.

The extraction also captures metadata that proves useful during enrichment. Each row includes the Neo4j element ID and labels, enabling precise write-back operations later. Timestamps record when data was extracted, supporting incremental updates that avoid reprocessing unchanged records.

## Step 2: Store Unstructured Documents in Unity Catalog Volumes

The lakehouse stores customer profiles, market research, and investment guides as files in Unity Catalog volumes. These documents contain information that never made it into structured fields during data entry, either because the schema didn't anticipate it or because free-form text captured nuances that checkboxes couldn't express.

```
/Volumes/retail_investment/retail_investment/documents/
├── customer_profile_james_anderson.txt
├── customer_profile_maria_rodriguez.txt
├── renewable_energy_investment_trends.txt
├── market_analysis_technology_sector.txt
└── ... (14 documents total)
```

Maria Rodriguez's profile reveals ESG preferences not captured in the database:

> Maria has expressed particular interest in socially responsible investing. She has inquired about ESG funds and companies with strong sustainability practices.

Her structured record shows `riskProfile: conservative` and holdings in GFIN (Global Finance Corp). The database has no field for investment philosophy or values-based preferences. A dropdown menu for risk tolerance can't capture "I want my money to reflect my values." That sentiment lives only in the profile document, invisible to any query against the structured tables.

Market research documents add another dimension. A renewable energy trends report might name specific companies like Solar Energy Systems (SOEN) and Renewable Power Inc (RPOW) as strong opportunities in the sector. An investment strategy guide might explain optimal portfolio allocations for different risk profiles. This contextual information helps agents understand not just what customers want, but what options exist to satisfy those wants.

## Step 3: Configure the Multi-Agent System

Two specialized agents handle different data modalities. A supervisor coordinates their work and synthesizes their outputs into actionable insights.

### Genie Agent: Structured Data Queries

The Genie agent translates natural language into SQL queries against the Delta Lake tables. When asked "Which customers have investment accounts with balances exceeding $50,000?", Genie generates the appropriate joins across customer, account, and edge tables, executes the query, and returns results in a format suitable for further analysis.

Genie excels at quantitative questions: account balances, portfolio values, transaction counts, position sizes. It understands the schema of the extracted tables and can perform complex aggregations that would require multiple Cypher queries to replicate. The tradeoff is that Genie cannot interpret context, sentiment, or stated preferences. It answers questions about what *is*, not what customers *want* or *feel*.

### Knowledge Assistant: Document Analysis

The Knowledge Assistant reads documents from the Unity Catalog volume using retrieval-augmented generation (RAG). It extracts customer preferences, investment interests, and qualitative insights that exist only in prose form.

When asked "What investment interests has James Anderson expressed?", the Knowledge Assistant searches the document corpus, retrieves relevant chunks from James's profile, and synthesizes a response: "James Anderson (C0001) has expressed interest in renewable energy stocks and retail investment companies. His profile notes interest in expanding beyond his current technology-focused portfolio."

The Knowledge Assistant handles questions that structured data cannot answer. What themes does a customer mention repeatedly? What concerns have they raised about their current portfolio? What life events might influence their investment timeline? These insights hide in narrative text, accessible only through document understanding.

### Multi-Agent Supervisor: Orchestration and Synthesis

Neither agent works in isolation. The supervisor orchestrates their collaboration, understanding which agent to invoke for each subtask and how to combine their responses into coherent analysis.

Consider the question: "Find customers interested in renewable energy who have no renewable energy holdings." This requires both agents working in sequence. The Knowledge Assistant first identifies customers who mention renewable energy interest in their profiles. Genie then queries the portfolio tables to retrieve actual holdings for those specific customers. The supervisor compares the two result sets, flagging customers where expressed interest doesn't match portfolio reality.

This orchestration creates analytical capabilities that neither agent possesses alone. Genie can't read profiles. The Knowledge Assistant can't query portfolio tables. Together, coordinated by the supervisor, they can answer questions that span the structured-unstructured divide. The supervisor also handles follow-up queries, maintaining context across a multi-turn analysis session and knowing when to invoke each agent based on the nature of the question.

## Step 4: Identify Enrichment Opportunities

The multi-agent system reveals gaps invisible to either data source alone. These gaps fall into several categories, each representing a different kind of enrichment opportunity.

**Interest-holding mismatches** occur when customers express preferences their portfolios don't reflect. James Anderson mentions renewable energy; his portfolio contains only technology stocks. This gap might represent a cross-sell opportunity, a sign that an advisor conversation is overdue, or simply a customer preference that hasn't yet translated into action.

**Risk profile discrepancies** emerge when narrative descriptions contradict structured classifications. A customer classified as "aggressive" in the database might describe themselves as "careful" or "preservation-focused" in profile conversations. These mismatches often indicate stale data, miscommunication during onboarding, or evolving customer attitudes that haven't been captured in structured updates.

**Data quality gaps** appear when agents find information in documents that should exist in structured fields but doesn't. Employment changes, family circumstances, retirement timelines, and other life details often appear in profile notes long before anyone updates the database. Flagging these gaps prompts data stewardship efforts that improve the structured data itself.

**Gap Analysis Results:**

| Customer | Expressed Interest | Current Holdings | Gap Type |
|----------|-------------------|------------------|----------|
| C0001 (James Anderson) | Renewable energy, retail investment | TCOR, SMTC, MOBD (all tech) | Interest-holding mismatch |
| C0002 (Maria Rodriguez) | ESG/sustainable investing | GFIN (financial sector) | Values-portfolio mismatch |
| C0003 (Robert Chen) | Aggressive growth, active trading | Mixed portfolio | No gap (profile matches behavior) |

James and Maria represent enrichment opportunities. Robert's profile aligns with his actual behavior, requiring no enrichment. Not every analysis yields a gap, and that's useful information too. Confirming alignment validates the structured data and indicates that this customer's record accurately reflects their situation.

## Step 5: Propose and Validate Graph Enrichments

Agents generate enrichment proposals in a structured format that captures both the proposed relationship and the evidence supporting it:

```python
enrichment_proposal = {
    "source_node": {"label": "Customer", "key": "C0001"},
    "relationship_type": "INTERESTED_IN",
    "target_node": {"label": "Sector", "key": "RenewableEnergy"},
    "confidence": 0.92,
    "source_document": "customer_profile_james_anderson.txt",
    "extracted_phrase": "expressed interest in expanding his portfolio to include renewable energy stocks"
}
```

The confidence score reflects extraction certainty. "Expressed strong interest in" yields higher confidence than "mentioned considering" or "advisor suggested." Cross-referencing multiple documents that mention the same interest boosts consolidated confidence above any single extraction.

Before writing to the graph, the ontology validation layer checks for conflicts. Without this check, agents might create semantically equivalent relationship types with different names: INTERESTED_IN, HAS_INTEREST_IN, SHOWS_INTEREST_FOR. The validator compares proposed relationship types against existing schema, using semantic similarity to catch near-duplicates. If a sufficiently similar type exists, the proposal reuses it rather than creating redundancy.

Schema evolution follows a governance workflow. Low-risk patterns auto-approve: adding an INTERESTED_IN relationship to a customer who doesn't have one yet. Novel relationship types queue for human review. A data architect examines proposals for DISLIKES or AVOIDS relationships, deciding whether these concepts deserve first-class representation in the graph or whether they should map to existing constructs with appropriate properties.

## Step 6: Write Enrichments Back to Neo4j

Validated enrichments become Cypher statements that create new nodes and relationships:

```cypher
MERGE (sector:Sector {sectorId: 'RenewableEnergy'})
SET sector.name = 'Renewable Energy'

MATCH (c:Customer {customerId: 'C0001'})
MATCH (s:Sector {sectorId: 'RenewableEnergy'})
MERGE (c)-[r:INTERESTED_IN]->(s)
SET r.confidence = 0.92,
    r.source_document = 'customer_profile_james_anderson.txt'
```

The MERGE pattern ensures idempotency. Running the same enrichment twice doesn't create duplicate relationships. Properties on the relationship capture provenance: which document contained the evidence, what phrase was extracted, when the enrichment occurred, what confidence level the agent assigned.

The enriched graph now answers questions that were previously impossible:

```cypher
MATCH (c:Customer)-[:INTERESTED_IN]->(s:Sector {name: 'Renewable Energy'})
WHERE NOT EXISTS {
    MATCH (c)-[:HAS_ACCOUNT]->()-[:HAS_POSITION]->()-[:OF_SECURITY]->()-[:OF_COMPANY]->(co)
    WHERE co.sector = 'Renewable Energy'
}
RETURN c.customerId, c.firstName, c.lastName
```

This query finds customers who have expressed renewable energy interest but hold no renewable energy stocks. Before enrichment, this question couldn't be asked. The graph had no representation of customer interests, only holdings. After enrichment, interests become first-class relationships that participate in graph queries alongside transactional data.

## Applying Graph Algorithms to Enriched Data

Writing enrichments back to Neo4j preserves the graph's semantic structure for advanced analytics. Neo4j Graph Data Science algorithms operate on relationships as first-class objects, enabling computations that would be awkward or impossible in tabular form.

### Jaccard Similarity on INTERESTED_IN Relationships

Jaccard similarity measures overlap between sets. For customers, the "set" is their collection of interest relationships. Two customers who share three out of four interests have higher Jaccard similarity than two who share one out of ten.

```cypher
CALL gds.nodeSimilarity.stream('customer-interests', {similarityCutoff: 0.3})
YIELD node1, node2, similarity
RETURN gds.util.asNode(node1).customerId AS customer1,
       gds.util.asNode(node2).customerId AS customer2,
       similarity
ORDER BY similarity DESC
```

Customers with high similarity scores share multiple interest sectors. This powers recommendation engines: "Customers with similar interests also invested in..." The recommendations emerge from the graph structure itself, not from explicit rules or predetermined segments. As enrichment adds more interest relationships, the similarity computations automatically incorporate new data without requiring model retraining.

### Community Detection on Interest Clusters

Louvain community detection groups densely connected nodes into clusters. Applied to the customer-interest graph, it identifies natural groupings of customers who share common interests.

Community 3 might contain customers interested in ESG investing and sustainable energy. Community 7 might cluster aggressive growth seekers who mention technology and biotech. These communities emerge organically from the relationship structure, revealing segments that marketing teams might not have anticipated.

Marketing can target communities with relevant campaigns. Advisors can use community membership as conversation context: "I see you share interests with customers who have found success with our sustainable investing options." The segmentation updates automatically as enrichment adds new interest relationships, keeping clusters current without manual intervention.

## Why Tabular Representations Fall Short

Extracting graph data to Delta Lake tables enables agent queries, but the tabular representation doesn't support graph algorithms or intuitive multi-hop exploration. The distinction matters when choosing where to perform different types of analysis.

Consider finding customers who share banks with customers holding renewable energy stocks. In Cypher:

```cypher
MATCH (c1:Customer)-[:HAS_ACCOUNT]->(:Account)-[:AT_BANK]->(b:Bank)
      <-[:AT_BANK]-(:Account)<-[:HAS_ACCOUNT]-(c2:Customer)
      -[:HAS_ACCOUNT]->(:Account)-[:HAS_POSITION]->(:Position)
      -[:OF_SECURITY]->(:Stock)-[:OF_COMPANY]->(co:Company)
WHERE co.sector = 'Renewable Energy' AND c1 <> c2
RETURN DISTINCT c1.customerId, b.name as shared_bank
```

The pattern reads naturally: start with a customer, follow the account relationship to their bank, traverse back through other accounts at the same bank to find other customers, then follow those customers' investment paths to see if they hold renewable energy stocks. Six relationship hops expressed in a single pattern.

The equivalent SQL requires joining 10 tables. The join order affects performance dramatically, and reasoning about cardinality explosions requires understanding how many accounts exist per customer, how many customers per bank, how many positions per account. The cognitive overhead increases with each hop, and query plans become difficult to predict.

This doesn't mean tabular representations are useless. Delta Lake tables excel at large-scale aggregations, batch processing, and serving as data sources for SQL-speaking analytics tools. The Genie agent needs those tables to answer quantitative questions. The architecture uses each representation for its strengths: tables for agent comprehension and batch analytics, the graph for relationship traversal and real-time queries.

The ontology table that helps agents understand graph structure provides another example. Agents query it to check whether proposed relationship types already exist, but no analyst would want to explore the graph through that flattened representation. The semantic richness that makes graphs intuitive for humans is precisely what gets lost when relationships decompose into foreign key references across multiple tables.

## Implementation Considerations

### Schema Evolution and Governance

Agents propose new relationship types as they discover patterns. Without governance, schema sprawl becomes a problem. A graph with 47 subtly different relationship types for expressing customer preferences becomes harder to query than one with a coherent, well-documented ontology.

The architecture routes schema proposals through approval workflows. Low-risk additions (new instances of approved relationship types) auto-approve. Novel types (DISLIKES, CONCERNED_ABOUT, SKEPTICAL_OF) queue for review by data architects who decide whether the concept deserves dedicated representation or should map to existing constructs.

This human-in-the-loop checkpoint prevents agents from evolving the schema in directions that make sense locally but create incoherence globally. An agent processing customer profiles might propose WORRIED_ABOUT relationships, while another processing advisor notes might propose HAS_CONCERNS relationships. A human reviewer recognizes these as the same concept and consolidates them, maintaining schema integrity.

### Confidence Scoring and Validation

Agent extractions aren't perfect. Language models occasionally hallucinate facts, misinterpret context, or extract information that documents don't actually contain. Confidence scoring provides a mechanism for triaging extraction quality.

| Extraction Pattern | Confidence | Action |
|-------------------|------------|--------|
| "expressed strong interest in" | 0.95 | Auto-approve |
| "mentioned considering" | 0.70 | Approve with flag |
| "advisor suggested" | 0.40 | Queue for review |
| Ambiguous context | < 0.30 | Reject |

Cross-referencing improves confidence. If three documents mention James's renewable energy interest, the consolidated confidence exceeds any single extraction. Disagreement between documents triggers review rather than automatic enrichment.

High-stakes domains require stricter thresholds. A healthcare knowledge graph might require human review for any extraction below 0.9 confidence. A marketing segmentation graph might auto-approve at 0.6. The thresholds encode organizational risk tolerance, not technical constraints.

### Incremental Processing and Cost Management

Running full enrichment analysis across all customers and documents after every update becomes prohibitively expensive. LLM inference costs accumulate with document volume, and reprocessing unchanged records wastes compute budget.

The architecture supports incremental triggers. When a customer profile document updates, the system re-analyzes that specific customer against their current graph state. When new market research arrives, a batch job analyzes all documents of that type for novel patterns. Schema changes trigger re-evaluation of existing enrichments against the updated ontology.

Incremental processing keeps agent costs proportional to change volume rather than total data volume. An organization with 100,000 customer profiles doesn't reprocess all of them daily; it processes the hundreds that changed since yesterday.

### Provenance and Explainability

Every enriched relationship carries metadata about its origin. When a relationship manager asks "Why does the system think James wants renewable energy?", the answer traces back to specific document phrases:

```cypher
MATCH (c:Customer {customerId: 'C0001'})-[r:INTERESTED_IN]->(s:Sector)
RETURN r.source_document, r.extracted_phrase, r.confidence
```

This transparency builds trust in agent-generated enrichments. Stakeholders can audit the reasoning, dispute incorrect extractions, and understand why the system made particular recommendations. Explainability also supports compliance requirements in regulated industries where automated decisions must be justifiable.

## The Feedback Loop

The pattern creates a continuous improvement cycle where each iteration adds value:

1. **Extract**: Graph data flows to the lakehouse for agent analysis
2. **Analyze**: Agents compare structured data against unstructured documents
3. **Propose**: Gaps become enrichment candidates with confidence scores
4. **Validate**: Ontology checks prevent schema conflicts and duplicates
5. **Enrich**: Approved relationships write back to Neo4j
6. **Query**: Graph algorithms surface insights from enriched relationships
7. **Repeat**: New documents and graph changes trigger incremental analysis

```
     ┌─────────────────────────────────────────────────────────────┐
     │                                                             │
     │    ┌──────────┐    ┌───────────┐    ┌──────────────────┐   │
     │    │  Neo4j   │───▶│ Lakehouse │───▶│  Multi-Agent     │   │
     │    │  Graph   │    │           │    │  Analysis        │   │
     │    └──────────┘    └───────────┘    └────────┬─────────┘   │
     │         ▲                                    │             │
     │         │         ┌──────────────┐           │             │
     │         └─────────│  Validated   │◀──────────┘             │
     │                   │  Enrichments │                         │
     │                   └──────────────┘                         │
     │                                                             │
     └─────────────────────────────────────────────────────────────┘
```

The graph accumulates institutional knowledge over time. Early cycles capture obvious interest-holding gaps. Later cycles detect subtler patterns: correlations between customer interests and life stages, sector preferences that cluster by geography, investment themes that emerge in profile language before they appear in market trends. The enriched graph becomes a corporate memory that combines transactional facts with behavioral insights, capturing nuances that no upfront schema design could anticipate.

## What This Pattern Does Not Solve

Agent-augmented enrichment has limitations worth acknowledging before committing to implementation.

**Latency**: The enrichment loop runs asynchronously. Changes don't appear instantly in the graph. A customer who updates their profile this morning might not see enrichment-powered recommendations until tomorrow's batch run. For use cases requiring real-time updates, this pattern supplements rather than replaces event-driven architectures.

**Cost**: LLM inference costs accumulate with document volume. Extracting insights from 10,000 customer profiles costs more than extracting from 100, and costs scale with document length and complexity. Incremental processing and confidence thresholds help control costs, but they don't eliminate them. Organizations should model expected volumes and inference costs before committing to production deployment.

**Hallucination risk**: Agents occasionally extract facts that documents don't actually contain. A customer who mentioned "renewable energy" in the context of concerns about volatility might get tagged as interested in the sector. Confidence scoring and cross-validation reduce but don't eliminate this risk. Human review remains necessary for high-stakes enrichments, especially in regulated industries.

**Schema complexity**: Each new relationship type adds cognitive load for developers querying the graph. The ontology must balance richness against navigability. Too many relationship types makes the graph harder to understand and query; too few loses semantic precision. Finding the right granularity requires iterative refinement and user feedback.

**Cold start**: The pattern requires existing graph data and documents to analyze. Bootstrapping a new domain requires populating both sources before enrichment provides value. An empty graph and an empty document store produce no insights, regardless of how sophisticated the agents are.

## Starting Point

Begin with a specific gap analysis question. "Which customers have expressed interests not reflected in their portfolios?" is concrete enough to implement and validate within a sprint. Resist the temptation to build a general-purpose enrichment engine before proving value with a narrow use case.

The code examples in this post use a retail investment domain, but the pattern applies wherever structured graphs coexist with unstructured documents: supply chain networks with supplier profiles, healthcare systems with clinical notes, enterprise knowledge bases with research papers, or customer support graphs with ticket histories.

The graph database becomes more than a query engine. It becomes an evolving representation of organizational knowledge, continuously enriched by agents that bridge the structured-unstructured divide.
