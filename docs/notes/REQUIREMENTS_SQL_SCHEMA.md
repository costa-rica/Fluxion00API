# Requirements for SQL_SCHEMA.md

## Purpose

Create `SQL_SCHEMA.md` - a condensed database schema reference optimized for LLM consumption in Text-to-SQL applications. This file will be used by the Fluxion00API agent system to provide database schema context when generating SQL queries.

## Target Location

`docs/SQL_SCHEMA.md` (root of NewsNexus10Db project)

## Design Constraints

### Size Requirements

- **Target size**: 10,000-15,000 characters (~2,500-4,000 tokens)
- **Maximum size**: 20,000 characters (~5,000 tokens)
- Current `DATABASE_OVERVIEW.md` is 35,000+ characters - this must be **50-60% smaller**

### Why Conciseness Matters

The consuming LLM (Mistral:instruct on Ollama) has limited context window:
- Mistral 7B v0.2+: 32k tokens total context
- SQL_SCHEMA.md will be included in every Text-to-SQL prompt
- Must leave room for: system prompt, user question, conversation history, generated SQL

**Token budget breakdown per query**:
- System prompt: ~500-1,000 tokens
- SQL_SCHEMA.md: ~2,500-4,000 tokens (target)
- User question: ~10-50 tokens
- Conversation history: ~1,000-5,000 tokens (variable)
- Generated SQL + reasoning: ~500-1,000 tokens

## Content to Include

### Essential Information

1. **Table names** (actual SQLite table names, not TypeScript model names)
2. **Column names and data types**
3. **Primary keys** (PK)
4. **Foreign keys** (FK) with references
5. **Important constraints** (NOT NULL, UNIQUE, DEFAULT values)
6. **Brief table descriptions** (one sentence maximum)

### Format

Use compact tabular format with standard abbreviations:
- PK = Primary Key
- FK = Foreign Key
- Ref = References (which table/column)

## Content to Exclude

### Remove Entirely

1. **TypeScript code examples** (templates, model initialization, import statements)
2. **Sequelize ORM instructions** (initialization patterns, sync commands)
3. **Project architecture** (directory structure, package.json details)
4. **Environment setup** (PATH_DATABASE, NAME_DB configuration)
5. **Usage examples** (how to use models in Node.js apps)
6. **Development guidance** (why initialization order matters, etc.)
7. **Relationship narratives** - condense verbose relationship descriptions

### Simplify

1. **Relationships**: Include only in foreign key columns, not separate sections
2. **Descriptions**: Maximum one sentence per table
3. **Column descriptions**: Only when name is ambiguous

## Example Format

Use the Articles table as the template. Here's how it should be represented:

```markdown
### Articles

Core article storage from news aggregation services.

| Column                      | Type     | Constraints | Notes                               |
| --------------------------- | -------- | ----------- | ----------------------------------- |
| id                          | INTEGER  | PK          |                                     |
| publicationName             | STRING   | NULL        | News source name                    |
| author                      | STRING   | NULL        |                                     |
| title                       | STRING   | NULL        | Article headline                    |
| description                 | STRING   | NULL        | Article summary/excerpt             |
| url                         | STRING   | NULL        | Original article URL                |
| urlToImage                  | STRING   | NULL        | Featured image URL                  |
| publishedDate               | DATEONLY | NULL        | Publication date                    |
| entityWhoFoundArticleId     | INTEGER  | FK, NULL    | Ref: EntityWhoFoundArticles.id      |
| newsApiRequestId            | INTEGER  | FK, NULL    | Ref: NewsApiRequests.id             |
| newsRssRequestId            | INTEGER  | FK, NULL    | Ref: NewsRssRequests.id             |
| createdAt                   | DATE     | NOT NULL    |                                     |
| updatedAt                   | DATE     | NOT NULL    |                                     |
```

**Note**: All timestamps (createdAt, updatedAt) can be condensed to a single line if space is critical:
```
| createdAt, updatedAt        | DATE     | NOT NULL    | Timestamps                          |
```

## Table Organization

### Grouping (Optional but Recommended)

Organize tables into logical groups for easier scanning:

1. **Core Tables**: Articles, Users, States
2. **Approval Workflow**: ArticleApproveds, ArticlesApproved02, ArticleRevieweds, ArticleIsRelevants
3. **Content & Metadata**: ArticleContents, ArticleDuplicateAnalyses
4. **News Aggregation**: NewsApiRequests, NewsRssRequests, NewsArticleAggregatorSources, WebsiteDomains
5. **AI & Categorization**: ArtificialIntelligences, EntityWhoFoundArticles, EntityWhoCategorizedArticles
6. **Reports**: Reports
7. **Junction Tables**: All *Contract tables

### Junction Tables

For junction/contract tables, include a brief note about the many-to-many relationship:

```markdown
### ArticleStateContracts

Links Articles to States (many-to-many).

| Column    | Type    | Constraints | Notes             |
| --------- | ------- | ----------- | ----------------- |
| id        | INTEGER | PK          |                   |
| articleId | INTEGER | FK NOT NULL | Ref: Articles.id  |
| stateId   | INTEGER | FK NOT NULL | Ref: States.id    |
| createdAt | DATE    | NOT NULL    | Timestamps        |
| updatedAt | DATE    | NOT NULL    |                   |
```

## Model vs Table Names

**Do not include TypeScript model names** unless they differ significantly from table names. The LLM only needs to know SQLite table names for query generation.

Example of what NOT to include:
- ~~**Model:** `Article`~~ (unnecessary - table name is obvious)
- ~~**Model:** `ArticleApproved`~~ (unnecessary)

Only mention model names if there's a significant mismatch that could cause confusion.

## Additional Notes

### Header

Include a brief header explaining the purpose:

```markdown
# SQL Schema Reference

Database schema for NewsNexus10 (SQLite). Optimized for Text-to-SQL query generation.

**Important**: All tables include `createdAt` and `updatedAt` timestamp fields (DATE, NOT NULL) unless otherwise noted.
```

### Relationship Details

The current DATABASE_OVERVIEW.md has extensive relationship documentation (lines 556-642). **Drastically condense this**:
- Foreign keys in table definitions are sufficient for most relationships
- Only document complex many-to-many relationships briefly
- Remove verbose narrative descriptions

## Validation Checklist

Before finalizing SQL_SCHEMA.md, verify:

- [ ] File size is ≤20,000 characters
- [ ] Target size of 10,000-15,000 characters achieved
- [ ] All table names match actual SQLite table names
- [ ] All foreign key references are accurate
- [ ] No TypeScript code examples included
- [ ] No Sequelize initialization instructions included
- [ ] No environment setup or project architecture details
- [ ] Junction tables clearly identify the many-to-many relationship
- [ ] Consistent formatting across all tables

## Implementation Notes

This file will be generated in the **NewsNexus10Db** project (TypeScript database models project), not in Fluxion00API. The generated `SQL_SCHEMA.md` will then be referenced by the Fluxion00API agent system when implementing Text-to-SQL functionality.
