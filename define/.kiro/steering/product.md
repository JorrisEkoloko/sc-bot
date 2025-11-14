# Product Overview

## Crypto Intelligence System

A real-time cryptocurrency signal monitoring and analysis system that tracks Telegram channels for crypto mentions, extracts token addresses, monitors price performance, and provides intelligence-driven insights.

## Core Functionality

- **Real-time Monitoring**: Tracks 50+ Telegram channels for crypto signals
- **Multi-chain Support**: Ethereum and Solana address extraction (95% accuracy)
- **Price Intelligence**: Multi-API price fetching with intelligent failover (CoinGecko, Birdeye, Moralis, DexScreener)
- **Performance Tracking**: 7-day ATH tracking with 2-hour update cycles
- **Intelligence Layer**: Market cap analysis, channel reputation scoring, holistic signal confidence
- **Data Output**: Dual CSV + Google Sheets output with 26-column format and conditional formatting

## Key Features

- **HDRB Model**: Research-compliant scoring system with IEEE validation
- **Outcome-based Learning**: Channel reputation updates based on actual trading results
- **99% API Reduction**: Targeted ATH checking only for mentioned coins
- **Multi-tier Analysis**: Market cap classification (micro/small/large) with risk assessment

## Current State

This repository contains comprehensive documentation for a **system rebuild** that simplifies the architecture from 4,135+ lines in main.py to <500 lines while preserving 100% of functionality. The rebuild reduces 24+ directories to 6-8 focused components and 100+ files to 19 core modules.

## Success Metrics

- 88% code reduction in main orchestration
- 100% functional preservation
- Production-ready with comprehensive error handling
- Scalable to 50+ channels without degradation
