"""
Preset Selection Service - Rule Evaluation Engine.

Safely evaluates declarative rules to determine which randomizer preset
to use for a tournament match based on match properties and player settings.
"""

from __future__ import annotations
from typing import Optional, Any, Dict, List
import re
import logging
from datetime import datetime

from modules.tournament.models.match_schedule import Match, Tournament
from modules.tournament.models.tournament_match_settings import (
    TournamentMatchSettings,
)
from models.randomizer_preset import RandomizerPreset

logger = logging.getLogger(__name__)


class PresetSelectionService:
    """
    Service for evaluating preset selection rules.
    
    Provides safe, declarative rule evaluation without code execution.
    Rules are JSON configurations that specify conditions and resulting presets.
    """
    
    # Maximum rules to prevent performance issues
    MAX_RULES = 20
    
    # Maximum condition nesting depth
    MAX_CONDITION_DEPTH = 5
    
    # Whitelisted field prefixes that can be accessed
    ALLOWED_FIELD_PREFIXES = {
        'match.',
        'settings.',
        'tournament.',
    }
    
    # Supported operators
    OPERATORS = {
        # Equality
        'equals', 'not_equals',
        # String operations
        'contains', 'starts_with', 'ends_with', 'matches_regex',
        # Numeric comparison
        '>', '>=', '<', '<=', 'between',
        # List operations
        'in', 'not_in',
    }
    
    # Logical operators
    LOGICAL_OPERATORS = {'AND', 'OR', 'NOT'}
    
    async def select_preset_for_match(
        self,
        match: Match,
        tournament: Tournament,
        game_number: int = 1,
        player_settings: Optional[TournamentMatchSettings] = None,
    ) -> Optional[int]:
        """
        Evaluate rules and return preset_id to use for a match.
        
        Args:
            match: Match to select preset for
            tournament: Tournament configuration
            game_number: Game number in best-of-N series
            player_settings: Optional player-submitted settings
            
        Returns:
            preset_id to use, or None to use tournament default
        """
        # No rules configured - use tournament default
        if not tournament.preset_selection_rules:
            logger.debug(
                "No preset selection rules configured for tournament %s",
                tournament.id
            )
            return tournament.randomizer_preset_id
        
        rules_config = tournament.preset_selection_rules
        rules = rules_config.get('rules', [])
        
        # Validate rule count
        if len(rules) > self.MAX_RULES:
            logger.warning(
                "Tournament %s has %d rules (max %d), truncating",
                tournament.id,
                len(rules),
                self.MAX_RULES
            )
            rules = rules[:self.MAX_RULES]
        
        # Build evaluation context
        context = await self._build_context(
            match, tournament, game_number, player_settings
        )
        
        # Evaluate rules in order (first match wins)
        for idx, rule in enumerate(rules):
            rule_name = rule.get('name', f'Rule {idx + 1}')
            
            try:
                if self._evaluate_rule(rule, context):
                    preset_id = rule.get('preset_id')
                    logger.info(
                        "Match %s matched rule '%s', using preset %s",
                        match.id,
                        rule_name,
                        preset_id
                    )
                    return preset_id
            except Exception as e:
                logger.error(
                    "Error evaluating rule '%s' for match %s: %s",
                    rule_name,
                    match.id,
                    e,
                    exc_info=True
                )
                # Continue to next rule on error
                continue
        
        # No rules matched - use tournament default
        logger.debug(
            "No rules matched for match %s, using tournament default preset %s",
            match.id,
            tournament.randomizer_preset_id
        )
        return tournament.randomizer_preset_id
    
    async def _build_context(
        self,
        match: Match,
        tournament: Tournament,
        game_number: int,
        player_settings: Optional[TournamentMatchSettings],
    ) -> Dict[str, Any]:
        """
        Build evaluation context with all available data.
        
        Args:
            match: Match instance
            tournament: Tournament instance
            game_number: Game number in series
            player_settings: Optional player settings
            
        Returns:
            Dictionary of context data for rule evaluation
        """
        # Ensure match has required relations loaded
        await match.fetch_related('players__user', 'tournament')
        
        # Build match context
        match_context = {
            'id': match.id,
            'title': match.title or '',
            'round_number': match.round_number or 0,
            'game_number': game_number,
            'scheduled_at': match.scheduled_at,
            'player_count': await match.players.all().count(),
        }
        
        # Add datetime properties if scheduled
        if match.scheduled_at:
            match_context['scheduled_at.day_of_week'] = match.scheduled_at.strftime('%A')
            match_context['scheduled_at.hour'] = match.scheduled_at.hour
            match_context['scheduled_at.day'] = match.scheduled_at.day
        
        # Build settings context (from player submission)
        settings_context = {}
        if player_settings and player_settings.settings:
            settings_context = player_settings.settings.copy()
        
        # Build tournament context
        tournament_context = {
            'id': tournament.id,
            'name': tournament.name,
            # Add more tournament fields as needed
        }
        
        # Combine into full context
        context = {
            'match': match_context,
            'settings': settings_context,
            'tournament': tournament_context,
        }
        
        return context
    
    def _evaluate_rule(self, rule: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Evaluate a single rule against context.
        
        Args:
            rule: Rule configuration dictionary
            context: Evaluation context
            
        Returns:
            True if rule matches, False otherwise
        """
        conditions = rule.get('conditions')
        if not conditions:
            logger.warning("Rule has no conditions: %s", rule.get('name', 'Unknown'))
            return False
        
        return self._evaluate_condition(conditions, context, depth=0)
    
    def _evaluate_condition(
        self,
        condition: Dict[str, Any],
        context: Dict[str, Any],
        depth: int = 0,
    ) -> bool:
        """
        Recursively evaluate a condition (may contain nested conditions).
        
        Args:
            condition: Condition configuration
            context: Evaluation context
            depth: Current recursion depth
            
        Returns:
            True if condition is satisfied
            
        Raises:
            ValueError: If condition is malformed or exceeds max depth
        """
        # Check depth limit
        if depth > self.MAX_CONDITION_DEPTH:
            raise ValueError(f"Condition nesting exceeds maximum depth of {self.MAX_CONDITION_DEPTH}")
        
        # Check if this is a logical operator (AND/OR/NOT)
        condition_type = condition.get('type')
        
        if condition_type in self.LOGICAL_OPERATORS:
            return self._evaluate_logical_condition(condition, context, depth)
        
        # Otherwise, this is a leaf condition - evaluate it
        return self._evaluate_leaf_condition(condition, context)
    
    def _evaluate_logical_condition(
        self,
        condition: Dict[str, Any],
        context: Dict[str, Any],
        depth: int,
    ) -> bool:
        """
        Evaluate a logical condition (AND/OR/NOT).
        
        Args:
            condition: Logical condition configuration
            context: Evaluation context
            depth: Current recursion depth
            
        Returns:
            Result of logical operation
        """
        condition_type = condition['type']
        conditions = condition.get('conditions', [])
        
        if condition_type == 'AND':
            # All conditions must be true
            return all(
                self._evaluate_condition(cond, context, depth + 1)
                for cond in conditions
            )
        
        elif condition_type == 'OR':
            # At least one condition must be true
            return any(
                self._evaluate_condition(cond, context, depth + 1)
                for cond in conditions
            )
        
        elif condition_type == 'NOT':
            # Negate the result of a single condition
            if len(conditions) != 1:
                raise ValueError("NOT operator requires exactly one condition")
            return not self._evaluate_condition(conditions[0], context, depth + 1)
        
        else:
            raise ValueError(f"Unknown logical operator: {condition_type}")
    
    def _evaluate_leaf_condition(
        self,
        condition: Dict[str, Any],
        context: Dict[str, Any],
    ) -> bool:
        """
        Evaluate a leaf condition (no nested conditions).
        
        Args:
            condition: Leaf condition configuration
            context: Evaluation context
            
        Returns:
            Result of comparison
        """
        field = condition.get('field')
        operator = condition.get('operator')
        expected_value = condition.get('value')
        
        if not field or not operator:
            raise ValueError("Condition missing 'field' or 'operator'")
        
        # Validate field is allowed
        if not any(field.startswith(prefix) for prefix in self.ALLOWED_FIELD_PREFIXES):
            raise ValueError(f"Field '{field}' is not allowed")
        
        # Validate operator is supported
        if operator not in self.OPERATORS:
            raise ValueError(f"Operator '{operator}' is not supported")
        
        # Get actual value from context
        actual_value = self._get_field_value(field, context)
        
        # Perform comparison
        return self._compare_values(actual_value, operator, expected_value)
    
    def _get_field_value(self, field: str, context: Dict[str, Any]) -> Any:
        """
        Get field value from context using dot notation.
        
        Args:
            field: Field path (e.g., 'match.title', 'settings.preset')
            context: Evaluation context
            
        Returns:
            Field value or None if not found
        """
        parts = field.split('.')
        value = context
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
                if value is None:
                    return None
            else:
                return None
        
        return value
    
    def _compare_values(
        self,
        actual: Any,
        operator: str,
        expected: Any,
    ) -> bool:
        """
        Compare two values using the specified operator.
        
        Args:
            actual: Actual value from context
            operator: Comparison operator
            expected: Expected value from rule
            
        Returns:
            Comparison result
        """
        # Handle None/null values
        if actual is None:
            return operator == 'equals' and expected is None
        
        try:
            # Equality operators
            if operator == 'equals':
                return actual == expected
            
            elif operator == 'not_equals':
                return actual != expected
            
            # String operators
            elif operator == 'contains':
                return str(expected).lower() in str(actual).lower()
            
            elif operator == 'starts_with':
                return str(actual).lower().startswith(str(expected).lower())
            
            elif operator == 'ends_with':
                return str(actual).lower().endswith(str(expected).lower())
            
            elif operator == 'matches_regex':
                # Limited regex support - validate pattern first
                pattern = str(expected)
                if len(pattern) > 200:  # Prevent catastrophic backtracking
                    raise ValueError("Regex pattern too long")
                return bool(re.search(pattern, str(actual), re.IGNORECASE))
            
            # Numeric comparison operators
            elif operator in ('>', '>=', '<', '<='):
                actual_num = float(actual) if actual is not None else 0
                expected_num = float(expected)
                
                if operator == '>':
                    return actual_num > expected_num
                elif operator == '>=':
                    return actual_num >= expected_num
                elif operator == '<':
                    return actual_num < expected_num
                elif operator == '<=':
                    return actual_num <= expected_num
            
            elif operator == 'between':
                # expected should be [min, max]
                if not isinstance(expected, (list, tuple)) or len(expected) != 2:
                    raise ValueError("'between' operator requires [min, max] array")
                actual_num = float(actual) if actual is not None else 0
                return expected[0] <= actual_num <= expected[1]
            
            # List operators
            elif operator == 'in':
                if not isinstance(expected, (list, tuple)):
                    raise ValueError("'in' operator requires array value")
                return actual in expected
            
            elif operator == 'not_in':
                if not isinstance(expected, (list, tuple)):
                    raise ValueError("'not_in' operator requires array value")
                return actual not in expected
            
            else:
                raise ValueError(f"Operator '{operator}' not implemented")
        
        except (ValueError, TypeError) as e:
            logger.warning(
                "Comparison failed for %s %s %s: %s",
                actual,
                operator,
                expected,
                e
            )
            return False
    
    async def validate_rules(
        self,
        rules_config: Dict[str, Any],
        tournament_id: int,
    ) -> tuple[bool, Optional[str]]:
        """
        Validate a rules configuration before saving.
        
        Args:
            rules_config: Rules configuration to validate
            tournament_id: Tournament ID (for preset validation)
            
        Returns:
            (is_valid, error_message)
        """
        try:
            rules = rules_config.get('rules', [])
            
            # Check rule count
            if len(rules) > self.MAX_RULES:
                return False, f"Too many rules (max {self.MAX_RULES})"
            
            # Validate each rule
            for idx, rule in enumerate(rules):
                # Check required fields
                if 'conditions' not in rule:
                    return False, f"Rule {idx + 1} missing 'conditions'"
                
                if 'preset_id' not in rule:
                    return False, f"Rule {idx + 1} missing 'preset_id'"
                
                # Validate preset exists
                preset_id = rule['preset_id']
                preset = await RandomizerPreset.get_or_none(id=preset_id)
                if not preset:
                    return False, f"Rule {idx + 1}: Preset {preset_id} not found"
                
                # Validate conditions structure
                is_valid, error = self._validate_condition(rule['conditions'], depth=0)
                if not is_valid:
                    return False, f"Rule {idx + 1}: {error}"
            
            return True, None
        
        except Exception as e:
            logger.error("Rule validation error: %s", e, exc_info=True)
            return False, f"Validation error: {str(e)}"
    
    def _validate_condition(
        self,
        condition: Dict[str, Any],
        depth: int = 0,
    ) -> tuple[bool, Optional[str]]:
        """
        Validate a condition structure.
        
        Args:
            condition: Condition to validate
            depth: Current recursion depth
            
        Returns:
            (is_valid, error_message)
        """
        # Check depth
        if depth > self.MAX_CONDITION_DEPTH:
            return False, f"Condition nesting exceeds maximum depth of {self.MAX_CONDITION_DEPTH}"
        
        condition_type = condition.get('type')
        
        # Logical operator
        if condition_type in self.LOGICAL_OPERATORS:
            conditions = condition.get('conditions', [])
            
            if not conditions:
                return False, f"{condition_type} requires at least one condition"
            
            if condition_type == 'NOT' and len(conditions) != 1:
                return False, "NOT operator requires exactly one condition"
            
            # Recursively validate nested conditions
            for cond in conditions:
                is_valid, error = self._validate_condition(cond, depth + 1)
                if not is_valid:
                    return False, error
            
            return True, None
        
        # Leaf condition
        field = condition.get('field')
        operator = condition.get('operator')
        
        if not field:
            return False, "Condition missing 'field'"
        
        if not operator:
            return False, "Condition missing 'operator'"
        
        # Validate field prefix
        if not any(field.startswith(prefix) for prefix in self.ALLOWED_FIELD_PREFIXES):
            return False, f"Field '{field}' is not allowed"
        
        # Validate operator
        if operator not in self.OPERATORS:
            return False, f"Operator '{operator}' is not supported"
        
        # Validate value exists (can be None for some operators)
        if 'value' not in condition and operator not in ('equals', 'not_equals'):
            return False, f"Condition missing 'value' for operator '{operator}'"
        
        return True, None
