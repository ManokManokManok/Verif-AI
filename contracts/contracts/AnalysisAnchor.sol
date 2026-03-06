// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

/**
 * @title AnalysisAnchor
 * @notice Stores tamper-proof anchors for Verif-AI analysis results
 * @dev Gas-optimized: uses event-only logging instead of storage.
 *      All record data is emitted in events (part of the immutable receipt trie).
 *      Off-chain indexing reads event logs for verification and retrieval.
 *
 *      Gas optimization summary:
 *        - Removed records mapping (saved ~66,000 gas from 3 SSTOREs)
 *        - Removed recordCount state (saved ~5,000 gas from SSTORE)
 *        - Removed on-chain existence check SLOAD (saved ~2,100 gas)
 *        - Total reduction: ~101,000 → ~28,000 gas per storeRecord call
 * 
 * PRIVACY POLICY:
 * - NO raw messages, user text, email, phone, or PII is ever stored on-chain
 * - Only computed hashes and numerical classifications are emitted
 * - The payloadHash is computed from a canonical non-PII payload off-chain
 * 
 * ACCESS CONTROL:
 * - Only the contract owner (backend signer) can store records
 * - Anyone can read events from the blockchain
 * 
 * SECURITY NOTE:
 * - Events are part of the transaction receipt and block receipt root
 * - They are immutable once the block is finalized
 * - Duplicate prevention is handled off-chain by the backend before sending tx
 */
contract AnalysisAnchor {
    
    // =========================================================================
    // STATE VARIABLES
    // =========================================================================
    
    /// @notice Contract owner (backend signer)
    address public owner;
    
    // =========================================================================
    // EVENTS
    // =========================================================================
    
    /**
     * @notice Emitted when a new record is stored (primary data store)
     * @param payloadHash The keccak256 hash of the canonical payload
     * @param refId The analysis reference ID
     * @param scamClass The scam classification (0-14 or 255 for unknown)
     * @param confidenceBps Confidence score in basis points
     * @param timestamp Analysis creation timestamp
     * @param storedBy Address that stored the record
     */
    event RecordStored(
        bytes32 indexed payloadHash,
        bytes32 indexed refId,
        uint8 scamClass,
        uint16 confidenceBps,
        uint64 timestamp,
        address storedBy
    );
    
    /**
     * @notice Emitted when ownership is transferred
     * @param previousOwner The previous owner address
     * @param newOwner The new owner address
     */
    event OwnershipTransferred(
        address indexed previousOwner,
        address indexed newOwner
    );
    
    // =========================================================================
    // ERRORS
    // =========================================================================
    
    /// @notice Thrown when caller is not the owner
    error OnlyOwner();
    
    /// @notice Thrown when confidence exceeds 10000 basis points
    error InvalidConfidence(uint16 confidenceBps);
    
    /// @notice Thrown when scamClass is out of range (must be 0-14 or 255)
    error InvalidScamClass(uint8 scamClass);
    
    /// @notice Thrown when new owner address is zero
    error InvalidOwnerAddress();
    
    // =========================================================================
    // MODIFIERS
    // =========================================================================
    
    /**
     * @notice Restricts function to contract owner
     */
    modifier onlyOwner() {
        if (msg.sender != owner) {
            revert OnlyOwner();
        }
        _;
    }
    
    // =========================================================================
    // CONSTRUCTOR
    // =========================================================================
    
    /**
     * @notice Initialize contract with deployer as owner
     */
    constructor() {
        owner = msg.sender;
        emit OwnershipTransferred(address(0), msg.sender);
    }
    
    // =========================================================================
    // EXTERNAL FUNCTIONS
    // =========================================================================
    
    /**
     * @notice Anchor an analysis result on-chain via event emission
     * @dev Only callable by owner. Data is stored exclusively in events.
     *      Duplicate prevention is handled off-chain by the backend.
     * @param payloadHash Keccak256 hash of the canonical payload (no PII)
     * @param scamClass Scam classification (0-14, or 255 for "unknown"/-1)
     * @param confidenceBps Confidence in basis points (0-10000)
     * @param timestamp Unix timestamp of analysis creation (UTC)
     * @param refId Analysis reference ID as bytes32
     */
    function storeRecord(
        bytes32 payloadHash,
        uint8 scamClass,
        uint16 confidenceBps,
        uint64 timestamp,
        bytes32 refId
    ) external onlyOwner {
        // Validation (cheap computation only, no storage reads)
        if (confidenceBps > 10000) {
            revert InvalidConfidence(confidenceBps);
        }
        if (scamClass > 14 && scamClass != 255) {
            revert InvalidScamClass(scamClass);
        }
        
        // Emit event as the immutable on-chain record
        emit RecordStored(
            payloadHash,
            refId,
            scamClass,
            confidenceBps,
            timestamp,
            msg.sender
        );
    }
    
    /**
     * @notice Transfer ownership to a new address
     * @dev Only callable by current owner
     * @param newOwner The new owner address
     */
    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) {
            revert InvalidOwnerAddress();
        }
        address oldOwner = owner;
        owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }
}