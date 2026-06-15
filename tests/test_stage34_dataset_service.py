import json
from pathlib import Path

import pytest

from application.dataset_service import (
    DatasetExportSequenceRequest,
    DatasetListRequest,
    DatasetListResult,
    DatasetExportSequenceResult,
    dataset_list,
    dataset_export_sequence,
)

SAMPLES = Path(__file__).resolve().parents[1] / "samples" / "policy_sequences"


class TestDatasetList:
    def test_lists_expected_ids(self):
        result = dataset_list(
            DatasetListRequest(
                adapter_name="mini_sequence",
                source=SAMPLES,
            )
        )
        assert "simple_safe_sequence_001" in result.sequence_ids
        assert "near_miss_sequence_001" in result.sequence_ids
        assert "collision_sequence_001" in result.sequence_ids
        assert len(result.sequence_ids) == 3

    def test_rejects_unknown_adapter(self):
        with pytest.raises(ValueError, match="unsupported dataset adapter"):
            dataset_list(
                DatasetListRequest(
                    adapter_name="nonexistent",
                    source=SAMPLES,
                )
            )

    def test_list_result_to_dict(self):
        result = DatasetListResult(
            adapter_name="mini_sequence",
            source=SAMPLES,
            sequence_ids=("a", "b"),
        )
        d = result.to_dict()
        assert d["adapter"] == "mini_sequence"
        assert d["sequence_ids"] == ["a", "b"]
        assert d["count"] == 2


class TestDatasetExportSequence:
    def test_exports_sequence_to_file(self, tmp_path):
        output = tmp_path / "exported.json"
        result = dataset_export_sequence(
            DatasetExportSequenceRequest(
                adapter_name="mini_sequence",
                source=SAMPLES,
                sequence_id="simple_safe_sequence_001",
                output=output,
            )
        )
        assert result.sequence_id == "simple_safe_sequence_001"
        assert result.exported_path == output
        assert output.exists()
        payload = json.loads(output.read_text(encoding="utf-8"))
        assert payload["sequence_id"] == "simple_safe_sequence_001"
        assert len(payload["actions"]) == 2

    def test_export_to_app_result(self, tmp_path):
        output = tmp_path / "exported.json"
        result = dataset_export_sequence(
            DatasetExportSequenceRequest(
                adapter_name="mini_sequence",
                source=SAMPLES,
                sequence_id="simple_safe_sequence_001",
                output=output,
            )
        )
        app_result = result.to_app_result()
        assert app_result.ok is True
        assert app_result.mode == "dataset_export_sequence"
        assert app_result.artifacts[0].kind == "exported_sequence"

    def test_export_without_output_keeps_sequence_in_memory(self):
        result = dataset_export_sequence(
            DatasetExportSequenceRequest(
                adapter_name="mini_sequence",
                source=SAMPLES,
                sequence_id="simple_safe_sequence_001",
                output=None,
            )
        )
        assert result.exported_path is None
        assert result.sequence is not None
        assert result.sequence.sequence_id == "simple_safe_sequence_001"

    def test_export_nonexistent_sequence_raises(self):
        with pytest.raises(KeyError):
            dataset_export_sequence(
                DatasetExportSequenceRequest(
                    adapter_name="mini_sequence",
                    source=SAMPLES,
                    sequence_id="does_not_exist",
                )
            )
