"""
Blockchain Configuration

Loads blockchain settings from environment variables.
"""

import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load env from backend directory (where .env is located)
BACKEND_DIR = Path(__file__).resolve().parents[3]  # blockchain -> infrastructure -> src -> backend
load_dotenv(BACKEND_DIR / '.env')


@dataclass
class BlockchainConfig:
    """
    Blockchain configuration loaded from environment.
    
    Environment Variables:
        CHAIN_ENABLED: "true" or "false" - Enable/disable blockchain features
        CHAIN_RPC_URL: Ethereum JSON-RPC URL (e.g., http://127.0.0.1:7545 for Ganache)
        CHAIN_PRIVATE_KEY: Private key for the backend signer (with or without 0x prefix)
        CHAIN_CONTRACT_ADDRESS: Deployed AnalysisAnchor contract address
        CHAIN_NETWORK_NAME: Human-readable network name (e.g., "ganache", "sepolia")
        CHAIN_GAS_LIMIT: Optional gas limit override (default: 500000)
    """
    enabled: bool
    rpc_url: Optional[str]
    private_key: Optional[str]
    contract_address: Optional[str]
    network_name: str
    gas_limit: int
    
    def is_valid(self) -> bool:
        """Check if configuration is valid for blockchain operations."""
        if not self.enabled:
            return True  # Disabled config is valid (no-op mode)
        
        return all([
            self.rpc_url,
            self.private_key,
            self.contract_address
        ])
    
    def get_validation_errors(self) -> list[str]:
        """Get list of missing required configuration."""
        if not self.enabled:
            return []
        
        errors = []
        if not self.rpc_url:
            errors.append("CHAIN_RPC_URL is not set")
        if not self.private_key:
            errors.append("CHAIN_PRIVATE_KEY is not set")
        if not self.contract_address:
            errors.append("CHAIN_CONTRACT_ADDRESS is not set")
        
        return errors


_config: Optional[BlockchainConfig] = None


def get_blockchain_config() -> BlockchainConfig:
    """
    Get blockchain configuration singleton.
    
    Returns:
        BlockchainConfig instance loaded from environment
    """
    global _config
    
    if _config is None:
        enabled_str = os.getenv('CHAIN_ENABLED', 'false').lower()
        enabled = enabled_str in ('true', '1', 'yes')
        
        private_key = os.getenv('CHAIN_PRIVATE_KEY', '')
        # Normalize private key format (ensure 0x prefix)
        if private_key and not private_key.startswith('0x'):
            private_key = '0x' + private_key
        
        _config = BlockchainConfig(
            enabled=enabled,
            rpc_url=os.getenv('CHAIN_RPC_URL'),
            private_key=private_key if private_key else None,
            contract_address=os.getenv('CHAIN_CONTRACT_ADDRESS'),
            network_name=os.getenv('CHAIN_NETWORK_NAME', 'ganache'),
            gas_limit=int(os.getenv('CHAIN_GAS_LIMIT', '500000'))
        )
    
    return _config


def reset_config() -> None:
    """Reset configuration (useful for testing)."""
    global _config
    _config = None
