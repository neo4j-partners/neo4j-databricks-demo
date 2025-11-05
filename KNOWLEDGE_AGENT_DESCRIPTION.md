# Multi-Agent System Descriptions

This document contains configuration descriptions for creating the multi-agent system in Databricks.

---

## Genie Agent Description

Use this description when creating the Genie space for querying structured lakehouse data.

### Description

Answers questions about retail investment customers, account balances, portfolio holdings, stock positions, banking relationships, and transaction history across structured data extracted from a graph database into Delta Lake tables.

---

## Knowledge Agent Description

Use this description when creating the Knowledge Agent in Databricks to help the agent understand when to use this data source.

### Data Source Description

This knowledge base contains comprehensive customer profiles, institutional data, and investment research documents for a retail investment platform. The content includes:

**CUSTOMER PROFILES**: Detailed narratives containing demographics, risk profiles, current account holdings, investment preferences, personal financial goals, life circumstances, stated investment interests that may not yet be reflected in portfolios, savings habits, customer service preferences, credit scores, and banking relationship history.

**INSTITUTIONAL PROFILES**: Bank and branch profiles describing organizational history, asset size, geographic presence, investment philosophy, service offerings, wealth management capabilities, business banking specialization, community involvement, and customer satisfaction metrics.

**COMPANY RESEARCH**: Investment analysis reports and quarterly earnings summaries covering business models, financial performance, market position, growth trajectories, competitive advantages, analyst ratings, and strategic initiatives.

**INVESTMENT GUIDES**: Strategy guides covering portfolio allocation approaches for different risk profiles, diversification principles, rebalancing strategies, tax efficiency techniques, retirement planning across life stages, and real estate investment opportunities including direct ownership, REITs, and alternative structures.

**MARKET RESEARCH**: Sector analysis covering technology trends, renewable energy opportunities, market valuations, growth drivers, competitive dynamics, and investment themes across various industries.

**INDUSTRY INSIGHTS**: Research on financial services industry transformation including digital banking, payment innovation, lending disruption, wealth management evolution, emerging technologies, regulatory compliance requirements, and competitive landscape changes.

Use this knowledge base to answer questions about customer investment interests and preferences, risk tolerance narratives, personal financial goals and life circumstances, banking relationship histories, institutional capabilities and specializations, company fundamentals and performance, investment strategy recommendations by risk profile, sector trends and opportunities, retirement planning approaches, real estate investing strategies, regulatory compliance requirements, and industry disruption. This data complements structured lakehouse data by providing narrative context, qualitative insights, forward-looking research, and unexpressed customer preferences that may not be captured in transactional databases.

### Agent Instructions

You are analyzing unstructured customer profiles and investment research documents. Your primary objectives are to:

1. Extract detailed customer insights including stated investment interests, personal goals, risk tolerance narratives, family circumstances, and preferences that may not be reflected in their current portfolio holdings
2. Identify gaps between what customers express interest in (e.g., renewable energy, ESG investing, real estate) and their actual investment positions
3. Provide context about banking relationships, service preferences, and customer engagement patterns
4. Reference specific investment research and market trends from the knowledge base when relevant to customer interests
5. Highlight opportunities for portfolio alignment with customer values and stated preferences
6. Surface qualitative information about customer financial sophistication, life stage, and long-term objectives

When answering questions, cite specific details from customer profiles including customer IDs, ages, occupations, risk profiles, and direct references to their stated interests. Cross-reference market research documents when discussing investment opportunities related to customer interests.

---

## Multi-Agent Supervisor Description

Use this description when creating the Multi-Agent Supervisor to orchestrate both the Genie and Knowledge Agent.

### Description

Provides comprehensive retail investment intelligence by combining structured transactional data analysis with unstructured customer insights and market research. Analyzes customer portfolios, account activity, and holdings alongside qualitative preferences, investment interests, and research recommendations to identify opportunities, gaps, and personalized financial guidance.
