// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title AnalysisAnchor
 * @notice Stores tamper-proof anchors for Verif-AI analysis results
 * @dev On-chain storage of non-PII metadata only: hash, classification, confidence, timestamp, refId
 * 
 * PRIVACY POLICY:
 * - NO raw messages, user text, email, phone, or PII is ever stored on-chain
 * - Only computed hashes and numerical classifications are stored
 * - The payloadHash is computed from a canonical non-PII payload off-chain
 * 
 * ACCESS CONTROL:
 * - Only the contract owner (backend signer) can store records
 * - Anyone can read/verify records
 */
contract AnalysisAnchor {
    
    // =========================================================================
    // STRUCTS
    // =========================================================================
    
    /**
     * @notice On-chain record structure for an anchored analysis
     * @param exists Whether this record exists (used for existence checks)
     * @param scamClass Classification result (0-14, with -1 represented as 255)
     * @param confidenceBps Confidence in basis points (0-10000)
     * @param timestamp Unix timestamp when analysis was created (UTC)
     * @param refId Reference ID (UUID bytes32 representation)
     * @param storedBy Address that stored this record
     * @param blockNumber Block number when record was stored
     */
    struct AnchorRecord {
        bool exists;
        uint8 scamClass;
        uint16 confidenceBps;
        uint64 timestamp;
        bytes32 refId;
        address storedBy;
        uint64 blockNumber;
    }
    
    // =========================================================================
    // STATE VARIABLES
    // =========================================================================
    
    /// @notice Contract owner (backend signer)
    address public owner;
    
    /// @notice Mapping from payloadHash to AnchorRecord
    mapping(bytes32 => AnchorRecord) private records;
    
    /// @notice Total number of records stored
    uint256 public recordCount;
    
    // =========================================================================
    // EVENTS
    // =========================================================================
    
    /**
     * @notice Emitted when a new record is stored
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
    
    /// @notice Thrown when record already exists for given payloadHash
    error RecordAlreadyExists(bytes32 payloadHash);
    
    /// @notice Thrown when record does not exist
    error RecordNotFound(bytes32 payloadHash);
    
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
     * @notice Store an analysis anchor on-chain
     * @dev Only callable by owner. Reverts if record already exists.
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
        // Validation
        if (records[payloadHash].exists) {
            revert RecordAlreadyExists(payloadHash);
        }
        if (confidenceBps > 10000) {
            revert InvalidConfidence(confidenceBps);
        }
        // scamClass: 0-14 valid, 255 is "unknown"/-1 sentinel
        if (scamClass > 14 && scamClass != 255) {
            revert InvalidScamClass(scamClass);
        }
        
        // Store the record
        records[payloadHash] = AnchorRecord({
            exists: true,
            scamClass: scamClass,
            confidenceBps: confidenceBps,
            timestamp: timestamp,
            refId: refId,
            storedBy: msg.sender,
            blockNumber: uint64(block.number)
        });
        
        recordCount++;
        
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
     * @notice Retrieve an anchored record by payloadHash
     * @param payloadHash The hash to look up
     * @return exists Whether the record exists
     * @return scamClass The stored scam classification
     * @return confidenceBps The stored confidence in basis points
     * @return timestamp The stored analysis timestamp
     * @return refId The stored reference ID
     * @return storedBy Address that stored the record
     */
    function getRecord(bytes32 payloadHash)
        external
        view
        returns (
            bool exists,
            uint8 scamClass,
            uint16 confidenceBps,
            uint64 timestamp,
            bytes32 refId,
            address storedBy
        )
    {
        AnchorRecord storage record = records[payloadHash];
        return (
            record.exists,
            record.scamClass,
            record.confidenceBps,
            record.timestamp,
            record.refId,
            record.storedBy
        );
    }
    
    /**
     * @notice Check if a record exists for a given payloadHash
     * @param payloadHash The hash to check
     * @return Whether the record exists
     */
    function recordExists(bytes32 payloadHash) external view returns (bool) {
        return records[payloadHash].exists;
    }
    
    /**
     * @notice Get the block number when a record was stored
     * @param payloadHash The hash to look up
     * @return The block number (0 if record doesn't exist)
     */
    function getRecordBlockNumber(bytes32 payloadHash) external view returns (uint64) {
        return records[payloadHash].blockNumber;
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
    
    /**
     * @notice Verify that a payload hash matches stored metadata
     * @dev Convenience function for verification
     * @param payloadHash The hash to verify
     * @param expectedScamClass Expected scam class value
     * @param expectedConfidenceBps Expected confidence in basis points
     * @param expectedTimestamp Expected timestamp
     * @param expectedRefId Expected reference ID
     * @return matches Whether all values match
     * @return recordFound Whether the record exists
     */
    function verifyRecord(
        bytes32 payloadHash,
        uint8 expectedScamClass,
        uint16 expectedConfidenceBps,
        uint64 expectedTimestamp,
        bytes32 expectedRefId
    ) external view returns (bool matches, bool recordFound) {
        AnchorRecord storage record = records[payloadHash];
        
        if (!record.exists) {
            return (false, false);
        }
        
        bool allMatch = (
            record.scamClass == expectedScamClass &&
            record.confidenceBps == expectedConfidenceBps &&
            record.timestamp == expectedTimestamp &&
            record.refId == expectedRefId
        );
        
        return (allMatch, true);
    }
}
