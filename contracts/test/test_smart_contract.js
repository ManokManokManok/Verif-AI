const AnalysisAnchor = artifacts.require("AnalysisAnchor");

contract("AnalysisAnchor", (accounts) => {
  const [owner, unauthorized] = accounts;
  
  // Test data
  const testPayloadHash = web3.utils.keccak256("test-payload");
  const testRefId = web3.utils.keccak256("550e8400-e29b-41d4-a716-446655440000");
  const testScamClass = 0;
  const testConfidenceBps = 8550;
  const testTimestamp = Math.floor(Date.now() / 1000);

  let contract;

  beforeEach(async () => {
    contract = await AnalysisAnchor.new({ from: owner });
  });

  describe("Deployment", () => {
    it("should set the deployer as owner", async () => {
      const contractOwner = await contract.owner();
      assert.equal(contractOwner, owner, "Owner should be deployer");
    });

    it("should start with zero records", async () => {
      const count = await contract.recordCount();
      assert.equal(count.toNumber(), 0, "Record count should be 0");
    });
  });

  describe("storeRecord", () => {
    it("should store a valid record", async () => {
      const tx = await contract.storeRecord(
        testPayloadHash,
        testScamClass,
        testConfidenceBps,
        testTimestamp,
        testRefId,
        { from: owner }
      );

      // Check event was emitted
      assert.equal(tx.logs.length, 1, "Should emit one event");
      assert.equal(tx.logs[0].event, "RecordStored", "Should emit RecordStored");
      assert.equal(tx.logs[0].args.payloadHash, testPayloadHash);
      assert.equal(tx.logs[0].args.scamClass.toNumber(), testScamClass);

      // Check record count
      const count = await contract.recordCount();
      assert.equal(count.toNumber(), 1, "Record count should be 1");
    });

    it("should reject unauthorized callers", async () => {
      try {
        await contract.storeRecord(
          testPayloadHash,
          testScamClass,
          testConfidenceBps,
          testTimestamp,
          testRefId,
          { from: unauthorized }
        );
        assert.fail("Should have reverted");
      } catch (error) {
        // Custom errors show as "revert" - just verify it reverted
        assert.include(error.message, "revert", "Should revert for unauthorized caller");
      }
    });

    it("should reject duplicate payloadHash", async () => {
      await contract.storeRecord(
        testPayloadHash,
        testScamClass,
        testConfidenceBps,
        testTimestamp,
        testRefId,
        { from: owner }
      );

      try {
        await contract.storeRecord(
          testPayloadHash,
          testScamClass + 1,
          testConfidenceBps,
          testTimestamp,
          testRefId,
          { from: owner }
        );
        assert.fail("Should have reverted");
      } catch (error) {
        assert.include(error.message, "revert", "Should revert for duplicate hash");
      }
    });

    it("should reject invalid confidence (>10000)", async () => {
      try {
        await contract.storeRecord(
          testPayloadHash,
          testScamClass,
          10001, // Invalid: > 10000
          testTimestamp,
          testRefId,
          { from: owner }
        );
        assert.fail("Should have reverted");
      } catch (error) {
        assert.include(error.message, "revert", "Should revert for invalid confidence");
      }
    });

    it("should reject invalid scamClass (15-254)", async () => {
      try {
        await contract.storeRecord(
          testPayloadHash,
          15, // Invalid: not 0-14 or 255
          testConfidenceBps,
          testTimestamp,
          testRefId,
          { from: owner }
        );
        assert.fail("Should have reverted");
      } catch (error) {
        assert.include(error.message, "revert", "Should revert for invalid scamClass");
      }
    });

    it("should accept scamClass 255 (unknown/-1)", async () => {
      const tx = await contract.storeRecord(
        testPayloadHash,
        255, // Valid: represents -1/unknown
        testConfidenceBps,
        testTimestamp,
        testRefId,
        { from: owner }
      );
      assert.equal(tx.logs[0].args.scamClass.toNumber(), 255);
    });

    it("should accept scamClass 0-14", async () => {
      for (let scamClass = 0; scamClass <= 14; scamClass++) {
        const hash = web3.utils.keccak256(`test-${scamClass}`);
        await contract.storeRecord(
          hash,
          scamClass,
          testConfidenceBps,
          testTimestamp,
          testRefId,
          { from: owner }
        );
      }
      const count = await contract.recordCount();
      assert.equal(count.toNumber(), 15);
    });
  });

  describe("getRecord", () => {
    it("should return stored record data", async () => {
      await contract.storeRecord(
        testPayloadHash,
        testScamClass,
        testConfidenceBps,
        testTimestamp,
        testRefId,
        { from: owner }
      );

      const result = await contract.getRecord(testPayloadHash);
      
      assert.equal(result.exists, true, "Record should exist");
      assert.equal(result.scamClass.toNumber(), testScamClass, "ScamClass should match");
      assert.equal(result.confidenceBps.toNumber(), testConfidenceBps, "ConfidenceBps should match");
      assert.equal(result.timestamp.toNumber(), testTimestamp, "Timestamp should match");
      assert.equal(result.refId, testRefId, "RefId should match");
      assert.equal(result.storedBy, owner, "StoredBy should be owner");
    });

    it("should return exists=false for non-existent record", async () => {
      const nonExistentHash = web3.utils.keccak256("does-not-exist");
      const result = await contract.getRecord(nonExistentHash);
      
      assert.equal(result.exists, false, "Record should not exist");
    });
  });

  describe("recordExists", () => {
    it("should return true for existing record", async () => {
      await contract.storeRecord(
        testPayloadHash,
        testScamClass,
        testConfidenceBps,
        testTimestamp,
        testRefId,
        { from: owner }
      );

      const exists = await contract.recordExists(testPayloadHash);
      assert.equal(exists, true);
    });

    it("should return false for non-existing record", async () => {
      const exists = await contract.recordExists(testPayloadHash);
      assert.equal(exists, false);
    });
  });

  describe("verifyRecord", () => {
    beforeEach(async () => {
      await contract.storeRecord(
        testPayloadHash,
        testScamClass,
        testConfidenceBps,
        testTimestamp,
        testRefId,
        { from: owner }
      );
    });

    it("should return matches=true for correct data", async () => {
      const result = await contract.verifyRecord(
        testPayloadHash,
        testScamClass,
        testConfidenceBps,
        testTimestamp,
        testRefId
      );

      assert.equal(result.matches, true, "Should match");
      assert.equal(result.recordFound, true, "Record should be found");
    });

    it("should return matches=false for wrong scamClass", async () => {
      const result = await contract.verifyRecord(
        testPayloadHash,
        testScamClass + 1, // Wrong
        testConfidenceBps,
        testTimestamp,
        testRefId
      );

      assert.equal(result.matches, false, "Should not match");
      assert.equal(result.recordFound, true, "Record should be found");
    });

    it("should return recordFound=false for non-existent hash", async () => {
      const result = await contract.verifyRecord(
        web3.utils.keccak256("does-not-exist"),
        testScamClass,
        testConfidenceBps,
        testTimestamp,
        testRefId
      );

      assert.equal(result.matches, false, "Should not match");
      assert.equal(result.recordFound, false, "Record should not be found");
    });
  });

  describe("transferOwnership", () => {
    it("should allow owner to transfer ownership", async () => {
      await contract.transferOwnership(unauthorized, { from: owner });
      const newOwner = await contract.owner();
      assert.equal(newOwner, unauthorized);
    });

    it("should reject transfer from non-owner", async () => {
      try {
        await contract.transferOwnership(unauthorized, { from: unauthorized });
        assert.fail("Should have reverted");
      } catch (error) {
        assert.include(error.message, "revert", "Should revert for non-owner");
      }
    });

    it("should reject transfer to zero address", async () => {
      try {
        await contract.transferOwnership("0x0000000000000000000000000000000000000000", { from: owner });
        assert.fail("Should have reverted");
      } catch (error) {
        assert.include(error.message, "revert", "Should revert for zero address");
      }
    });
  });
});