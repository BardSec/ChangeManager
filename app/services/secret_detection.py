import re
from typing import List, Tuple


class SecretDetector:
    """Detect potential secrets in change record text."""
    
    # Patterns for common secret types
    PATTERNS = [
        (r'-----BEGIN (?:RSA |DSA )?PRIVATE KEY-----', 'Private key'),
        (r'-----BEGIN CERTIFICATE-----', 'Certificate'),
        (r'password\s*[=:]\s*["\']?[\w\-!@#$%^&*()+=]{8,}', 'Password'),
        (r'api[_-]?key\s*[=:]\s*["\']?[\w\-]{20,}', 'API key'),
        (r'secret[_-]?key\s*[=:]\s*["\']?[\w\-]{20,}', 'Secret key'),
        (r'aws[_-]?access[_-]?key[_-]?id\s*[=:]\s*["\']?A[A-Z0-9]{19}', 'AWS access key'),
        (r'aws[_-]?secret[_-]?access[_-]?key\s*[=:]\s*["\']?[\w/+=]{40}', 'AWS secret key'),
        (r'[a-zA-Z0-9_-]*:[a-zA-Z0-9_-]{20,}@', 'Credentials in URL'),
        (r'bearer\s+[a-zA-Z0-9\-._~+/]+=*', 'Bearer token'),
        (r'token\s*[=:]\s*["\']?[a-zA-Z0-9\-._~+/]{32,}', 'Token'),
        (r'sk_live_[a-zA-Z0-9]{24,}', 'Stripe secret key'),
        (r'rk_live_[a-zA-Z0-9]{24,}', 'Stripe restricted key'),
        (r'ghp_[a-zA-Z0-9]{36,}', 'GitHub personal access token'),
        (r'ghs_[a-zA-Z0-9]{36,}', 'GitHub OAuth token'),
        (r'AKIA[0-9A-Z]{16}', 'AWS access key ID'),
        (r'-----BEGIN OPENSSH PRIVATE KEY-----', 'SSH private key'),
        (r'PRIVATE KEY.*-----END', 'Private key block'),
    ]
    
    @classmethod
    def scan(cls, text: str) -> List[Tuple[str, str]]:
        """
        Scan text for potential secrets.
        
        Args:
            text: Text to scan
            
        Returns:
            List of tuples (pattern_name, matched_text_preview)
        """
        if not text:
            return []
        
        findings = []
        text_lower = text.lower()
        
        for pattern, name in cls.PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                # Create a preview (first 50 chars of match)
                preview = match.group(0)[:50]
                if len(match.group(0)) > 50:
                    preview += '...'
                findings.append((name, preview))
        
        return findings
    
    @classmethod
    def has_secrets(cls, change_data: dict) -> Tuple[bool, List[Tuple[str, str]]]:
        """
        Check if change data contains potential secrets.
        
        Args:
            change_data: Dictionary with change record fields
            
        Returns:
            Tuple of (has_secrets: bool, findings: List)
        """
        # Fields to scan for secrets
        fields_to_scan = [
            'what_changed',
            'backout_plan',
            'outcome_notes',
            'post_change_issues',
            'links',
        ]
        
        all_findings = []
        
        for field in fields_to_scan:
            value = change_data.get(field)
            if value:
                # Handle both string and list values
                if isinstance(value, list):
                    value = ' '.join(str(v) for v in value)
                else:
                    value = str(value)
                
                findings = cls.scan(value)
                all_findings.extend(findings)
        
        return len(all_findings) > 0, all_findings
