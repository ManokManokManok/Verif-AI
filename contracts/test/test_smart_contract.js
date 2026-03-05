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
  });

  describe("storeRecord", () => {
    it("should emit RecordStored event with correct data", async () => {
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
      assert.equal(tx.logs[0].args.confidenceBps.toNumber(), testConfidenceBps);
      assert.equal(tx.logs[0].args.timestamp.toNumber(), testTimestamp);
      assert.equal(tx.logs[0].args.storedBy, owner);
    });

    it("should use significantly less gas than storage-based approach", async () => {
      const tx = await contract.storeRecord(
        testPayloadHash,
        testScamClass,
        testConfidenceBps,
        testTimestamp,
        testRefId,
        { from: owner }
      );

      const gasUsed = tx.receipt.gasUsed;
      console.log(`      Gas used: ${gasUsed}`);
      // Event-only approach should use well under 30,000 gas
      assert.isBelow(gasUsed, 30000, `Gas should be < 30,000 (was ${gasUsed})`);
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
        assert.include(error.message, "revert", "Should revert for unauthorized caller");
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
        const tx = await contract.storeRecord(
          hash,
          scamClass,
          testConfidenceBps,
          testTimestamp,
          testRefId,
          { from: owner }
        );
        assert.equal(tx.logs[0].args.scamClass.toNumber(), scamClass);
      }
    });
  });

  describe("Event-based record retrieval", () => {
    it("should allow reading records from event logs", async () => {
      await contract.storeRecord(
        testPayloadHash,
        testScamClass,
        testConfidenceBps,
        testTimestamp,
        testRefId,
        { from: owner }
      );

      // Retrieve from event logs (the optimized verification path)
      const events = await contract.getPastEvents("RecordStored", {
        filter: { payloadHash: testPayloadHash },
        fromBlock: 0,
        toBlock: "latest"
      });

      assert.equal(events.length, 1, "Should find one matching event");
      assert.equal(events[0].returnValues.scamClass, String(testScamClass));
      assert.equal(events[0].returnValues.confidenceBps, String(testConfidenceBps));
      assert.equal(events[0].returnValues.storedBy, owner);
    });

    it("should return empty array for non-existent hash", async () => {
      const nonExistentHash = web3.utils.keccak256("does-not-exist");
      const events = await contract.getPastEvents("RecordStored", {
        filter: { payloadHash: nonExistentHash },
        fromBlock: 0,
        toBlock: "latest"
      });

      assert.equal(events.length, 0, "Should find no events");
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