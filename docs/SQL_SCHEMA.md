# SQL Schema Reference

Database schema for NewsNexus10 (SQLite). Optimized for Text-to-SQL query generation.

**Important**: All tables include `createdAt` and `updatedAt` timestamp fields (DATE, NOT NULL).

## Core Tables

### Articles

Core article storage from news aggregation services.

| Column                  | Type     | Constraints | Notes                          |
| ----------------------- | -------- | ----------- | ------------------------------ |
| id                      | INTEGER  | PK          |                                |
| publicationName         | STRING   | NULL        | News source name               |
| author                  | STRING   | NULL        |                                |
| title                   | STRING   | NULL        | Article headline               |
| description             | STRING   | NULL        | Article summary/excerpt        |
| url                     | STRING   | NULL        | Original article URL           |
| urlToImage              | STRING   | NULL        | Featured image URL             |
| publishedDate           | DATEONLY | NULL        | Publication date               |
| entityWhoFoundArticleId | INTEGER  | FK, NULL    | Ref: EntityWhoFoundArticles.id |
| newsApiRequestId        | INTEGER  | FK, NULL    | Ref: NewsApiRequests.id        |
| newsRssRequestId        | INTEGER  | FK, NULL    | Ref: NewsRssRequests.id        |
| createdAt, updatedAt    | DATE     | NOT NULL    | Timestamps                     |

### Users

User accounts for the system.

| Column              | Type    | Constraints       | Notes                |
| ------------------- | ------- | ----------------- | -------------------- |
| id                  | INTEGER | PK                |                      |
| username            | STRING  | NOT NULL          |                      |
| email               | STRING  | NOT NULL          |                      |
| password            | STRING  | NOT NULL          |                      |
| isAdmin             | BOOLEAN | DEFAULT false     |                      |
| createdAt, updatedAt| DATE    | NOT NULL          | Timestamps           |

### States

US States reference table.

| Column              | Type    | Constraints       | Notes                |
| ------------------- | ------- | ----------------- | -------------------- |
| id                  | INTEGER | PK                |                      |
| name                | STRING  | NOT NULL          | State full name      |
| abbreviation        | STRING  | NOT NULL          | State abbreviation   |
| createdAt, updatedAt| DATE    | NOT NULL          | Timestamps           |

## Approval Workflow

### ArticleApproveds

User approval decisions for articles.

| Column                      | Type     | Constraints       | Notes             |
| --------------------------- | -------- | ----------------- | ----------------- |
| id                          | INTEGER  | PK                |                   |
| userId                      | INTEGER  | FK, NOT NULL      | Ref: Users.id     |
| articleId                   | INTEGER  | FK, NOT NULL      | Ref: Articles.id  |
| isApproved                  | BOOLEAN  | DEFAULT true      |                   |
| headlineForPdfReport        | STRING   | NULL              |                   |
| publicationNameForPdfReport | STRING   | NULL              |                   |
| publicationDateForPdfReport | DATEONLY | NULL              |                   |
| textForPdfReport            | STRING   | NULL              |                   |
| urlForPdfReport             | STRING   | NULL              |                   |
| kmNotes                     | STRING   | NULL              | Knowledge manager notes |
| createdAt, updatedAt        | DATE     | NOT NULL          | Timestamps        |

### ArticlesApproved02

AI-driven article approval decisions.

| Column                      | Type     | Constraints       | Notes                       |
| --------------------------- | -------- | ----------------- | --------------------------- |
| id                          | INTEGER  | PK                |                             |
| artificialIntelligenceId    | INTEGER  | FK, NOT NULL      | Ref: ArtificialIntelligences.id |
| articleId                   | INTEGER  | FK, NOT NULL      | Ref: Articles.id            |
| isApproved                  | BOOLEAN  | DEFAULT true      |                             |
| headlineForPdfReport        | STRING   | NULL              |                             |
| publicationNameForPdfReport | STRING   | NULL              |                             |
| publicationDateForPdfReport | DATEONLY | NULL              |                             |
| textForPdfReport            | STRING   | NULL              |                             |
| urlForPdfReport             | STRING   | NULL              |                             |
| kmNotes                     | STRING   | NULL              | Knowledge manager notes     |
| createdAt, updatedAt        | DATE     | NOT NULL          | Timestamps                  |

### ArticleRevieweds

User review tracking for articles.

| Column              | Type    | Constraints       | Notes             |
| ------------------- | ------- | ----------------- | ----------------- |
| id                  | INTEGER | PK                |                   |
| userId              | INTEGER | FK, NOT NULL      | Ref: Users.id     |
| articleId           | INTEGER | FK, NOT NULL      | Ref: Articles.id  |
| isReviewed          | BOOLEAN | DEFAULT true      |                   |
| kmNotes             | STRING  | NULL              |                   |
| createdAt, updatedAt| DATE    | NOT NULL          | Timestamps        |

### ArticleIsRelevants

User relevance judgments for articles.

| Column              | Type    | Constraints       | Notes             |
| ------------------- | ------- | ----------------- | ----------------- |
| id                  | INTEGER | PK                |                   |
| userId              | INTEGER | FK, NOT NULL      | Ref: Users.id     |
| articleId           | INTEGER | FK, NOT NULL      | Ref: Articles.id  |
| isRelevant          | BOOLEAN | DEFAULT true      |                   |
| kmNotes             | STRING  | NULL              |                   |
| createdAt, updatedAt| DATE    | NOT NULL          | Timestamps        |

## Content & Metadata

### ArticleContents

Full text content scraped from articles.

| Column                  | Type    | Constraints  | Notes                           |
| ----------------------- | ------- | ------------ | ------------------------------- |
| id                      | INTEGER | PK           |                                 |
| articleId               | INTEGER | FK, NOT NULL | Ref: Articles.id                |
| content                 | STRING  | NOT NULL     | Full article text               |
| scrapeStatusCheerio     | BOOLEAN | NULL         | Cheerio scraper success status  |
| scrapeStatusPuppeteer   | BOOLEAN | NULL         | Puppeteer scraper success status|
| createdAt, updatedAt    | DATE    | NOT NULL     | Timestamps                      |

### ArticleDuplicateAnalyses

Duplicate detection analysis results.

| Column                | Type    | Constraints  | Notes                          |
| --------------------- | ------- | ------------ | ------------------------------ |
| id                    | INTEGER | PK           |                                |
| articleIdNew          | INTEGER | FK, NOT NULL | Ref: Articles.id (new article) |
| articleIdApproved     | INTEGER | FK, NOT NULL | Ref: Articles.id (approved)    |
| reportId              | INTEGER | FK, NULL     | Ref: Reports.id                |
| sameArticleIdFlag     | INTEGER | NOT NULL     |                                |
| articleNewState       | STRING  | NOT NULL     |                                |
| articleApprovedState  | STRING  | NOT NULL     |                                |
| sameStateFlag         | INTEGER | NOT NULL     |                                |
| urlCheck              | INTEGER | NOT NULL     | URL similarity score           |
| contentHash           | FLOAT   | NOT NULL     | Content hash similarity        |
| embeddingSearch       | FLOAT   | NOT NULL     | Embedding similarity score     |
| createdAt, updatedAt  | DATE    | NOT NULL     | Timestamps                     |

## News Aggregation

### NewsApiRequests

Requests made to news API services.

| Column                             | Type     | Constraints  | Notes                               |
| ---------------------------------- | -------- | ------------ | ----------------------------------- |
| id                                 | INTEGER  | PK           |                                     |
| newsArticleAggregatorSourceId      | INTEGER  | FK, NOT NULL | Ref: NewsArticleAggregatorSources.id|
| countOfArticlesReceivedFromRequest | INTEGER  | NULL         |                                     |
| countOfArticlesSavedToDbFromRequest| INTEGER  | NULL         |                                     |
| countOfArticlesAvailableFromRequest| INTEGER  | NULL         |                                     |
| dateStartOfRequest                 | DATEONLY | NULL         | Request date range start            |
| dateEndOfRequest                   | DATEONLY | NULL         | Request date range end              |
| status                             | STRING   | NULL         |                                     |
| url                                | STRING   | NULL         | API request URL                     |
| andString                          | STRING   | NULL         | Boolean AND search terms            |
| orString                           | STRING   | NULL         | Boolean OR search terms             |
| notString                          | STRING   | NULL         | Boolean NOT search terms            |
| isFromAutomation                   | BOOLEAN  | DEFAULT false|                                     |
| createdAt, updatedAt               | DATE     | NOT NULL     | Timestamps                          |

### NewsRssRequests

Requests made to RSS feeds.

| Column                             | Type     | Constraints  | Notes                               |
| ---------------------------------- | -------- | ------------ | ----------------------------------- |
| id                                 | INTEGER  | PK           |                                     |
| newsArticleAggregatorSourceId      | INTEGER  | FK, NOT NULL | Ref: NewsArticleAggregatorSources.id|
| countOfArticlesReceivedFromRequest | INTEGER  | NULL         |                                     |
| countOfArticlesSavedToDbFromRequest| INTEGER  | NULL         |                                     |
| dateStartOfRequest                 | DATEONLY | NULL         |                                     |
| dateEndOfRequest                   | DATEONLY | NULL         |                                     |
| gotResponse                        | BOOLEAN  | NULL         |                                     |
| createdAt, updatedAt               | DATE     | NOT NULL     | Timestamps                          |

### NewsArticleAggregatorSources

News API and RSS feed sources configuration.

| Column              | Type    | Constraints      | Notes                |
| ------------------- | ------- | ---------------- | -------------------- |
| id                  | INTEGER | PK               |                      |
| nameOfOrg           | STRING  | NULL             | Organization name    |
| url                 | STRING  | NULL             | Base URL             |
| apiKey              | STRING  | NULL             | API key              |
| isApi               | BOOLEAN | DEFAULT false    | Is API source        |
| isRss               | BOOLEAN | DEFAULT false    | Is RSS source        |
| createdAt, updatedAt| DATE    | NOT NULL         | Timestamps           |

### WebsiteDomains

Website domains for filtering news sources.

| Column                 | Type    | Constraints      | Notes                    |
| ---------------------- | ------- | ---------------- | ------------------------ |
| id                     | INTEGER | PK               |                          |
| name                   | STRING  | NOT NULL         | Domain name              |
| isArchived             | BOOLEAN | DEFAULT false    |                          |
| isArchievedNewsDataIo  | BOOLEAN | DEFAULT false    | Archived for NewsData.io |
| createdAt, updatedAt   | DATE    | NOT NULL         | Timestamps               |

## AI & Categorization

### ArtificialIntelligences

AI models configuration.

| Column               | Type    | Constraints  | Notes                  |
| -------------------- | ------- | ------------ | ---------------------- |
| id                   | INTEGER | PK           |                        |
| name                 | STRING  | NOT NULL     | Model name             |
| description          | STRING  | NULL         |                        |
| huggingFaceModelName | STRING  | NULL         | HuggingFace model ID   |
| huggingFaceModelType | STRING  | NULL         | Model type/category    |
| createdAt, updatedAt | DATE    | NOT NULL     | Timestamps             |

### EntityWhoFoundArticles

Tracks which entity (user or aggregator) found an article.

| Column                        | Type    | Constraints | Notes                               |
| ----------------------------- | ------- | ----------- | ----------------------------------- |
| id                            | INTEGER | PK          |                                     |
| userId                        | INTEGER | FK, NULL    | Ref: Users.id                       |
| newsArticleAggregatorSourceId | INTEGER | FK, NULL    | Ref: NewsArticleAggregatorSources.id|
| createdAt, updatedAt          | DATE    | NOT NULL    | Timestamps                          |

### EntityWhoCategorizedArticles

Tracks which entity (user or AI) categorized an article.

| Column                   | Type    | Constraints | Notes                           |
| ------------------------ | ------- | ----------- | ------------------------------- |
| id                       | INTEGER | PK          |                                 |
| userId                   | INTEGER | FK, NULL    | Ref: Users.id                   |
| artificialIntelligenceId | INTEGER | FK, NULL    | Ref: ArtificialIntelligences.id |
| createdAt, updatedAt     | DATE    | NOT NULL    | Timestamps                      |

### Keywords

Keyword definitions for article categorization.

| Column              | Type    | Constraints      | Notes        |
| ------------------- | ------- | ---------------- | ------------ |
| id                  | INTEGER | PK               |              |
| keyword             | STRING  | NOT NULL         |              |
| category            | STRING  | NULL             |              |
| isArchived          | BOOLEAN | DEFAULT false    |              |
| createdAt, updatedAt| DATE    | NOT NULL         | Timestamps   |

## Reports

### Reports

Client report generation tracking.

| Column                | Type    | Constraints  | Notes               |
| --------------------- | ------- | ------------ | ------------------- |
| id                    | INTEGER | PK           |                     |
| dateSubmittedToClient | DATE    | NULL         |                     |
| nameCrFormat          | STRING  | NULL         | CR format filename  |
| nameZipFile           | STRING  | NULL         | Zip archive name    |
| userId                | INTEGER | FK, NOT NULL | Ref: Users.id       |
| createdAt, updatedAt  | DATE    | NOT NULL     | Timestamps          |

## Junction Tables

### ArticleStateContracts

Links Articles to States (many-to-many).

| Column              | Type    | Constraints  | Notes          |
| ------------------- | ------- | ------------ | -------------- |
| id                  | INTEGER | PK           |                |
| articleId           | INTEGER | FK, NOT NULL | Ref: Articles.id|
| stateId             | INTEGER | FK, NOT NULL | Ref: States.id |
| createdAt, updatedAt| DATE    | NOT NULL     | Timestamps     |

### ArticleKeywordContracts

Links Articles to categorization entities with keyword rankings.

| Column                 | Type    | Constraints  | Notes                             |
| ---------------------- | ------- | ------------ | --------------------------------- |
| id                     | INTEGER | PK           |                                   |
| articleId              | INTEGER | FK, NOT NULL | Ref: Articles.id                  |
| entityWhoCategorizesId | INTEGER | FK, NOT NULL | Ref: EntityWhoCategorizedArticles.id|
| ranking                | FLOAT   | NOT NULL     | Keyword relevance score           |
| createdAt, updatedAt   | DATE    | NOT NULL     | Timestamps                        |

### ArticleReportContracts

Links Articles to Reports (many-to-many).

| Column                         | Type    | Constraints      | Notes             |
| ------------------------------ | ------- | ---------------- | ----------------- |
| id                             | INTEGER | PK               |                   |
| reportId                       | INTEGER | FK, NOT NULL     | Ref: Reports.id   |
| articleId                      | INTEGER | FK, NOT NULL     | Ref: Articles.id  |
| articleReferenceNumberInReport | STRING  | NULL             |                   |
| articleAcceptedByCpsc          | BOOLEAN | DEFAULT true     | CPSC acceptance   |
| articleRejectionReason         | STRING  | NULL             |                   |
| createdAt, updatedAt           | DATE    | NOT NULL         | Timestamps        |

### ArticleEntityWhoCategorizedArticleContracts

Links Articles to categorization entities with keyword metadata.

| Column                 | Type    | Constraints  | Notes                             |
| ---------------------- | ------- | ------------ | --------------------------------- |
| id                     | INTEGER | PK           |                                   |
| articleId              | INTEGER | FK, NOT NULL | Ref: Articles.id                  |
| entityWhoCategorizesId | INTEGER | FK, NOT NULL | Ref: EntityWhoCategorizedArticles.id|
| keyword                | STRING  | NULL         | Detected keyword                  |
| keywordRating          | FLOAT   | NULL         | Keyword confidence score          |
| createdAt, updatedAt   | DATE    | NOT NULL     | Timestamps                        |

**Note**: Unique index on (articleId, entityWhoCategorizesId, keyword).

### ArticleEntityWhoCategorizedArticleContracts02

Links Articles to categorization entities with flexible key-value storage.

| Column                 | Type    | Constraints  | Notes                             |
| ---------------------- | ------- | ------------ | --------------------------------- |
| id                     | INTEGER | PK           |                                   |
| articleId              | INTEGER | FK, NOT NULL | Ref: Articles.id                  |
| entityWhoCategorizesId | INTEGER | FK, NOT NULL | Ref: EntityWhoCategorizedArticles.id|
| key                    | STRING  | NULL         | Metadata key                      |
| valueString            | STRING  | NULL         | String value                      |
| valueNumber            | FLOAT   | NULL         | Numeric value                     |
| valueBoolean           | BOOLEAN | NULL         | Boolean value                     |
| createdAt, updatedAt   | DATE    | NOT NULL     | Timestamps                        |

**Note**: Unique index on (articleId, entityWhoCategorizesId, key).

### NewsApiRequestWebsiteDomainContracts

Links NewsApiRequests to WebsiteDomains (many-to-many).

| Column                        | Type    | Constraints         | Notes                  |
| ----------------------------- | ------- | ------------------- | ---------------------- |
| id                            | INTEGER | PK                  |                        |
| newsApiRequestId              | INTEGER | FK, NULL            | Ref: NewsApiRequests.id|
| websiteDomainId               | INTEGER | FK, NULL            | Ref: WebsiteDomains.id |
| includedOrExcludedFromRequest | STRING  | DEFAULT "included"  | Filter type            |
| createdAt, updatedAt          | DATE    | NOT NULL            | Timestamps             |

### NewsArticleAggregatorSourceStateContracts

Links NewsArticleAggregatorSources to States (many-to-many).

| Column                        | Type    | Constraints  | Notes                               |
| ----------------------------- | ------- | ------------ | ----------------------------------- |
| id                            | INTEGER | PK           |                                     |
| stateId                       | INTEGER | FK, NOT NULL | Ref: States.id                      |
| newsArticleAggregatorSourceId | INTEGER | FK, NOT NULL | Ref: NewsArticleAggregatorSources.id|
| createdAt, updatedAt          | DATE    | NOT NULL     | Timestamps                          |
