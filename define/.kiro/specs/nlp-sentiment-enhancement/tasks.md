# Implementation Plan

- [x] 1. Setup and Configuration

  - Create configuration dataclass for sentiment settings
  - Add environment variables for NLP model configuration
  - Add crypto vocabulary constants to sentiment analyzer
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 2. Enhance Pattern Matcher

  - [x] 2.1 Add crypto-specific positive vocabulary (15 terms)

    - Add WAGMI, GM, LFG, degen, ape, diamond hands, hodl, alpha, based, ser, fren, ngmi, chad, whale, moonshot
    - _Requirements: 3.1, 3.2, 3.4_

  - [x] 2.2 Add crypto-specific negative vocabulary (15 terms)

    - Add ngmi, paper hands, rekt, fud, jeet, rugged, honeypot, bagholder, cope, salty, exit liquidity, vaporware, shitcoin, pump and dump, wash trading
    - _Requirements: 3.1, 3.3, 3.4_

  - [x] 2.3 Implement confidence scoring

    - Calculate confidence based on match strength and signal clarity
    - Return confidence score with sentiment result
    - _Requirements: 6.3, 1.2_

  - [x] 2.4 Implement conflicting signal detection

    - Detect when both positive and negative patterns match
    - Flag as low confidence when signals conflict
    - _Requirements: 1.3_

- [x] 3. Implement Confidence Evaluator

  - [x] 3.1 Create confidence threshold logic

    - Check if pattern confidence exceeds threshold (0.7)
    - Route to NLP if confidence is low
    - _Requirements: 1.2, 1.3, 5.3_

  - [x] 3.2 Implement negation detection

    - Detect negation keywords (not, don't, never, no)
    - Check 3-word context window after negation
    - Flag for NLP processing when negation found
    - _Requirements: 2.1_

  - [x] 3.3 Implement sarcasm detection

    - Detect quotes around positive words
    - Detect sarcasm emojis (🙄, 🤡)
    - Detect excessive punctuation (!!!, ???)
    - Flag for NLP processing when sarcasm indicators found
    - _Requirements: 2.2_

  - [x] 3.4 Implement routing decision logic

    - Combine all confidence checks
    - Return boolean decision for NLP invocation
    - _Requirements: 1.2, 1.3, 1.4_

- [x] 4. Implement NLP Analyzer

  - [x] 4.1 Create NLP analyzer class

    - Initialize with model name and device configuration
    - Implement lazy model loading
    - Cache model in memory after first load
    - _Requirements: 4.3, 5.1, 5.5_

  - [x] 4.2 Implement model loading with error handling

    - Download model from Hugging Face Hub
    - Cache model locally in configured directory
    - Handle download failures with retry logic
    - Fall back to pattern-only if model unavailable
    - _Requirements: 5.4, 8.1, 8.3_

  - [x] 4.3 Implement text preprocessing

    - Replace @mentions with @user token
    - Replace URLs with http token
    - Normalize whitespace
    - Truncate to 512 tokens max
    - _Requirements: 2.5_

  - [x] 4.4 Implement NLP inference

    - Run transformer model inference
    - Convert model output to sentiment label and score
    - Map confidence scores to -1.0 to +1.0 range
    - Handle inference errors with fallback
    - _Requirements: 1.4, 2.1, 2.2, 2.3, 2.4, 2.5, 8.2_

  - [x] 4.5 Implement GPU acceleration support

    - Detect GPU availability
    - Use GPU device if available and configured
    - Fall back to CPU if GPU unavailable
    - _Requirements: 5.5_

  - [x] 4.6 Implement batch processing

    - Support processing multiple messages in batch
    - Optimize inference for batch mode
    - _Requirements: 4.5_

- [ ] 5. Implement Result Merger

  - [x] 5.1 Create SentimentResult dataclass

    - Define all result fields (label, score, confidence, method, etc.)
    - Include pattern and NLP results
    - Add metadata fields (processing time, flags)
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x] 5.2 Implement result formatting

    - Convert internal results to SentimentResult format
    - Add method flag (pattern/nlp/fallback)
    - Calculate and include processing time
    - _Requirements: 6.4, 9.3_

  - [x] 5.3 Implement backward compatible interface

    - Maintain existing analyze(text) method signature
    - Return simple (label, score) tuple
    - Add new analyze_detailed(text) method for full results
    - _Requirements: 7.1, 7.2, 7.4_

- [x] 6. Implement Hybrid System Integration

  - [x] 6.1 Create main analyze method

    - Call pattern matcher first
    - Evaluate confidence
    - Route to NLP if needed
    - Merge and return results
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 6.2 Implement fallback mechanism

    - Catch NLP errors and fall back to pattern result
    - Log fallback events with reason
    - Set method flag to 'fallback'
    - _Requirements: 1.5, 8.1, 8.2_

  - [x] 6.3 Implement performance optimization

    - Ensure pattern-only path remains fast (<5ms)
    - Cache NLP model to avoid reload overhead
    - Track and optimize NLP invocation rate
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 7. Add Configuration Management

  - [x] 7.1 Create SentimentConfig dataclass

    - Define all configuration parameters
    - Set sensible defaults
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 7.2 Add environment variable loading

    - Load NLP settings from .env file
    - Support disabling NLP enhancement
    - Support model selection
    - _Requirements: 5.1, 5.2_

  - [x] 7.3 Add configuration validation

    - Validate model name format
    - Validate threshold ranges (0.0-1.0)
    - Validate device selection (cpu/gpu)
    - _Requirements: 5.1_

- [x] 8. Implement Error Handling

  - [x] 8.1 Add model loading error handling

    - Catch download failures
    - Retry once with exponential backoff
    - Log errors with details
    - Fall back to pattern-only mode
    - _Requirements: 8.1, 8.3_

  - [x] 8.2 Add inference error handling

    - Catch inference exceptions
    - Log error with truncated input
    - Return pattern-based fallback
    - Never raise unhandled exceptions
    - _Requirements: 8.2, 8.4_

  - [x] 8.3 Add timeout handling

    - Set 5-second timeout for NLP inference
    - Return pattern result on timeout
    - Log slow inference warnings
    - _Requirements: 8.4_

  - [x] 8.4 Add out-of-memory handling

    - Catch OOM errors
    - Reduce batch size
    - Clear model cache
    - Fall back to CPU if on GPU
    - _Requirements: 8.4_

- [ ] 9. Add Monitoring and Logging

  - [x] 9.1 Add classification method logging

    - Log pattern vs NLP usage at DEBUG level
    - Include confidence scores in logs
    - _Requirements: 9.1_

  - [x] 9.2 Add performance metrics logging

    - Track NLP inference time
    - Log slow inference warnings (>200ms)
    - _Requirements: 9.3_

  - [x] 9.3 Add periodic statistics logging

    - Track pattern match rate
    - Track NLP invocation rate
    - Log stats every 100 messages
    - _Requirements: 9.2_

  - [x] 9.4 Add fallback event logging

    - Log when falling back from NLP to pattern
    - Include reason for fallback
    - _Requirements: 9.5_

  - [x] 9.5 Implement metrics exposure

    - Expose pattern match rate metric
    - Expose NLP invocation rate metric
    - Expose average inference time metric
    - _Requirements: 9.4_

- [ ] 10. Create Test Suite

  - [x] 10.1 Create pattern matcher tests

    - Test existing positive/negative/neutral cases
    - Test new crypto vocabulary
    - Test confidence calculation
    - Test conflicting signal detection
    - _Requirements: 10.1_

  - [x] 10.2 Create context understanding tests

    - Test negation handling (20 cases)
    - Test sarcasm detection (10 cases)
    - Test conditional sentiment (10 cases)
    - _Requirements: 10.2_

  - [x] 10.3 Create crypto language tests

    - Test crypto-specific positive terms (15 cases)
    - Test crypto-specific negative terms (15 cases)
    - Test context-dependent terms (10 cases)
    - _Requirements: 10.3_

  - [x] 10.4 Create NLP analyzer tests

    - Test model loading and caching
    - Test preprocessing correctness
    - Test inference accuracy
    - Test error handling and fallback
    - _Requirements: 10.1_

  - [x] 10.5 Create integration tests

    - Test end-to-end sentiment analysis
    - Test hybrid system routing
    - Test backward compatibility
    - _Requirements: 10.1_

  - [ ]\* 10.6 Create performance benchmark tests

    - Benchmark pattern-only speed (<5ms)
    - Benchmark NLP inference speed (<200ms CPU)
    - Benchmark hybrid average speed (<50ms)
    - Verify pattern match rate (>80%)
    - _Requirements: 10.5_

  - [ ]\* 10.7 Create accuracy validation tests
    - Test on 500-message labeled dataset
    - Verify pattern-only accuracy (70% overall)
    - Verify hybrid accuracy (85% overall)
    - Verify no regression on clear cases
    - _Requirements: 10.4_

- [ ] 11. Update Documentation

  - [ ] 11.1 Update sentiment analyzer docstrings

    - Document new methods and parameters
    - Add usage examples
    - Document configuration options
    - _Requirements: 7.1, 7.2_

  - [ ] 11.2 Create configuration guide

    - Document all environment variables
    - Provide configuration examples
    - Explain model selection
    - _Requirements: 5.1, 5.2_

  - [ ] 11.3 Create troubleshooting guide
    - Document common errors and solutions
    - Explain fallback behavior
    - Provide performance tuning tips
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 12. Update Dependencies

  - [x] 12.1 Add transformers library to requirements.txt

    - Add transformers==4.35.0
    - Add torch==2.1.0
    - Add sentencepiece==0.1.99
    - _Requirements: 4.1_

  - [x] 12.2 Update .env.example

    - Add sentiment configuration variables
    - Add comments explaining each setting
    - _Requirements: 5.1, 5.2_
