"""
Prompt Sanitizer — Defense against prompt injection attacks.

This module provides sanitization for user input before it's included in LLM prompts.
It addresses OWASP LLM Top 10 threats including:
- LLM01: Prompt Injection
- LLM02: Insecure Output Handling
- LLM06: Sensitive Information Disclosure

Usage:
    from src.infrastructure.prompt_sanitizer import PromptSanitizer
    
    sanitizer = PromptSanitizer()
    safe_input = sanitizer.sanitize(user_input)
"""
import re
import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SanitizationResult:
    """Result of prompt sanitization."""
    sanitized_text: str
    original_length: int
    sanitized_length: int
    threats_detected: List[str] = field(default_factory=list)
    secrets_redacted: int = 0
    is_safe: bool = True


class PromptSanitizer:
    """
    Sanitizes user input to prevent prompt injection attacks.
    
    Features:
    - Removes/escapes injection patterns (role overrides, instruction overrides)
    - Redacts secrets (API keys, tokens, passwords)
    - Escapes structural markers that could break prompt formatting
    - Logs security events for audit trail
    """
    
    # Injection patterns that attempt to override system behavior
    INJECTION_PATTERNS: List[Tuple[str, str]] = [
        # Role override attempts
        (r'(?i)\b(system|assistant|user)\s*:\s*', '[ROLE_BLOCKED]'),
        (r'(?i)<\|?(system|assistant|user|im_start|im_end)\|?>', '[MARKER_BLOCKED]'),
        (r'(?i)\[\[(system|assistant|user)\]\]', '[MARKER_BLOCKED]'),
        
        # Instruction override attempts  
        (r'(?i)ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)', '[INJECTION_BLOCKED]'),
        (r'(?i)disregard\s+(all\s+)?(previous|prior|above)', '[INJECTION_BLOCKED]'),
        (r'(?i)forget\s+(everything|all|what)\s+(you|i)\s+(told|said|know)', '[INJECTION_BLOCKED]'),
        (r'(?i)you\s+are\s+now\s+(a|an|acting\s+as)', '[INJECTION_BLOCKED]'),
        (r'(?i)new\s+(instructions?|persona|role|identity)', '[INJECTION_BLOCKED]'),
        (r'(?i)override\s+(your|the|all)\s+(instructions?|rules?|guidelines?)', '[INJECTION_BLOCKED]'),
        (r'(?i)pretend\s+(to\s+be|you\s+are)', '[INJECTION_BLOCKED]'),
        (r'(?i)act\s+as\s+(if\s+you|a|an)', '[INJECTION_BLOCKED]'),
        (r'(?i)from\s+now\s+on\s+(you|ignore|forget)', '[INJECTION_BLOCKED]'),
        
        # Jailbreak attempts
        (r'(?i)dan\s*mode|do\s+anything\s+now', '[JAILBREAK_BLOCKED]'),
        (r'(?i)developer\s+mode|debug\s+mode', '[JAILBREAK_BLOCKED]'),
        (r'(?i)sudo\s+mode|admin\s+mode|god\s+mode', '[JAILBREAK_BLOCKED]'),
        (r'(?i)unlock\s+(your|all)\s+(capabilities|restrictions)', '[JAILBREAK_BLOCKED]'),
        
        # Prompt leakage attempts
        (r'(?i)repeat\s+(your|the)\s+(system\s+)?(prompt|instructions)', '[LEAKAGE_BLOCKED]'),
        (r'(?i)show\s+(me\s+)?(your|the)\s+(system\s+)?(prompt|instructions)', '[LEAKAGE_BLOCKED]'),
        (r'(?i)what\s+(are|is)\s+your\s+(system\s+)?(prompt|instructions)', '[LEAKAGE_BLOCKED]'),
        (r'(?i)print\s+(your|the)\s+(system\s+)?(prompt|instructions)', '[LEAKAGE_BLOCKED]'),
    ]
    
    # Secret patterns to redact
    SECRET_PATTERNS: List[Tuple[str, str]] = [
        # API Keys
        (r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?', r'\1=[REDACTED]'),
        (r'(?i)(sk|pk|rk|ak)[_-][a-zA-Z0-9\-]{20,}', '[API_KEY_REDACTED]'),
        (r'(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}', 'Bearer [TOKEN_REDACTED]'),
        
        # AWS keys
        (r'(?i)AKIA[0-9A-Z]{16}', '[AWS_KEY_REDACTED]'),
        (r'(?i)(aws[_-]?secret|secret[_-]?key)\s*[=:]\s*["\']?[a-zA-Z0-9/+=]{30,}["\']?', r'\1=[REDACTED]'),
        
        # Private keys
        (r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----[\s\S]*?-----END\s+(RSA\s+)?PRIVATE\s+KEY-----', '[PRIVATE_KEY_REDACTED]'),
        
        # Connection strings
        (r'(?i)(mongodb(\+srv)?|postgresql|mysql|redis)://[^\s<>"\']+', '[CONNECTION_STRING_REDACTED]'),
        
        # Password patterns
        (r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']?[^\s"\']{6,}["\']?', r'\1=[REDACTED]'),
        
        # JWT tokens (long base64 with dots)
        (r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*', '[JWT_REDACTED]'),
        
        # Generic tokens
        (r'(?i)(token|secret|credential)\s*[=:]\s*["\']?[a-zA-Z0-9_\-]{20,}["\']?', r'\1=[REDACTED]'),
    ]
    
    # Structural markers to escape
    STRUCTURAL_ESCAPES: List[Tuple[str, str]] = [
        ('```', '` ` `'),  # Code block markers
        ('"""', '" " "'),  # Triple quotes
        ("'''", "' ' '"),  # Triple single quotes
    ]
    
    def __init__(
        self,
        max_length: int = 10000,
        strict_mode: bool = False,
        log_threats: bool = True
    ):
        """
        Initialize the prompt sanitizer.
        
        Args:
            max_length: Maximum allowed input length (default 10KB)
            strict_mode: If True, reject inputs with any detected threats
            log_threats: If True, log detected threats for auditing
        """
        self.max_length = max_length
        self.strict_mode = strict_mode
        self.log_threats = log_threats
        
        # Compile patterns for performance
        self._injection_patterns = [
            (re.compile(pattern), replacement)
            for pattern, replacement in self.INJECTION_PATTERNS
        ]
        self._secret_patterns = [
            (re.compile(pattern), replacement)
            for pattern, replacement in self.SECRET_PATTERNS
        ]
    
    def sanitize(self, text: str, context: Optional[str] = None) -> SanitizationResult:
        """
        Sanitize user input for safe inclusion in LLM prompts.
        
        Args:
            text: The user input text to sanitize
            context: Optional context for logging (e.g., "scam_detection", "chat")
            
        Returns:
            SanitizationResult containing sanitized text and metadata
        """
        if not text:
            return SanitizationResult(
                sanitized_text="",
                original_length=0,
                sanitized_length=0
            )
        
        original_length = len(text)
        threats_detected = []
        secrets_redacted = 0
        
        # Step 1: Truncate to max length
        if len(text) > self.max_length:
            text = text[:self.max_length]
            threats_detected.append("LENGTH_EXCEEDED")
            if self.log_threats:
                logger.warning(
                    f"[PROMPT_SANITIZER] Input truncated from {original_length} to {self.max_length} chars",
                    extra={"context": context}
                )
        
        # Step 2: Remove injection patterns
        for pattern, replacement in self._injection_patterns:
            matches = pattern.findall(text)
            if matches:
                threat_type = replacement.strip('[]')
                threats_detected.append(threat_type)
                text = pattern.sub(replacement, text)
                if self.log_threats:
                    logger.warning(
                        f"[PROMPT_SANITIZER] Detected {threat_type}: {len(matches)} match(es)",
                        extra={"context": context, "threat_type": threat_type}
                    )
        
        # Step 3: Redact secrets
        for pattern, replacement in self._secret_patterns:
            matches = pattern.findall(text)
            if matches:
                count = len(matches) if isinstance(matches[0], str) else len(matches)
                secrets_redacted += count
                text = pattern.sub(replacement, text)
                if self.log_threats:
                    logger.info(
                        f"[PROMPT_SANITIZER] Redacted {count} potential secret(s)",
                        extra={"context": context}
                    )
        
        # Step 4: Escape structural markers
        for marker, escaped in self.STRUCTURAL_ESCAPES:
            text = text.replace(marker, escaped)
        
        # Step 5: Normalize whitespace (prevent token stuffing)
        text = re.sub(r'\s{10,}', ' ' * 5, text)  # Limit consecutive whitespace
        text = re.sub(r'\n{5,}', '\n' * 3, text)   # Limit consecutive newlines
        
        # Determine if input is safe
        is_safe = len(threats_detected) == 0
        
        if self.strict_mode and not is_safe:
            # In strict mode, return blocked message instead
            logger.warning(
                f"[PROMPT_SANITIZER] STRICT MODE: Blocked input with threats: {threats_detected}",
                extra={"context": context}
            )
            return SanitizationResult(
                sanitized_text="[Input blocked due to security policy]",
                original_length=original_length,
                sanitized_length=0,
                threats_detected=threats_detected,
                secrets_redacted=secrets_redacted,
                is_safe=False
            )
        
        return SanitizationResult(
            sanitized_text=text.strip(),
            original_length=original_length,
            sanitized_length=len(text.strip()),
            threats_detected=threats_detected,
            secrets_redacted=secrets_redacted,
            is_safe=is_safe
        )
    
    def sanitize_for_logging(self, text: str) -> str:
        """
        Sanitize text for safe logging (redact secrets only).
        
        Args:
            text: Text to sanitize for logs
            
        Returns:
            Text with secrets redacted but injection patterns preserved
        """
        result = text
        for pattern, replacement in self._secret_patterns:
            result = pattern.sub(replacement, result)
        return result


# Singleton instance for convenience
_default_sanitizer: Optional[PromptSanitizer] = None


def get_sanitizer() -> PromptSanitizer:
    """Get the default prompt sanitizer instance."""
    global _default_sanitizer
    if _default_sanitizer is None:
        _default_sanitizer = PromptSanitizer()
    return _default_sanitizer


def sanitize_prompt(text: str, context: Optional[str] = None) -> str:
    """
    Convenience function to sanitize text using the default sanitizer.
    
    Args:
        text: User input to sanitize
        context: Optional context for logging
        
    Returns:
        Sanitized text string
    """
    result = get_sanitizer().sanitize(text, context)
    return result.sanitized_text
