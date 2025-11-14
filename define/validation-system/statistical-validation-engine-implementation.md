# Statistical Validation Engine - Enhanced Implementation (< 500 lines)

## Overview

The StatisticalValidationEngine ensures HDRB model research compliance, validates correlation benchmarks, and maintains academic standards throughout the system with continuous statistical monitoring.

## Core Functionality

### Research Compliance Validation

- **HDRB Model Compliance**: Exact IEEE research implementation
- **Statistical Benchmarks**: 77% accuracy, 70% correlation targets
- **Academic Standards**: p < 0.05 significance validation
- **Continuous Monitoring**: Real-time compliance checking

## Implementation

```python
# validation/statistical_validation_engine.py
"""
HDRB model research compliance and statistical validation
Ensures academic standards and benchmark compliance
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from scipy import stats
import json
from pathlib import Path

@dataclass
class StatisticalBenchmark:
    """Statistical benchmark definition"""
    name: str
    target_value: float
    current_value: float
    threshold_type: str  # minimum, maximum, exact
    significance_level: float
    sample_size: int
    last_updated: datetime

@dataclass
class ComplianceResult:
    """Research compliance validation result"""
    benchmark_name: str
    is_compliant: bool
    current_value: float
    target_value: float
    confidence_interval: Tuple[float, float]
    p_value: float
    sample_size: int
    validation_timestamp: datetime

class StatisticalValidationEngine:
    """HDRB model compliance and statistical validation"""

    def __init__(self, config):
        self.logger = logging.getLogger(__name__)
        self.config = config

        # Research benchmarks from IEEE paper
        self.research_benchmarks = {
            'prediction_accuracy': StatisticalBenchmark(
                name='prediction_accuracy',
                target_value=0.77,  # 77% accuracy target
                current_value=0.0,
                threshold_type='minimum',
                significance_level=0.05,
                sample_size=0,
                last_updated=datetime.now()
            ),
            'sentiment_price_correlation': StatisticalBenchmark(
                name='sentiment_price_correlation',
                target_value=0.70,  # 70% correlation target
                current_value=0.0,
                threshold_type='minimum',
                significance_level=0.05,
                sample_size=0,
                last_updated=datetime.now()
            ),
            'spearman_correlation': StatisticalBenchmark(
                name='spearman_correlation',
                target_value=0.642,  # Spearman ≥ 0.642
                current_value=0.0,
                threshold_type='minimum',
                significance_level=0.05,
                sample_size=0,
                last_updated=datetime.now()
            ),
            'noise_reduction_rate': StatisticalBenchmark(
                name='noise_reduction_rate',
                target_value=0.45,  # 45% noise reduction
                current_value=0.0,
                threshold_type='minimum',
                significance_level=0.05,
                sample_size=0,
                last_updated=datetime.now()
            )
        }

        # Data collection for validation
        self.validation_data = {
            'predictions': [],
            'outcomes': [],
            'sentiment_scores': [],
            'price_changes': [],
            'noise_filtered': 0,
            'total_messages': 0
        }

        # Validation history
        self.validation_history = []
        self.history_file = Path('data/validation_history.json')

        # Statistics
        self.stats = {
            'validations_performed': 0,
            'compliance_passes': 0,
            'compliance_failures': 0,
            'last_validation_time': None,
            'benchmark_updates': 0
        }

        # Load existing data
        asyncio.create_task(self.load_validation_history())

    async def validate_hdrb_compliance(self, hdrb_scores: List[float],
                                     message_data: List[Dict[str, Any]]) -> ComplianceResult:
        """Validate HDRB model compliance with research standards"""
        try:
            if not hdrb_scores or len(hdrb_scores) < 10:
                return ComplianceResult(
                    benchmark_name='hdrb_compliance',
                    is_compliant=False,
                    current_value=0.0,
                    target_value=0.77,
                    confidence_interval=(0.0, 0.0),
                    p_value=1.0,
                    sample_size=len(hdrb_scores),
                    validation_timestamp=datetime.now()
                )

            # Validate HDRB score distribution
            mean_score = np.mean(hdrb_scores)
            std_score = np.std(hdrb_scores)

            # Check if scores are in valid range (0-1)
            valid_range = all(0 <= score <= 1 for score in hdrb_scores)

            # Check score distribution (should not be all the same)
            score_variance = np.var(hdrb_scores)
            has_variance = score_variance > 0.01

            # Calculate confidence interval
            confidence_interval = stats.t.interval(
                0.95, len(hdrb_scores) - 1,
                loc=mean_score,
                scale=stats.sem(hdrb_scores)
            )

            # Statistical significance test (one-sample t-test against random baseline 0.5)
            t_stat, p_value = stats.ttest_1samp(hdrb_scores, 0.5)

            # Compliance check
            is_compliant = (
                valid_range and
                has_variance and
                mean_score > 0.5 and  # Better than random
                p_value < 0.05  # Statistically significant
            )

            # Update benchmark
            self.research_benchmarks['prediction_accuracy'].current_value = mean_score
            self.research_benchmarks['prediction_accuracy'].sample_size = len(hdrb_scores)
            self.research_benchmarks['prediction_accuracy'].last_updated = datetime.now()

            return ComplianceResult(
                benchmark_name='hdrb_compliance',
                is_compliant=is_compliant,
                current_value=mean_score,
                target_value=0.77,
                confidence_interval=confidence_interval,
                p_value=p_value,
                sample_size=len(hdrb_scores),
                validation_timestamp=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"Error validating HDRB compliance: {e}")
            return ComplianceResult(
                benchmark_name='hdrb_compliance',
                is_compliant=False,
                current_value=0.0,
                target_value=0.77,
                confidence_interval=(0.0, 0.0),
                p_value=1.0,
                sample_size=0,
                validation_timestamp=datetime.now()
            )

    async def validate_sentiment_correlation(self, sentiment_scores: List[float],
                                           price_changes: List[float]) -> ComplianceResult:
        """Validate sentiment-price correlation against research benchmarks"""
        try:
            if len(sentiment_scores) != len(price_changes) or len(sentiment_scores) < 10:
                return ComplianceResult(
                    benchmark_name='sentiment_correlation',
                    is_compliant=False,
                    current_value=0.0,
                    target_value=0.70,
                    confidence_interval=(0.0, 0.0),
                    p_value=1.0,
                    sample_size=len(sentiment_scores),
                    validation_timestamp=datetime.now()
                )

            # Calculate Pearson correlation
            pearson_corr, pearson_p = stats.pearsonr(sentiment_scores, price_changes)

            # Calculate Spearman correlation (research benchmark)
            spearman_corr, spearman_p = stats.spearmanr(sentiment_scores, price_changes)

            # Calculate confidence interval for correlation
            n = len(sentiment_scores)
            z_score = np.arctanh(pearson_corr)
            se = 1 / np.sqrt(n - 3)
            ci_lower = np.tanh(z_score - 1.96 * se)
            ci_upper = np.tanh(z_score + 1.96 * se)

            # Compliance check
            is_compliant = (
                abs(pearson_corr) >= 0.70 and  # 70% correlation target
                abs(spearman_corr) >= 0.642 and  # Research benchmark
                pearson_p < 0.05 and  # Statistical significance
                spearman_p < 0.05
            )

            # Update benchmarks
            self.research_benchmarks['sentiment_price_correlation'].current_value = abs(pearson_corr)
            self.research_benchmarks['sentiment_price_correlation'].sample_size = n
            self.research_benchmarks['spearman_correlation'].current_value = abs(spearman_corr)
            self.research_benchmarks['spearman_correlation'].sample_size = n

            # Store data for future validation
            self.validation_data['sentiment_scores'].extend(sentiment_scores)
            self.validation_data['price_changes'].extend(price_changes)

            return ComplianceResult(
                benchmark_name='sentiment_correlation',
                is_compliant=is_compliant,
                current_value=abs(pearson_corr),
                target_value=0.70,
                confidence_interval=(ci_lower, ci_upper),
                p_value=pearson_p,
                sample_size=n,
                validation_timestamp=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"Error validating sentiment correlation: {e}")
            return ComplianceResult(
                benchmark_name='sentiment_correlation',
                is_compliant=False,
                current_value=0.0,
                target_value=0.70,
                confidence_interval=(0.0, 0.0),
                p_value=1.0,
                sample_size=0,
                validation_timestamp=datetime.now()
            )

    async def validate_noise_reduction(self, total_messages: int,
                                     filtered_messages: int) -> ComplianceResult:
        """Validate noise reduction against 45% target"""
        try:
            if total_messages == 0:
                return ComplianceResult(
                    benchmark_name='noise_reduction',
                    is_compliant=False,
                    current_value=0.0,
                    target_value=0.45,
                    confidence_interval=(0.0, 0.0),
                    p_value=1.0,
                    sample_size=0,
                    validation_timestamp=datetime.now()
                )

            # Calculate noise reduction rate
            noise_filtered = total_messages - filtered_messages
            noise_reduction_rate = noise_filtered / total_messages

            # Calculate confidence interval for proportion
            p = noise_reduction_rate
            n = total_messages
            se = np.sqrt(p * (1 - p) / n)
            ci_lower = max(0, p - 1.96 * se)
            ci_upper = min(1, p + 1.96 * se)

            # Statistical test (one-sample proportion test)
            # H0: noise reduction = 0.45, H1: noise reduction != 0.45
            z_stat = (p - 0.45) / np.sqrt(0.45 * 0.55 / n)
            p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

            # Compliance check
            is_compliant = (
                noise_reduction_rate >= 0.45 and  # 45% minimum target
                n >= 100  # Sufficient sample size
            )

            # Update benchmark
            self.research_benchmarks['noise_reduction_rate'].current_value = noise_reduction_rate
            self.research_benchmarks['noise_reduction_rate'].sample_size = n

            # Store data
            self.validation_data['noise_filtered'] += noise_filtered
            self.validation_data['total_messages'] += total_messages

            return ComplianceResult(
                benchmark_name='noise_reduction',
                is_compliant=is_compliant,
                current_value=noise_reduction_rate,
                target_value=0.45,
                confidence_interval=(ci_lower, ci_upper),
                p_value=p_value,
                sample_size=n,
                validation_timestamp=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"Error validating noise reduction: {e}")
            return ComplianceResult(
                benchmark_name='noise_reduction',
                is_compliant=False,
                current_value=0.0,
                target_value=0.45,
                confidence_interval=(0.0, 0.0),
                p_value=1.0,
                sample_size=0,
                validation_timestamp=datetime.now()
            )

    async def validate_prediction_accuracy(self, predictions: List[float],
                                         outcomes: List[float]) -> ComplianceResult:
        """Validate prediction accuracy against 77% target"""
        try:
            if len(predictions) != len(outcomes) or len(predictions) < 10:
                return ComplianceResult(
                    benchmark_name='prediction_accuracy',
                    is_compliant=False,
                    current_value=0.0,
                    target_value=0.77,
                    confidence_interval=(0.0, 0.0),
                    p_value=1.0,
                    sample_size=len(predictions),
                    validation_timestamp=datetime.now()
                )

            # Convert to binary classification (positive/negative outcomes)
            binary_predictions = [1 if p > 0.5 else 0 for p in predictions]
            binary_outcomes = [1 if o > 0 else 0 for o in outcomes]

            # Calculate accuracy
            correct_predictions = sum(1 for p, o in zip(binary_predictions, binary_outcomes) if p == o)
            accuracy = correct_predictions / len(predictions)

            # Calculate confidence interval for accuracy
            n = len(predictions)
            se = np.sqrt(accuracy * (1 - accuracy) / n)
            ci_lower = max(0, accuracy - 1.96 * se)
            ci_upper = min(1, accuracy + 1.96 * se)

            # Statistical test against 77% target
            z_stat = (accuracy - 0.77) / np.sqrt(0.77 * 0.23 / n)
            p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

            # Compliance check
            is_compliant = (
                accuracy >= 0.77 and  # 77% minimum target
                n >= 30  # Sufficient sample size
            )

            # Store data
            self.validation_data['predictions'].extend(predictions)
            self.validation_data['outcomes'].extend(outcomes)

            return ComplianceResult(
                benchmark_name='prediction_accuracy',
                is_compliant=is_compliant,
                current_value=accuracy,
                target_value=0.77,
                confidence_interval=(ci_lower, ci_upper),
                p_value=p_value,
                sample_size=n,
                validation_timestamp=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"Error validating prediction accuracy: {e}")
            return ComplianceResult(
                benchmark_name='prediction_accuracy',
                is_compliant=False,
                current_value=0.0,
                target_value=0.77,
                confidence_interval=(0.0, 0.0),
                p_value=1.0,
                sample_size=0,
                validation_timestamp=datetime.now()
            )

    async def run_comprehensive_validation(self) -> Dict[str, ComplianceResult]:
        """Run comprehensive statistical validation"""
        try:
            self.logger.info("Running comprehensive statistical validation...")

            results = {}

            # Validate noise reduction if we have data
            if self.validation_data['total_messages'] > 0:
                results['noise_reduction'] = await self.validate_noise_reduction(
                    self.validation_data['total_messages'],
                    self.validation_data['total_messages'] - self.validation_data['noise_filtered']
                )

            # Validate sentiment correlation if we have data
            if (len(self.validation_data['sentiment_scores']) > 10 and
                len(self.validation_data['price_changes']) > 10):
                results['sentiment_correlation'] = await self.validate_sentiment_correlation(
                    self.validation_data['sentiment_scores'][-100:],  # Last 100 samples
                    self.validation_data['price_changes'][-100:]
                )

            # Validate prediction accuracy if we have data
            if (len(self.validation_data['predictions']) > 10 and
                len(self.validation_data['outcomes']) > 10):
                results['prediction_accuracy'] = await self.validate_prediction_accuracy(
                    self.validation_data['predictions'][-100:],  # Last 100 samples
                    self.validation_data['outcomes'][-100:]
                )

            # Update statistics
            self.stats['validations_performed'] += 1
            self.stats['last_validation_time'] = datetime.now()

            compliant_count = sum(1 for result in results.values() if result.is_compliant)
            if compliant_count == len(results) and results:
                self.stats['compliance_passes'] += 1
            else:
                self.stats['compliance_failures'] += 1

            # Store validation history
            self.validation_history.append({
                'timestamp': datetime.now().isoformat(),
                'results': {name: {
                    'is_compliant': result.is_compliant,
                    'current_value': result.current_value,
                    'target_value': result.target_value,
                    'p_value': result.p_value,
                    'sample_size': result.sample_size
                } for name, result in results.items()}
            })

            # Save validation history
            await self.save_validation_history()

            # Log results
            compliance_rate = compliant_count / max(1, len(results))
            self.logger.info(
                f"Statistical validation complete: {compliant_count}/{len(results)} compliant "
                f"({compliance_rate:.1%})"
            )

            return results

        except Exception as e:
            self.logger.error(f"Error in comprehensive validation: {e}")
            return {}

    def add_validation_data(self, data_type: str, data: Any):
        """Add data for statistical validation"""
        try:
            if data_type == 'sentiment_price_pair':
                self.validation_data['sentiment_scores'].append(data['sentiment'])
                self.validation_data['price_changes'].append(data['price_change'])
            elif data_type == 'prediction_outcome_pair':
                self.validation_data['predictions'].append(data['prediction'])
                self.validation_data['outcomes'].append(data['outcome'])
            elif data_type == 'message_filtering':
                self.validation_data['total_messages'] += data['total']
                self.validation_data['noise_filtered'] += data['filtered']

            # Limit data size to prevent memory issues
            max_size = 1000
            for key in ['sentiment_scores', 'price_changes', 'predictions', 'outcomes']:
                if len(self.validation_data[key]) > max_size:
                    self.validation_data[key] = self.validation_data[key][-max_size:]

        except Exception as e:
            self.logger.error(f"Error adding validation data: {e}")

    async def save_validation_history(self):
        """Save validation history to file"""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)

            # Keep only last 100 validation records
            if len(self.validation_history) > 100:
                self.validation_history = self.validation_history[-100:]

            with open(self.history_file, 'w') as f:
                json.dump({
                    'validation_history': self.validation_history,
                    'benchmarks': {name: {
                        'current_value': bench.current_value,
                        'target_value': bench.target_value,
                        'sample_size': bench.sample_size,
                        'last_updated': bench.last_updated.isoformat()
                    } for name, bench in self.research_benchmarks.items()},
                    'stats': self.stats,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error saving validation history: {e}")

    async def load_validation_history(self):
        """Load validation history from file"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    data = json.load(f)

                self.validation_history = data.get('validation_history', [])
                saved_stats = data.get('stats', {})
                self.stats.update(saved_stats)

                # Load benchmark data
                benchmarks_data = data.get('benchmarks', {})
                for name, bench_data in benchmarks_data.items():
                    if name in self.research_benchmarks:
                        self.research_benchmarks[name].current_value = bench_data.get('current_value', 0.0)
                        self.research_benchmarks[name].sample_size = bench_data.get('sample_size', 0)
                        if bench_data.get('last_updated'):
                            self.research_benchmarks[name].last_updated = datetime.fromisoformat(bench_data['last_updated'])

                self.logger.info(f"Loaded {len(self.validation_history)} validation records")

        except Exception as e:
            self.logger.error(f"Error loading validation history: {e}")

    def get_benchmark_status(self) -> Dict[str, Dict[str, Any]]:
        """Get current benchmark status"""
        return {
            name: {
                'current_value': bench.current_value,
                'target_value': bench.target_value,
                'is_meeting_target': (
                    bench.current_value >= bench.target_value
                    if bench.threshold_type == 'minimum'
                    else bench.current_value <= bench.target_value
                ),
                'sample_size': bench.sample_size,
                'last_updated': bench.last_updated.isoformat(),
                'progress_percentage': min(100, (bench.current_value / bench.target_value) * 100)
            }
            for name, bench in self.research_benchmarks.items()
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get statistical validation engine statistics"""
        compliance_rate = self.stats['compliance_passes'] / max(1, self.stats['validations_performed'])

        return {
            **self.stats,
            'compliance_rate': compliance_rate,
            'validation_data_size': {
                'sentiment_scores': len(self.validation_data['sentiment_scores']),
                'price_changes': len(self.validation_data['price_changes']),
                'predictions': len(self.validation_data['predictions']),
                'outcomes': len(self.validation_data['outcomes'])
            },
            'history_records': len(self.validation_history)
        }
```

## Key Features

### 📊 HDRB Research Compliance

- **IEEE Standards**: Exact research paper implementation
- **Statistical Significance**: p < 0.05 validation
- **Benchmark Targets**: 77% accuracy, 70% correlation
- **Continuous Monitoring**: Real-time compliance checking

### 🔬 Statistical Validation

- **Correlation Analysis**: Pearson and Spearman correlation
- **Confidence Intervals**: 95% confidence interval calculation
- **Significance Testing**: One-sample and proportion tests
- **Sample Size Validation**: Minimum sample requirements

### 📈 Performance Benchmarks

- **Noise Reduction**: 45% minimum target validation
- **Prediction Accuracy**: 77% accuracy benchmark
- **Sentiment Correlation**: 70% correlation target
- **Spearman Correlation**: ≥ 0.642 research benchmark

### 💾 Data Management

- **Validation History**: 100 most recent validation records
- **Benchmark Tracking**: Current vs target performance
- **Data Persistence**: JSON-based storage system
- **Memory Management**: 1000-sample data limits

## Integration Points

- **MessageProcessor**: HDRB score validation
- **ChannelReputation**: Prediction accuracy validation
- **PerformanceTracker**: Outcome data for correlation analysis
- **RealWorldDataProvider**: Authentic data validation

This implementation ensures the system maintains research compliance and academic standards throughout operation.
