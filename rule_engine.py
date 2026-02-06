"""
Rule Engine Module
Applies engineering rules to classify voltage levels
Based on electrical engineering standards - no ML training
"""

from typing import Dict, Tuple, List
import config


class RuleEngine:
    """Rule-based voltage classification engine"""
    
    def __init__(self):
        self.matched_rules = []
        
    def classify_voltage(self, features: Dict) -> Tuple[str, float, List[str]]:
        """
        Classify voltage based on extracted features
        
        Args:
            features: Dictionary of extracted features
            
        Returns:
            Tuple of (voltage_class, confidence, matched_rules)
        """
        # Try to match each voltage class
        scores = {}
        rule_matches = {}
        
        for voltage_class, rules in config.VOLTAGE_RULES.items():
            score, matches = self._evaluate_rules(features, rules, voltage_class)
            scores[voltage_class] = score
            rule_matches[voltage_class] = matches
        
        # Select best match
        best_class = max(scores.keys(), key=lambda k: scores[k])
        confidence = scores[best_class]
        matched = rule_matches[best_class]
        
        return best_class, confidence, matched
    
    def _evaluate_rules(self, features: Dict, rules: Dict, voltage_class: str) -> Tuple[float, List[str]]:
        """
        Evaluate rules for a specific voltage class
        
        Args:
            features: Extracted features
            rules: Rules for this voltage class
            voltage_class: Name of voltage class being evaluated
            
        Returns:
            Tuple of (confidence_score, list_of_matched_rules)
        """
        matched_rules = []
        total_rules = 0
        matched_count = 0
        
        # Check level count rules
        if 'min_levels' in rules:
            total_rules += 1
            if features['level_count'] >= rules['min_levels']:
                matched_count += 1
                matched_rules.append(f"Level count >= {rules['min_levels']}")
        
        if 'max_levels' in rules:
            total_rules += 1
            if features['level_count'] <= rules['max_levels']:
                matched_count += 1
                matched_rules.append(f"Level count <= {rules['max_levels']}")
        
        # Check crossarm rules
        if 'min_crossarms' in rules:
            total_rules += 1
            if features['crossarm_count'] >= rules['min_crossarms']:
                matched_count += 1
                matched_rules.append(f"Crossarm count >= {rules['min_crossarms']}")
        
        # Check spacing rules (33kV characteristic)
        if 'top_spacing_larger' in rules:
            total_rules += 1
            if features['top_spacing_larger'] == rules['top_spacing_larger']:
                matched_count += 1
                matched_rules.append("Top spacing is larger (33kV indicator)")
        
        # Check insulator rules
        if 'min_insulators' in rules:
            total_rules += 1
            if features['total_insulators'] >= rules['min_insulators']:
                matched_count += 1
                matched_rules.append(f"Insulator count >= {rules['min_insulators']}")
        
        if 'max_insulators' in rules:
            total_rules += 1
            if features['total_insulators'] <= rules['max_insulators']:
                matched_count += 1
                matched_rules.append(f"Insulator count <= {rules['max_insulators']}")
        
        # Check wire density (LT characteristic)
        if 'min_wire_density' in rules:
            total_rules += 1
            if features['wire_density'] >= rules['min_wire_density']:
                matched_count += 1
                matched_rules.append(f"Wire density >= {rules['min_wire_density']}")
        
        # Calculate confidence
        if total_rules == 0:
            confidence = 0.0
        else:
            confidence = matched_count / total_rules
        
        return confidence, matched_rules
    
    def detect_multi_circuit(self, features: Dict) -> bool:
        """
        Detect if pole is multi-circuit
        
        Args:
            features: Extracted features
            
        Returns:
            True if multi-circuit, False otherwise
        """
        return features['level_count'] >= config.MULTI_CIRCUIT_MIN_LEVELS
    
    def calculate_confidence_score(self, features: Dict, matched_rules: List[str]) -> Dict[str, float]:
        """
        Calculate detailed confidence scores
        
        Args:
            features: Extracted features
            matched_rules: List of matched rule descriptions
            
        Returns:
            Dictionary with confidence breakdown
        """
        scores = {
            'rule_match_score': len(matched_rules) / max(len(config.VOLTAGE_RULES), 1),
            'symmetry_score': features['symmetry_score'],
            'vertical_pole_confidence': 1.0 if features['vertical_pole_detected'] else 0.0,
        }
        
        # Weighted total
        weights = config.CONFIDENCE_WEIGHTS
        total_confidence = (
            scores['rule_match_score'] * (weights.get('level_match', 0.3) + 
                                          weights.get('crossarm_match', 0.2) + 
                                          weights.get('spacing_match', 0.2) +
                                          weights.get('insulator_match', 0.2)) +
            scores['symmetry_score'] * weights.get('symmetry_match', 0.1)
        )
        
        scores['total_confidence'] = total_confidence
        
        return scores
