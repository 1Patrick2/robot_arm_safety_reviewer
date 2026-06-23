"""Subcommand: ``dataset`` -- dataset adapter commands.

Registers the ``dataset`` subcommand tree with ``list`` and ``export-sequence``
sub-subcommands that interact with the dataset service.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from application.dataset_service import (
    DatasetExportSequenceRequest,
    DatasetListRequest,
    dataset_export_sequence,
    dataset_list,
)
from cli.output import print_dataset_list_result, print_dataset_export_result


def register_dataset_commands(subparsers) -> None:
    """Register the ``dataset`` subcommand and its sub-subcommands."""
    dataset_parser = subparsers.add_parser("dataset", help="Dataset adapter commands")
    dataset_subparsers = dataset_parser.add_subparsers(dest="dataset_command", required=True)

    # dataset list
    list_parser = dataset_subparsers.add_parser("list", help="List available sequences")
    list_parser.add_argument("--adapter", default="mini_sequence", help="Dataset adapter name")
    list_parser.add_argument("--source", default="bench/samples/policy_sequences", help="Dataset source directory")
    list_parser.add_argument("--json", action="store_true")
    list_parser.set_defaults(handler=handle_dataset_list)

    # dataset export-sequence
    export_parser = dataset_subparsers.add_parser("export-sequence", help="Export a single sequence")
    export_parser.add_argument("--adapter", default="mini_sequence", help="Dataset adapter name")
    export_parser.add_argument("--source", default="bench/samples/policy_sequences", help="Dataset source directory")
    export_parser.add_argument("--sequence-id", required=True, help="Sequence ID to export")
    export_parser.add_argument("--output", required=True, help="Output file path")
    export_parser.add_argument("--json", action="store_true")
    export_parser.set_defaults(handler=handle_dataset_export)


def handle_dataset_list(args: argparse.Namespace) -> None:
    """List available sequences from a dataset adapter."""
    result = dataset_list(
        DatasetListRequest(
            adapter_name=args.adapter,
            source=Path(args.source),
        )
    )
    print_dataset_list_result(result, as_json=args.json)


def handle_dataset_export(args: argparse.Namespace) -> None:
    """Export a single sequence from a dataset adapter."""
    result = dataset_export_sequence(
        DatasetExportSequenceRequest(
            adapter_name=args.adapter,
            source=Path(args.source),
            sequence_id=args.sequence_id,
            output=Path(args.output),
        )
    )
    print_dataset_export_result(result, as_json=args.json)
