# Case 1 — Enterprise Agentic Text-to-SQL
## Detailed Requirements Specification

## 1. Problem Statement

Build a production-oriented system that allows enterprise users to ask natural-language questions about data stored across one or more databases.

The system should:

1. Understand the user's question.
2. Determine whether it is a database query.
3. Identify the relevant data sources, schemas, tables, columns, and relationships.
4. Retrieve relevant business definitions and SQL examples.
5. Create a structured query plan.
6. Generate SQL.
7. Validate the SQL for syntax, schema correctness, semantics, security, and resource usage.
8. Repair invalid SQL through a bounded retry loop when possible.
9. Execute approved SQL through a controlled database gateway.
10. Validate and interpret the returned result.
11. Produce a concise natural-language answer.
12. Provide provenance explaining which data sources were used.
13. Enforce authorization independently of the LLM.
14. Maintain auditability, observability, reliability, and security.

The central goal is:

> Build a secure, permission-aware, production-oriented natural-language-to-SQL system that can discover relevant enterprise data, generate and validate SQL, execute it through controlled database access, and return a traceable natural-language answer.

---

# 2. Example Environment

Assume the system has access to multiple enterprise databases.

### Snowflake

```text
customers
├── customer_id
├── name
├── email
├── status
└── created_at

transactions
├── transaction_id
├── customer_id
├── amount
└── transaction_date
```

Relationship:

```text
customers.customer_id
        │
        └──────── transactions.customer_id
```

### PostgreSQL

```text
branches
├── branch_id
├── branch_name
└── region

employees
├── employee_id
├── branch_id
├── name
└── salary
```

A user could ask:

> "What was the total revenue from active customers in Q2?"

The system should determine:

- `revenue` → likely `SUM(transactions.amount)`
- `active customers` → `customers.status = 'ACTIVE'`
- `Q2` → appropriate date range
- relevant tables → `customers`, `transactions`
- join → `customers.customer_id = transactions.customer_id`

Then generate, validate, execute, and explain the resulting SQL.

---

# 3. Functional Requirements

## 3.1 Natural-Language Interface

The system must accept natural-language questions.

Examples:

```text
What was our revenue last quarter?
```

```text
Which customers generated more than $10,000 in revenue?
```

```text
How many employees are in each region?
```

The system should support:

- simple aggregations
- filtering
- sorting
- grouping
- joins
- date ranges
- ranking
- comparisons
- basic analytical queries

The initial MVP does not need to support arbitrary complex SQL.

---

# 4. Intent Classification

The system should first determine what type of request it received.

Initial intent categories:

```text
DATABASE_QUERY
NON_DATABASE
UNSAFE
AMBIGUOUS
```

### Example

```text
"Show me revenue by region"
→ DATABASE_QUERY
```

```text
"Write me a poem"
→ NON_DATABASE
```

```text
"Delete all customers"
→ UNSAFE
```

```text
"Show me our performance"
→ AMBIGUOUS
```

The classifier should be lightweight and fast.

A small model or deterministic classifier can handle the first routing stage.

Suggested target:

```text
Intent classification < 500 ms
```

---

# 5. Query Planning

The system should convert the natural-language question into a structured plan before generating SQL.

Example:

```json
{
  "goal": "Calculate revenue from active customers during Q2",
  "operations": [
    "filter active customers",
    "filter transactions by Q2",
    "join customers and transactions",
    "sum transaction amount"
  ],
  "required_data": [
    "customers.status",
    "customers.customer_id",
    "transactions.customer_id",
    "transactions.amount",
    "transactions.transaction_date"
  ]
}
```

The plan should identify:

- user goal
- required operations
- required data
- filters
- aggregations
- grouping
- sorting
- joins
- date constraints

The plan should be structured rather than free-form text.

---

# 6. Metadata / Schema Knowledge Base

The system needs a searchable representation of available enterprise data.

For every database object, store metadata such as:

### Database

```text
database_name
database_type
environment
region
```

### Schema

```text
schema_name
description
```

### Table

```text
table_name
description
row_count_estimate
owner
sensitivity
```

### Column

```text
column_name
data_type
description
nullable
sensitivity
```

### Relationships

```text
source_table
source_column
target_table
target_column
relationship_type
```

### Additional metadata

- primary keys
- foreign keys
- indexes
- business definitions
- synonyms
- permissions
- data sensitivity
- freshness
- lineage

---

# 7. Schema Retrieval

Do not send the entire enterprise schema to the LLM.

Instead, retrieve only the relevant metadata.

For example:

User question:

```text
What was our revenue last quarter?
```

Potential retrieved metadata:

```text
transactions.amount
transactions.transaction_date
transactions.customer_id
customers.customer_id
customers.status
```

The retrieval system should consider:

- table descriptions
- column descriptions
- business glossary
- relationships
- synonyms
- previous successful examples

Possible retrieval architecture:

```text
User Query
    ↓
Embedding
    ↓
Vector Search
    +
BM25 / Keyword Search
    ↓
Candidate Metadata
    ↓
Reranker
    ↓
Relevant Schema Context
```

Hybrid retrieval is preferred over vector search alone.

---

# 8. Business Glossary / Semantic Layer

The system should understand business terminology.

Examples:

```text
Revenue
→ SUM(transactions.amount)
```

```text
Active Customer
→ customers.status = 'ACTIVE'
```

```text
Churned Customer
→ customers.status = 'CHURNED'
```

```text
Q2 2026
→ 2026-04-01 through 2026-06-30
```

Business definitions should be stored independently from the LLM.

This reduces ambiguity and makes SQL generation more consistent.

---

# 9. Few-Shot SQL Example Retrieval

The system should maintain a collection of validated examples.

Example:

```json
{
  "question": "What was revenue last month?",
  "sql": "SELECT SUM(amount) FROM transactions WHERE transaction_date >= ...",
  "tables": ["transactions"]
}
```

Examples should be retrieved based on semantic and lexical similarity.

Useful metadata:

```text
question
SQL
tables_used
columns_used
business_domain
database_type
validation_status
```

Only trusted/validated examples should be used.

---

# 10. SQL Generation

The SQL generator should receive:

- original user question
- structured query plan
- relevant schema metadata
- business definitions
- relevant SQL examples
- database dialect
- authorization constraints

The generator should produce structured output.

Example:

```json
{
  "sql": "SELECT SUM(t.amount) ...",
  "tables_used": [
    "customers",
    "transactions"
  ],
  "columns_used": [
    "customers.status",
    "customers.customer_id",
    "transactions.customer_id",
    "transactions.amount",
    "transactions.transaction_date"
  ]
}
```

The LLM should never receive:

- database passwords
- API secrets
- unrestricted connection strings
- credentials

---

# 11. SQL Validation

SQL must not be executed immediately after generation.

Validation should occur before execution.

Validation should include:

## 11.1 Syntax Validation

Check whether the SQL parses correctly.

Use a SQL parser / AST library.

Do not rely solely on an LLM.

---

## 11.2 Schema Validation

Check:

- tables exist
- columns exist
- aliases are valid
- joins reference valid columns
- database dialect is correct

---

## 11.3 Semantic Validation

Check whether the SQL actually represents the requested operation.

Examples:

```text
User asks for revenue
→ SUM(amount)
```

rather than:

```text
COUNT(amount)
```

Check:

- filters
- aggregation
- grouping
- date ranges
- joins
- business definitions

---

## 11.4 Security Validation

Reject queries that:

- access unauthorized tables
- access unauthorized columns
- contain destructive operations
- attempt SQL injection
- bypass authorization
- access restricted data
- exceed allowed resource limits

Examples of destructive SQL:

```sql
DROP TABLE ...
```

```sql
DELETE FROM ...
```

```sql
UPDATE ...
```

The MVP should use read-only database credentials.

---

## 11.5 Resource Validation

Check for potentially expensive queries.

Potential controls:

- maximum execution time
- maximum rows
- query cost limits
- warehouse/resource limits
- restricted operations
- maximum joins
- maximum result size

---

# 12. Validator Architecture

Recommended validation pipeline:

```text
Generated SQL
     ↓
SQL Parser
     ↓
AST Validation
     ↓
Schema Validation
     ↓
Authorization Validation
     ↓
Security Validation
     ↓
Semantic Validation
     ↓
Resource Validation
     ↓
Execute / Reject
```

An LLM judge can optionally be used for semantic validation.

However:

> An LLM should not be the only SQL validator.

Deterministic validation should handle security and structural correctness wherever possible.

---

# 13. Query Repair

If SQL validation fails, the system may attempt repair.

Example:

```text
SQL Generator
      ↓
Validator
      ↓
FAIL
      ↓
Error Feedback
      ↓
SQL Generator
      ↓
Validator
```

The retry loop must be bounded.

Example:

```text
MAX_RETRIES = 2 or 3
```

The system should stop and return an error if repair repeatedly fails.

Never allow an unbounded agent loop.

---

# 14. Database Execution Gateway

The LLM should never directly connect to the database.

Use a controlled database gateway.

Architecture:

```text
Agent
  ↓
DB Gateway
  ↓
Authorization
  ↓
SQL Validation
  ↓
Resource Controls
  ↓
Database
```

The gateway should enforce:

- authentication
- authorization
- read-only credentials
- query timeout
- row limits
- resource limits
- connection pooling
- auditing
- database selection
- allowed schemas/tables

---

# 15. Authorization

Authorization must be enforced outside the LLM.

Possible models:

```text
RBAC
ABAC
Database Row-Level Security
Policy Engine
```

Example:

```text
User A
→ allowed to access sales tables

User B
→ allowed to access HR tables

User C
→ allowed to access only aggregated reports
```

The LLM should not decide whether the user is authorized.

The authorization layer should determine:

```text
WHO
+
WHAT
+
WHICH DATA
+
WHICH OPERATION
```

---

# 16. Result Processing

After SQL execution, the system receives structured results.

Example:

```json
{
  "columns": ["region", "revenue"],
  "rows": [
    ["East", 1200000],
    ["West", 950000]
  ]
}
```

The system should check:

- empty results
- unexpected result shape
- excessive result size
- execution errors
- null-heavy results
- obvious anomalies

---

# 17. Natural-Language Answer Generation

The final LLM should convert the structured result into a concise answer.

Example:

```text
Revenue in Q2 was $2.15M, with the East region contributing
$1.2M and the West region contributing $950K.
```

The final answer should not expose:

- chain-of-thought
- hidden prompts
- secrets
- internal authorization metadata
- unnecessary system internals

---

# 18. Provenance

The system should provide traceability.

Useful provenance:

```text
Database
Schema
Tables
Columns
Query ID
Execution timestamp
```

Example:

```text
Sources:
- Snowflake / analytics / transactions
- Snowflake / analytics / customers

Query ID:
QRY-12345
```

Do not expose unauthorized metadata.

---

# 19. Explainability

Provide a concise execution summary.

Example:

```text
I used the transactions and customers tables,
filtered transactions to Q2, restricted customers to ACTIVE,
and calculated SUM(transaction.amount).
```

Do not expose raw chain-of-thought.

---

# 20. Error Handling

The system should explicitly handle:

### Ambiguous Question

```text
"Show me performance"
```

Response:

```text
Which performance metric do you mean: revenue, profit, or sales volume?
```

### Missing Data

```text
The requested metric could not be found in the available data.
```

### Unauthorized Data

Do not reveal restricted data or unnecessary information about the existence of restricted resources.

### SQL Generation Failure

Attempt bounded repair.

### Database Failure

Return a controlled error.

### Timeout

Stop execution and return a timeout message.

### Empty Result

Explain that no matching records were found.

---

# 21. Observability

Every request should have a correlation/request ID.

Track:

```text
request_id
user_id
tenant_id
intent
query_plan
retrieved_schema
retrieved_examples
generated_sql
validation_result
retry_count
database
execution_time
model
model_latency
input_tokens
output_tokens
final_result
```

Be careful not to log:

- passwords
- API keys
- secrets
- unnecessary PII
- unrestricted database contents

Audit logs should be tamper-resistant where possible.

---

# 22. Performance Requirements

Initial target requirements:

| Component | Target |
|---|---:|
| Intent classification | < 500 ms |
| Schema retrieval | < 500 ms |
| SQL generation | < 3 s |
| SQL validation | < 1 s |
| Database execution | Workload dependent |
| End-to-end response | Ideally < 10 s |

These are initial engineering targets, not universal guarantees.

Database execution will usually dominate for complex queries.

---

# 23. Reliability Requirements

The system should tolerate:

- malformed SQL
- temporary database failures
- LLM failures
- timeouts
- unavailable data sources
- invalid tool responses
- overloaded databases

Required mechanisms:

### Timeouts

Every external call should have a timeout.

### Retries

Use bounded retries for transient failures.

### Circuit Breakers

Prevent repeatedly calling an unavailable database/model.

### Idempotency

Avoid accidental duplicate execution.

### Request IDs

Every workflow should have a unique identifier.

### Graceful Failure

The system should fail safely rather than executing uncertain SQL.

---

# 24. Security Requirements

Security is a core system requirement.

## Authentication

Determine who the user is.

Possible mechanisms:

```text
JWT
OAuth
SSO
API keys
```

## Authorization

Determine what the user can access.

```text
RBAC
ABAC
RLS
Policy Engine
```

## SQL Injection Protection

Never concatenate untrusted input into SQL manually.

Generated SQL must be parsed and validated.

## Database Credentials

Use:

- secret manager
- short-lived credentials where possible
- read-only database users
- connection pooling

Never give credentials to the LLM.

## PII Protection

Sensitive fields should be classified.

Examples:

```text
email
phone
address
salary
SSN
```

Apply:

- masking
- authorization
- redaction
- auditing

## Resource Protection

Apply:

- query timeouts
- row limits
- cost limits
- concurrency limits

## Prompt Injection Resistance

Treat retrieved database metadata, examples, and external content as untrusted data.

Do not allow retrieved content to override system policies.

Prompt injection defenses are not a substitute for authorization.

---

# 25. Suggested Architecture

High-level architecture:

```text
                    ┌───────────────┐
                    │     User      │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ API Gateway   │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Authentication│
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │Intent Classifier│
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Orchestrator  │
                    └───────┬───────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
       Schema RAG      Glossary RAG    Example RAG
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                    ┌───────────────┐
                    │ Query Planner │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ SQL Generator │
                    └───────┬───────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │    SQL Validator     │
                 │                     │
                 │ Syntax              │
                 │ Schema              │
                 │ Semantic            │
                 │ Security            │
                 │ Authorization       │
                 │ Resource Limits     │
                 └──────────┬──────────┘
                            │
                    ┌───────┴────────┐
                    │                │
                  FAIL              PASS
                    │                │
                    ▼                ▼
              SQL Repair       DB Gateway
                    │                │
                    └───────┐        ▼
                            │   ┌──────────┐
                            │   │ Database │
                            │   └────┬─────┘
                            │        │
                            │        ▼
                            │  Result Validator
                            │        │
                            └────────┤
                                     ▼
                              Answer Generator
                                     │
                                     ▼
                              Answer + Provenance
```

---

# 26. Recommended Technology Stack

## LLM

Use a strong model for:

- query planning
- SQL generation
- semantic reasoning
- final answer generation

Use a smaller model for:

- intent classification
- routing
- lightweight classification

---

## Retrieval

Possible options:

```text
Postgres + pgvector
Pinecone
Weaviate
Qdrant
Milvus
```

For an MVP:

```text
Postgres + pgvector
```

is sufficient.

Use hybrid retrieval:

```text
Dense embeddings
+
BM25 / lexical search
+
Optional reranking
```

---

## SQL Parsing

Use a deterministic SQL parser/AST library appropriate to the supported database dialects.

The parser should support:

- parsing
- AST inspection
- table extraction
- column extraction
- operation detection
- read/write detection

---

## Databases

For development:

```text
PostgreSQL
```

For multi-database testing:

```text
PostgreSQL
+
Snowflake
```

A local PostgreSQL environment is sufficient for the MVP.

---

## Workflow

Use a deterministic workflow/state machine initially.

Do not introduce a complex multi-agent framework unless it provides a clear benefit.

The system is fundamentally:

```text
classify
→ retrieve
→ plan
→ generate
→ validate
→ repair
→ execute
→ answer
```

---

# 27. Non-Functional Requirements

## Security

The system must prevent unauthorized access and unsafe SQL execution.

## Reliability

The system must fail safely when components fail.

## Scalability

The architecture should support:

- multiple users
- multiple databases
- concurrent queries
- horizontal scaling

## Observability

Every workflow should be traceable.

## Maintainability

Components should be modular:

```text
Classifier
Planner
Retriever
SQL Generator
Validator
DB Gateway
Result Processor
Answer Generator
```

## Auditability

Important actions should be recorded.

## Explainability

Users should understand where the answer came from without receiving internal chain-of-thought.

---

# 28. MVP Scope

The first implementation should remain small.

### MVP

Support:

- natural-language database queries
- one database initially
- PostgreSQL
- 2–3 tables
- schema retrieval
- basic business glossary
- SQL generation
- deterministic SQL parser
- basic security validation
- read-only execution
- natural-language answer
- basic logging

Example:

```text
User
 ↓
Intent
 ↓
Schema Retrieval
 ↓
SQL Generation
 ↓
SQL Validation
 ↓
PostgreSQL
 ↓
Answer
```

Use approximately:

```text
20–30 validated SQL examples
```

for few-shot retrieval.

---

# 29. Version 2

Add:

- multiple databases
- Snowflake
- hybrid retrieval
- reranking
- richer business glossary
- SQL repair
- RBAC
- query cost controls
- better observability
- evaluation framework
- result validation

Architecture becomes:

```text
Multi-DB
+
Schema RAG
+
Glossary
+
Example RAG
+
SQL Generator
+
Validator
+
Repair
+
Authorization
+
DB Gateway
```

---

# 30. Version 3

Add enterprise-grade governance:

- centralized policy engine
- fine-grained authorization
- row-level security
- column-level security
- PII masking
- model governance
- audit trail
- evaluation platform
- automated regression testing
- caching
- workload management
- autoscaling
- human-in-the-loop approval
- advanced monitoring

---

# 31. Evaluation Requirements

The system should not be evaluated only on whether SQL executes.

Evaluate:

## Intent Accuracy

```text
DATABASE_QUERY vs NON_DATABASE vs UNSAFE
```

## Schema Retrieval Recall

Did the system retrieve the correct tables and columns?

## SQL Correctness

Does the generated SQL produce the correct result?

## Semantic Accuracy

Does the SQL actually answer the question?

## Security

Does the system reject unauthorized access?

## Execution Reliability

Does the system handle failures correctly?

## Answer Accuracy

Does the final natural-language response correctly represent the database result?

## Latency

Track:

```text
TTFT
LLM latency
retrieval latency
validation latency
database latency
end-to-end latency
```

---

# 32. Important Edge Cases

The implementation should eventually test:

### Ambiguous terminology

```text
"sales"
```

Could mean:

- transaction count
- transaction amount
- revenue
- booked sales

### Missing table

The requested information does not exist.

### Multiple possible joins

Several paths exist between tables.

### Incorrect generated join

The SQL joins unrelated entities.

### Unauthorized table

The user asks for HR information without permission.

### Unauthorized column

The user can access customers but not their email addresses.

### Destructive query

```sql
DELETE ...
```

### Expensive query

A full-table operation over billions of rows.

### Empty result

No records match the question.

### Database outage

The database cannot be reached.

### LLM failure

The model times out or returns malformed structured output.

### Prompt injection

Retrieved metadata attempts to manipulate the agent.

### Cross-database query

Required information exists in different databases.

---

# 33. Suggested Implementation Phases

## Phase 1 — Database and Schema Catalog

Build:

```text
PostgreSQL
    ↓
Schema Introspection
    ↓
Metadata Catalog
```

Extract:

- databases
- schemas
- tables
- columns
- types
- primary keys
- foreign keys
- relationships
- descriptions

---

## Phase 2 — Schema Retrieval

Build:

```text
User Question
    ↓
Embedding
    ↓
Vector Search
    +
Keyword Search
    ↓
Relevant Schema
```

---

## Phase 3 — SQL Generation

Build:

```text
Question
+
Schema
+
Examples
+
Glossary
    ↓
LLM
    ↓
Structured SQL
```

---

## Phase 4 — SQL Validator

Build deterministic checks for:

```text
Syntax
Schema
Tables
Columns
Read/write operations
Authorization
Resource limits
```

---

## Phase 5 — Database Execution Gateway

Build:

```text
Validated SQL
    ↓
DB Gateway
    ↓
Read-only PostgreSQL
    ↓
Result
```

Add:

- timeout
- row limits
- logging
- connection pooling

---

## Phase 6 — Agentic Planning

Add:

```text
Intent
    ↓
Planner
    ↓
Structured Plan
    ↓
Schema / Glossary / Example Retrieval
    ↓
SQL Generator
```

The planner should determine which information is required instead of blindly retrieving everything.

---

## Phase 7 — Authorization and Governance

Add:

```text
Authentication
Authorization
RBAC / ABAC
Policy Engine
PII Controls
Audit Logs
```

Enforce policies before:

```text
data retrieval
LLM context construction
tool execution
result delivery
```

---

## Phase 8 — Evaluation and Observability

Build:

- golden dataset
- SQL correctness tests
- schema retrieval tests
- security tests
- regression tests
- latency monitoring
- token/cost monitoring
- failure monitoring
- audit dashboards

---

# 34. Core Design Principles

### Principle 1 — Never trust the LLM for security

Authorization must be enforced by deterministic infrastructure.

### Principle 2 — Never execute unvalidated SQL

SQL must pass deterministic validation before execution.

### Principle 3 — Do not send the entire schema to the LLM

Retrieve only relevant metadata.

### Principle 4 — Use structured intermediate representations

Use:

```text
Query Plan
SQL AST
Tool Schemas
Typed Results
```

rather than passing large amounts of free-form text.

### Principle 5 — Bound agent loops

Every retry or repair loop needs a maximum number of attempts.

### Principle 6 — Keep credentials outside the model context

The LLM should never see database credentials.

### Principle 7 — Separate planning from execution

The LLM proposes actions.

Controlled infrastructure executes them.

### Principle 8 — Prefer deterministic checks where possible

Use code for:

- syntax
- schema
- authorization
- resource limits
- destructive operations
- execution controls

Use LLMs for:

- natural-language understanding
- planning
- semantic interpretation
- SQL generation
- final explanation

---

# 35. Final Mental Model

For interviews, the architecture can be remembered as:

```text
User
 ↓
API Gateway
 ↓
Authentication
 ↓
Intent Classification
 ↓
Orchestrator
 ↓
Schema + Glossary + Example Retrieval
 ↓
Query Planner
 ↓
SQL Generator
 ↓
SQL Validator
 ├── Syntax
 ├── Schema
 ├── Semantics
 ├── Authorization
 ├── Security
 └── Resource Limits
 ↓
SQL Repair if needed
 ↓
Database Gateway
 ↓
Read-only Database
 ↓
Result Validation
 ↓
Answer Generator
 ↓
Answer + Provenance
```

The key interview point is:

> The LLM should propose what to do; deterministic infrastructure should decide what is allowed and execute it safely.
