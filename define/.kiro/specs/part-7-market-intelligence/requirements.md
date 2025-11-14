# Requirements Document - Part 7: Market Intelligence & Tier Classification

## Introduction

Part 7 adds market intelligence capabilities to the crypto intelligence system by analyzing market capitalization data, classifying tokens into risk tiers, and providing multi-factor risk assessments. This builds on Part 3's price fetching to provide deeper market context and risk analysis for investment decisions.

## Glossary

- **Market Analyzer**: Component that analyzes market cap data and classifies tokens into tiers
- **Market Cap Tier**: Classification of token size (large/mid/small/micro-cap)
- **Risk Assessment**: Multi-factor analysis combining market cap, liquidity, volume, and volatility
- **Liquidity Ratio**: Ratio of liquidity to market cap (liquidity_usd / market_cap)
- **Volume Ratio**: Ratio of 24h volume to market cap (volume_24h / market_cap)
- **Risk Score**: Weighted numerical score (0-100) indicating investment risk
- **Risk Level**: Categorical risk classification (low/moderate/high/extreme)
- **Data Completeness**: Percentage of risk factors available for analysis
- **Graceful Degradation**: Ability to provide partial analysis when data is incomplete

## Requirements

### Requirement 1: Market Cap Tier Classification

**User Story:** As a system operator, I want tokens classified into market cap tiers, so that I can quickly assess token size and maturity.

#### Acceptance Criteria

1. WHEN PriceData contains market_cap value, THE Market Analyzer SHALL classify the token into a tier
2. WHEN market_cap is >= $1,000,000,000, THE Market Analyzer SHALL classify as "large-cap"
3. WHEN market_cap is >= $100,000,000 and < $1,000,000,000, THE Market Analyzer SHALL classify as "mid-cap"
4. WHEN market_cap is >= $10,000,000 and < $100,000,000, THE Market Analyzer SHALL classify as "small-cap"
5. WHEN market_cap is < $10,000,000, THE Market Analyzer SHALL classify as "micro-cap"
6. WHEN market_cap is None or unavailable, THE Market Analyzer SHALL classify as "unknown"
7. WHEN classification completes, THE Market Analyzer SHALL return both tier code and human-readable description

### Requirement 2: Liquidity Risk Analysis

**User Story:** As a system operator, I want liquidity analyzed relative to market cap, so that I can assess token tradability and exit risk.

#### Acceptance Criteria

1. WHEN PriceData contains both liquidity_usd and market_cap, THE Market Analyzer SHALL calculate liquidity ratio
2. WHEN liquidity ratio is calculated, THE Market Analyzer SHALL divide liquidity_usd by market_cap
3. WHEN liquidity ratio is >= 0.10 (10%), THE Market Analyzer SHALL classify liquidity risk as "low"
4. WHEN liquidity ratio is >= 0.05 and < 0.10 (5-10%), THE Market Analyzer SHALL classify liquidity risk as "moderate"
5. WHEN liquidity ratio is < 0.05 (5%), THE Market Analyzer SHALL classify liquidity risk as "high"
6. WHEN liquidity_usd or market_cap is unavailable, THE Market Analyzer SHALL skip liquidity analysis
7. WHEN liquidity analysis completes, THE Market Analyzer SHALL include liquidity_ratio in output

### Requirement 3: Volume Risk Analysis

**User Story:** As a system operator, I want trading volume analyzed relative to market cap, so that I can assess market activity and price manipulation risk.

#### Acceptance Criteria

1. WHEN PriceData contains both volume_24h and market_cap, THE Market Analyzer SHALL calculate volume ratio
2. WHEN volume ratio is calculated, THE Market Analyzer SHALL divide volume_24h by market_cap
3. WHEN volume ratio is >= 0.20 (20%), THE Market Analyzer SHALL classify volume risk as "low"
4. WHEN volume ratio is >= 0.05 and < 0.20 (5-20%), THE Market Analyzer SHALL classify volume risk as "moderate"
5. WHEN volume ratio is < 0.05 (5%), THE Market Analyzer SHALL classify volume risk as "high"
6. WHEN volume_24h or market_cap is unavailable, THE Market Analyzer SHALL skip volume analysis
7. WHEN volume analysis completes, THE Market Analyzer SHALL include volume_ratio in output

### Requirement 4: Volatility Risk Analysis

**User Story:** As a system operator, I want price volatility analyzed, so that I can assess short-term price stability risk.

#### Acceptance Criteria

1. WHEN PriceData contains price_change_24h, THE Market Analyzer SHALL analyze volatility
2. WHEN absolute price_change_24h is < 10%, THE Market Analyzer SHALL classify volatility risk as "low"
3. WHEN absolute price_change_24h is >= 10% and < 30%, THE Market Analyzer SHALL classify volatility risk as "moderate"
4. WHEN absolute price_change_24h is >= 30%, THE Market Analyzer SHALL classify volatility risk as "high"
5. WHEN price_change_24h is unavailable, THE Market Analyzer SHALL skip volatility analysis
6. WHEN volatility analysis completes, THE Market Analyzer SHALL include volatility_risk in output

### Requirement 5: Multi-Factor Risk Scoring

**User Story:** As a system operator, I want a holistic risk score combining multiple factors, so that I can make informed investment decisions.

#### Acceptance Criteria

1. WHEN Market Analyzer performs analysis, THE Market Analyzer SHALL combine all available risk factors
2. WHEN calculating risk score, THE Market Analyzer SHALL weight tier risk at 40%
3. WHEN calculating risk score, THE Market Analyzer SHALL weight liquidity risk at 30%
4. WHEN calculating risk score, THE Market Analyzer SHALL weight volume risk at 20%
5. WHEN calculating risk score, THE Market Analyzer SHALL weight volatility risk at 10%
6. WHEN risk factors are missing, THE Market Analyzer SHALL normalize weights based on available factors
7. WHEN risk score is calculated, THE Market Analyzer SHALL convert to 0-100 scale
8. WHEN risk score is 0-25, THE Market Analyzer SHALL classify as "low" risk
9. WHEN risk score is 26-50, THE Market Analyzer SHALL classify as "moderate" risk
10. WHEN risk score is 51-75, THE Market Analyzer SHALL classify as "high" risk
11. WHEN risk score is 76-100, THE Market Analyzer SHALL classify as "extreme" risk

### Requirement 6: Graceful Degradation

**User Story:** As a system operator, I want partial analysis when data is incomplete, so that I always get maximum insight from available data.

#### Acceptance Criteria

1. WHEN market_cap is unavailable, THE Market Analyzer SHALL still attempt liquidity and volume analysis if data exists
2. WHEN only 1 risk factor is available, THE Market Analyzer SHALL calculate risk score using that factor at 100% weight
3. WHEN multiple factors are available, THE Market Analyzer SHALL calculate data_completeness percentage
4. WHEN data_completeness is calculated, THE Market Analyzer SHALL divide available factors by 4 (total possible factors)
5. WHEN analysis completes, THE Market Analyzer SHALL list which factors were used in calculation
6. WHEN no risk factors are available, THE Market Analyzer SHALL return risk_level as "unknown"
7. WHEN partial data exists, THE Market Analyzer SHALL include data_completeness in output

### Requirement 7: Integration with Price Engine

**User Story:** As a system operator, I want market intelligence automatically added to price data, so that enriched data flows through the pipeline seamlessly.

#### Acceptance Criteria

1. WHEN Price Engine fetches price data, THE Price Engine SHALL call Market Analyzer for enrichment
2. WHEN Market Analyzer enrichment completes, THE Price Engine SHALL add market intelligence fields to PriceData
3. WHEN enrichment fails, THE Price Engine SHALL log error and continue with price data only
4. WHEN enrichment succeeds, THE Price Engine SHALL cache enriched PriceData
5. WHEN cached data is retrieved, THE Price Engine SHALL return cached market intelligence without recalculation

### Requirement 8: Data Output Extension

**User Story:** As a system operator, I want market intelligence included in output tables, so that I can analyze risk in CSV and Google Sheets.

#### Acceptance Criteria

1. WHEN TOKEN_PRICES table is defined, THE Data Output SHALL include market_tier column
2. WHEN TOKEN_PRICES table is defined, THE Data Output SHALL include risk_level column
3. WHEN TOKEN_PRICES table is defined, THE Data Output SHALL include risk_score column
4. WHEN TOKEN_PRICES table is defined, THE Data Output SHALL include liquidity_ratio column
5. WHEN TOKEN_PRICES table is defined, THE Data Output SHALL include volume_ratio column
6. WHEN TOKEN_PRICES table is defined, THE Data Output SHALL include data_completeness column
7. WHEN writing to TOKEN_PRICES, THE Data Output SHALL populate market intelligence columns from PriceData
8. WHEN market intelligence is unavailable, THE Data Output SHALL write empty string or null values

### Requirement 9: Performance and Efficiency

**User Story:** As a system operator, I want market intelligence analysis to be fast, so that it doesn't slow down the pipeline.

#### Acceptance Criteria

1. WHEN Market Analyzer performs tier classification, THE Market Analyzer SHALL complete within 1 millisecond
2. WHEN Market Analyzer performs full risk assessment, THE Market Analyzer SHALL complete within 5 milliseconds
3. WHEN Market Analyzer is called repeatedly, THE Market Analyzer SHALL not cache results (Price Engine handles caching)
4. WHEN Market Analyzer encounters errors, THE Market Analyzer SHALL fail fast and return partial results

### Requirement 10: Logging and Transparency

**User Story:** As a system operator, I want market intelligence decisions logged, so that I can audit and debug classifications.

#### Acceptance Criteria

1. WHEN Market Analyzer classifies a tier, THE Market Analyzer SHALL log tier and market cap value
2. WHEN Market Analyzer calculates risk score, THE Market Analyzer SHALL log which factors were used
3. WHEN Market Analyzer encounters missing data, THE Market Analyzer SHALL log which fields are unavailable
4. WHEN Market Analyzer completes analysis, THE Market Analyzer SHALL log data_completeness percentage
5. WHEN Market Analyzer fails, THE Market Analyzer SHALL log error with context
