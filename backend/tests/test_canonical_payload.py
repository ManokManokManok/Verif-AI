"""
Phase 1 Unit Tests - Canonical Payload Schema and Hashing

Tests cover:
1. Payload validation (valid and invalid inputs)
2. Canonicalization determinism
3. Hash determinism and correctness
4. Schema evolution handling
5. Edge cases and error handling

Run with: python -m pytest tests/test_canonical.py -v
Or: python tests/test_canonical.py
"""

import sys
import os
import unittest
from pathlib import Path
from datetime import datetime, timezone
from copy import deepcopy

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add backend to path
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'verfai.settings')

from src.infrastructure.blockchain.canonical import (
    CanonicalPayload,
    PayloadValidationError,
    canonicalize_payload,
    compute_payload_hash,
    verify_payload_hash,
    validate_against_schema,
    get_json_schema,
    get_canonicalizer_for_version,
    reconstruct_payload_from_stored,
    CURRENT_SCHEMA_VERSION,
    VALID_ANALYZER_TYPES,
    SCAM_CLASS_MIN,
    SCAM_CLASS_MAX,
    CONFIDENCE_BPS_MIN,
    CONFIDENCE_BPS_MAX,
    EXAMPLE_PAYLOAD_V1,
    EXAMPLE_PAYLOAD_V1_WITH_LLM
)


class TestCanonicalPayloadValidation(unittest.TestCase):
    """Test payload validation rules."""
    
    def test_valid_payload_minimal(self):
        """Test creating a valid payload with minimal fields."""
        payload = CanonicalPayload(
            schema_version=1,
            analyzer_type="bert",
            analyzer_version="v1",
            ref_id="550e8400-e29b-41d4-a716-446655440000",
            created_at="2026-01-26T10:30:00.000Z",
            scam_class=0,
            confidence_bps=8550
        )
        
        self.assertEqual(payload.schema_version, 1)
        self.assertEqual(payload.analyzer_type, "bert")
        self.assertIsNone(payload.model_version)
    
    def test_valid_payload_with_model_version(self):
        """Test creating a valid payload with optional model_version."""
        payload = CanonicalPayload(
            schema_version=1,
            analyzer_type="llm",
            analyzer_version="v1",
            ref_id="550e8400-e29b-41d4-a716-446655440000",
            created_at="2026-01-26T10:30:00.000Z",
            scam_class=3,
            confidence_bps=9200,
            model_version="gemma-2b-v1"
        )
        
        self.assertEqual(payload.model_version, "gemma-2b-v1")
    
    def test_valid_analyzer_types(self):
        """Test all valid analyzer types."""
        for analyzer_type in VALID_ANALYZER_TYPES:
            payload = CanonicalPayload(
                schema_version=1,
                analyzer_type=analyzer_type,
                analyzer_version="v1",
                ref_id="550e8400-e29b-41d4-a716-446655440000",
                created_at="2026-01-26T10:30:00.000Z",
                scam_class=0,
                confidence_bps=5000
            )
            self.assertEqual(payload.analyzer_type, analyzer_type)
    
    def test_invalid_analyzer_type(self):
        """Test that invalid analyzer type raises error."""
        with self.assertRaises(PayloadValidationError) as ctx:
            CanonicalPayload(
                schema_version=1,
                analyzer_type="invalid",
                analyzer_version="v1",
                ref_id="550e8400-e29b-41d4-a716-446655440000",
                created_at="2026-01-26T10:30:00.000Z",
                scam_class=0,
                confidence_bps=5000
            )
        
        self.assertIn("analyzerType", str(ctx.exception))
    
    def test_invalid_schema_version(self):
        """Test that wrong schema version raises error."""
        with self.assertRaises(PayloadValidationError) as ctx:
            CanonicalPayload(
                schema_version=99,
                analyzer_type="bert",
                analyzer_version="v1",
                ref_id="550e8400-e29b-41d4-a716-446655440000",
                created_at="2026-01-26T10:30:00.000Z",
                scam_class=0,
                confidence_bps=5000
            )
        
        self.assertIn("schemaVersion", str(ctx.exception))
    
    def test_invalid_uuid_format(self):
        """Test that invalid UUID format raises error."""
        with self.assertRaises(PayloadValidationError) as ctx:
            CanonicalPayload(
                schema_version=1,
                analyzer_type="bert",
                analyzer_version="v1",
                ref_id="not-a-valid-uuid",
                created_at="2026-01-26T10:30:00.000Z",
                scam_class=0,
                confidence_bps=5000
            )
        
        self.assertIn("refId", str(ctx.exception))
    
    def test_invalid_timestamp_format(self):
        """Test that invalid timestamp format raises error."""
        invalid_timestamps = [
            "2026-01-26",  # Missing time
            "2026-01-26T10:30:00",  # Missing milliseconds
            "2026-01-26T10:30:00.000",  # Missing Z
            "2026-01-26T10:30:00.000+00:00",  # Wrong timezone format
            "not-a-date",
        ]
        
        for ts in invalid_timestamps:
            with self.assertRaises(PayloadValidationError, msg=f"Failed for: {ts}"):
                CanonicalPayload(
                    schema_version=1,
                    analyzer_type="bert",
                    analyzer_version="v1",
                    ref_id="550e8400-e29b-41d4-a716-446655440000",
                    created_at=ts,
                    scam_class=0,
                    confidence_bps=5000
                )
    
    def test_scam_class_boundaries(self):
        """Test scam class boundary values."""
        # Valid boundaries
        for scam_class in [SCAM_CLASS_MIN, 0, 7, SCAM_CLASS_MAX]:
            payload = CanonicalPayload(
                schema_version=1,
                analyzer_type="bert",
                analyzer_version="v1",
                ref_id="550e8400-e29b-41d4-a716-446655440000",
                created_at="2026-01-26T10:30:00.000Z",
                scam_class=scam_class,
                confidence_bps=5000
            )
            self.assertEqual(payload.scam_class, scam_class)
        
        # Invalid: below minimum
        with self.assertRaises(PayloadValidationError):
            CanonicalPayload(
                schema_version=1,
                analyzer_type="bert",
                analyzer_version="v1",
                ref_id="550e8400-e29b-41d4-a716-446655440000",
                created_at="2026-01-26T10:30:00.000Z",
                scam_class=SCAM_CLASS_MIN - 1,
                confidence_bps=5000
            )
        
        # Invalid: above maximum
        with self.assertRaises(PayloadValidationError):
            CanonicalPayload(
                schema_version=1,
                analyzer_type="bert",
                analyzer_version="v1",
                ref_id="550e8400-e29b-41d4-a716-446655440000",
                created_at="2026-01-26T10:30:00.000Z",
                scam_class=SCAM_CLASS_MAX + 1,
                confidence_bps=5000
            )
    
    def test_confidence_boundaries(self):
        """Test confidence basis points boundary values."""
        # Valid boundaries
        for confidence in [CONFIDENCE_BPS_MIN, 5000, CONFIDENCE_BPS_MAX]:
            payload = CanonicalPayload(
                schema_version=1,
                analyzer_type="bert",
                analyzer_version="v1",
                ref_id="550e8400-e29b-41d4-a716-446655440000",
                created_at="2026-01-26T10:30:00.000Z",
                scam_class=0,
                confidence_bps=confidence
            )
            self.assertEqual(payload.confidence_bps, confidence)
        
        # Invalid: below minimum
        with self.assertRaises(PayloadValidationError):
            CanonicalPayload(
                schema_version=1,
                analyzer_type="bert",
                analyzer_version="v1",
                ref_id="550e8400-e29b-41d4-a716-446655440000",
                created_at="2026-01-26T10:30:00.000Z",
                scam_class=0,
                confidence_bps=CONFIDENCE_BPS_MIN - 1
            )
        
        # Invalid: above maximum
        with self.assertRaises(PayloadValidationError):
            CanonicalPayload(
                schema_version=1,
                analyzer_type="bert",
                analyzer_version="v1",
                ref_id="550e8400-e29b-41d4-a716-446655440000",
                created_at="2026-01-26T10:30:00.000Z",
                scam_class=0,
                confidence_bps=CONFIDENCE_BPS_MAX + 1
            )


class TestCanonicalization(unittest.TestCase):
    """Test canonicalization rules and determinism."""
    
    def setUp(self):
        """Create a test payload."""
        self.payload = CanonicalPayload(
            schema_version=1,
            analyzer_type="bert",
            analyzer_version="v1",
            ref_id="550e8400-e29b-41d4-a716-446655440000",
            created_at="2026-01-26T10:30:00.000Z",
            scam_class=0,
            confidence_bps=8550
        )
    
    def test_canonical_json_is_deterministic(self):
        """Test that same payload always produces same JSON."""
        json1 = canonicalize_payload(self.payload)
        json2 = canonicalize_payload(self.payload)
        json3 = canonicalize_payload(self.payload)
        
        self.assertEqual(json1, json2)
        self.assertEqual(json2, json3)
    
    def test_canonical_json_has_sorted_keys(self):
        """Test that JSON keys are sorted alphabetically."""
        json_str = canonicalize_payload(self.payload)
        
        # Keys should appear in alphabetical order
        self.assertIn('"analyzerType"', json_str)
        
        # Check order by position
        positions = {
            'analyzerType': json_str.index('"analyzerType"'),
            'analyzerVersion': json_str.index('"analyzerVersion"'),
            'confidenceBps': json_str.index('"confidenceBps"'),
            'createdAt': json_str.index('"createdAt"'),
            'refId': json_str.index('"refId"'),
            'scamClass': json_str.index('"scamClass"'),
            'schemaVersion': json_str.index('"schemaVersion"'),
        }
        
        sorted_positions = dict(sorted(positions.items(), key=lambda x: x[1]))
        sorted_keys = list(sorted_positions.keys())
        
        # Should be alphabetically sorted
        self.assertEqual(sorted_keys, sorted(sorted_keys))
    
    def test_canonical_json_no_whitespace(self):
        """Test that JSON has no unnecessary whitespace."""
        json_str = canonicalize_payload(self.payload)
        
        # Should not contain spaces after colons or commas
        self.assertNotIn(': ', json_str)
        self.assertNotIn(', ', json_str)
        self.assertNotIn('\n', json_str)
        self.assertNotIn('\t', json_str)
    
    def test_canonical_json_no_float(self):
        """Test that no floating point numbers appear in JSON (numeric fields only)."""
        json_str = canonicalize_payload(self.payload)
        
        # Parse JSON and check numeric fields are integers
        import json as json_module
        data = json_module.loads(json_str)
        
        # These fields should be integers, not floats
        self.assertIsInstance(data["schemaVersion"], int)
        self.assertIsInstance(data["scamClass"], int)
        self.assertIsInstance(data["confidenceBps"], int)
        
        # Ensure they're not floats
        self.assertNotIsInstance(data["schemaVersion"], float)
        self.assertNotIsInstance(data["scamClass"], float)
        self.assertNotIsInstance(data["confidenceBps"], float)
    
    def test_optional_field_omitted_when_none(self):
        """Test that optional modelVersion is omitted when None."""
        json_str = canonicalize_payload(self.payload)
        self.assertNotIn('modelVersion', json_str)
    
    def test_optional_field_included_when_set(self):
        """Test that optional modelVersion is included when set."""
        payload = CanonicalPayload(
            schema_version=1,
            analyzer_type="llm",
            analyzer_version="v1",
            ref_id="550e8400-e29b-41d4-a716-446655440000",
            created_at="2026-01-26T10:30:00.000Z",
            scam_class=0,
            confidence_bps=8550,
            model_version="gemma-2b"
        )
        
        json_str = canonicalize_payload(payload)
        self.assertIn('"modelVersion":"gemma-2b"', json_str)


class TestHashing(unittest.TestCase):
    """Test hash computation and verification."""
    
    def setUp(self):
        """Create a test payload."""
        self.payload = CanonicalPayload(
            schema_version=1,
            analyzer_type="bert",
            analyzer_version="v1",
            ref_id="550e8400-e29b-41d4-a716-446655440000",
            created_at="2026-01-26T10:30:00.000Z",
            scam_class=0,
            confidence_bps=8550
        )
    
    def test_hash_is_deterministic(self):
        """Test that same payload always produces same hash."""
        hash1 = compute_payload_hash(self.payload)
        hash2 = compute_payload_hash(self.payload)
        hash3 = compute_payload_hash(self.payload)
        
        self.assertEqual(hash1, hash2)
        self.assertEqual(hash2, hash3)
    
    def test_hash_format_keccak256(self):
        """Test Keccak-256 hash format."""
        hash_value = compute_payload_hash(self.payload, "keccak256")
        
        # Should start with 0x
        self.assertTrue(hash_value.startswith("0x"))
        
        # Should be 66 characters (0x + 64 hex)
        self.assertEqual(len(hash_value), 66)
        
        # Should be valid hex
        int(hash_value, 16)  # Will raise if not valid hex
    
    def test_hash_format_sha256(self):
        """Test SHA-256 hash format."""
        hash_value = compute_payload_hash(self.payload, "sha256")
        
        # Should start with 0x
        self.assertTrue(hash_value.startswith("0x"))
        
        # Should be 66 characters (0x + 64 hex)
        self.assertEqual(len(hash_value), 66)
    
    def test_different_payloads_different_hashes(self):
        """Test that different payloads produce different hashes."""
        payload2 = CanonicalPayload(
            schema_version=1,
            analyzer_type="bert",
            analyzer_version="v1",
            ref_id="550e8400-e29b-41d4-a716-446655440000",
            created_at="2026-01-26T10:30:00.000Z",
            scam_class=0,
            confidence_bps=8551  # Different confidence
        )
        
        hash1 = compute_payload_hash(self.payload)
        hash2 = compute_payload_hash(payload2)
        
        self.assertNotEqual(hash1, hash2)
    
    def test_verify_payload_hash_success(self):
        """Test hash verification with correct hash."""
        hash_value = compute_payload_hash(self.payload)
        
        self.assertTrue(verify_payload_hash(self.payload, hash_value))
    
    def test_verify_payload_hash_failure(self):
        """Test hash verification with incorrect hash."""
        wrong_hash = "0x" + "a" * 64
        
        self.assertFalse(verify_payload_hash(self.payload, wrong_hash))
    
    def test_verify_hash_case_insensitive(self):
        """Test that hash verification is case insensitive."""
        hash_value = compute_payload_hash(self.payload)
        
        self.assertTrue(verify_payload_hash(self.payload, hash_value.upper()))
        self.assertTrue(verify_payload_hash(self.payload, hash_value.lower()))
    
    def test_invalid_algorithm_raises(self):
        """Test that invalid hash algorithm raises error."""
        with self.assertRaises(ValueError):
            compute_payload_hash(self.payload, "md5")


class TestSchemaEvolution(unittest.TestCase):
    """Test schema evolution and backward compatibility."""
    
    def test_get_canonicalizer_version_1(self):
        """Test getting canonicalizer for version 1."""
        canonicalizer = get_canonicalizer_for_version(1)
        self.assertEqual(canonicalizer, canonicalize_payload)
    
    def test_get_canonicalizer_unsupported_version(self):
        """Test getting canonicalizer for unsupported version."""
        with self.assertRaises(ValueError):
            get_canonicalizer_for_version(99)
    
    def test_reconstruct_from_stored(self):
        """Test reconstructing payload from stored dict."""
        stored = {
            "schemaVersion": 1,
            "analyzerType": "bert",
            "analyzerVersion": "v1",
            "refId": "550e8400-e29b-41d4-a716-446655440000",
            "createdAt": "2026-01-26T10:30:00.000Z",
            "scamClass": 0,
            "confidenceBps": 8550
        }
        
        payload = reconstruct_payload_from_stored(stored)
        
        self.assertEqual(payload.schema_version, 1)
        self.assertEqual(payload.analyzer_type, "bert")
        self.assertEqual(payload.confidence_bps, 8550)
    
    def test_reconstruct_preserves_hash(self):
        """Test that reconstructed payload produces same hash."""
        original = CanonicalPayload(
            schema_version=1,
            analyzer_type="bert",
            analyzer_version="v1",
            ref_id="550e8400-e29b-41d4-a716-446655440000",
            created_at="2026-01-26T10:30:00.000Z",
            scam_class=0,
            confidence_bps=8550
        )
        
        original_hash = compute_payload_hash(original)
        
        # Simulate storing and reconstructing
        stored = original.to_dict()
        reconstructed = reconstruct_payload_from_stored(stored)
        reconstructed_hash = compute_payload_hash(reconstructed)
        
        self.assertEqual(original_hash, reconstructed_hash)


class TestFromAnalysisResult(unittest.TestCase):
    """Test creating payload from analysis results."""
    
    def test_from_naive_datetime(self):
        """Test creating payload from naive datetime (assumed UTC)."""
        dt = datetime(2026, 1, 26, 10, 30, 0, 123456)
        
        payload = CanonicalPayload.from_analysis_result(
            ref_id="550e8400-e29b-41d4-a716-446655440000",
            scam_class=0,
            confidence_bps=8550,
            created_at=dt
        )
        
        self.assertEqual(payload.created_at, "2026-01-26T10:30:00.123Z")
    
    def test_from_aware_datetime(self):
        """Test creating payload from timezone-aware datetime."""
        dt = datetime(2026, 1, 26, 10, 30, 0, 123456, tzinfo=timezone.utc)
        
        payload = CanonicalPayload.from_analysis_result(
            ref_id="550e8400-e29b-41d4-a716-446655440000",
            scam_class=0,
            confidence_bps=8550,
            created_at=dt
        )
        
        self.assertEqual(payload.created_at, "2026-01-26T10:30:00.123Z")
    
    def test_microseconds_truncated_to_milliseconds(self):
        """Test that microseconds are truncated to milliseconds."""
        dt = datetime(2026, 1, 26, 10, 30, 0, 999999)  # 999.999 ms
        
        payload = CanonicalPayload.from_analysis_result(
            ref_id="550e8400-e29b-41d4-a716-446655440000",
            scam_class=0,
            confidence_bps=8550,
            created_at=dt
        )
        
        # Should be truncated to 999ms
        self.assertEqual(payload.created_at, "2026-01-26T10:30:00.999Z")


class TestValidateAgainstSchema(unittest.TestCase):
    """Test schema validation function."""
    
    def test_valid_data(self):
        """Test validation of valid data."""
        is_valid, errors = validate_against_schema(EXAMPLE_PAYLOAD_V1)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_valid_data_with_llm(self):
        """Test validation of valid data with LLM fields."""
        is_valid, errors = validate_against_schema(EXAMPLE_PAYLOAD_V1_WITH_LLM)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_missing_required_field(self):
        """Test validation catches missing required fields."""
        data = deepcopy(EXAMPLE_PAYLOAD_V1)
        del data["scamClass"]
        
        is_valid, errors = validate_against_schema(data)
        
        self.assertFalse(is_valid)
        self.assertTrue(any("scamClass" in e for e in errors))
    
    def test_invalid_field_value(self):
        """Test validation catches invalid field values."""
        data = deepcopy(EXAMPLE_PAYLOAD_V1)
        data["confidenceBps"] = 99999  # Out of range
        
        is_valid, errors = validate_against_schema(data)
        
        self.assertFalse(is_valid)
        self.assertTrue(any("confidenceBps" in e for e in errors))


class TestJsonSchema(unittest.TestCase):
    """Test JSON schema generation."""
    
    def test_schema_has_required_fields(self):
        """Test that JSON schema lists required fields."""
        schema = get_json_schema()
        
        required = schema.get("required", [])
        
        self.assertIn("schemaVersion", required)
        self.assertIn("analyzerType", required)
        self.assertIn("refId", required)
        self.assertIn("scamClass", required)
        self.assertIn("confidenceBps", required)
    
    def test_schema_has_optional_model_version(self):
        """Test that modelVersion is defined but not required."""
        schema = get_json_schema()
        
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        
        self.assertNotIn("modelVersion", required)
        self.assertIn("modelVersion", properties)


def run_tests():
    """Run all Phase 1 tests and return success status."""
    print("\n" + "=" * 70)
    print("     PHASE 1 TESTS - Canonical Payload Schema and Hashing")
    print("=" * 70 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCanonicalPayloadValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestCanonicalization))
    suite.addTests(loader.loadTestsFromTestCase(TestHashing))
    suite.addTests(loader.loadTestsFromTestCase(TestSchemaEvolution))
    suite.addTests(loader.loadTestsFromTestCase(TestFromAnalysisResult))
    suite.addTests(loader.loadTestsFromTestCase(TestValidateAgainstSchema))
    suite.addTests(loader.loadTestsFromTestCase(TestJsonSchema))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL PHASE 1 TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
