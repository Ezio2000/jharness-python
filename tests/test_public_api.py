from __future__ import annotations

import importlib

import conformance
import jharness.kernel as kernel
import jharness.kernel.diagnostics as diagnostics
import jharness.kernel.wire as wire
import jharness.providers as providers
import jharness.toolkit as toolkit


def test_package_all_exports_exist() -> None:
    for module in (kernel, toolkit, diagnostics, wire, conformance):
        exports = set(module.__all__)
        assert exports
        assert all(hasattr(module, name) for name in exports)
    assert providers.__all__ == []


def test_kernel_root_contains_the_documented_protocol_families() -> None:
    required = {
        "Runtime",
        "Invocation",
        "Checkpoint",
        "RunSnapshot",
        "Planning",
        "ToolsPending",
        "Suspended",
        "Completed",
        "Failed",
        "Limited",
        "RunRepository",
        "Model",
        "ToolCatalogProvider",
        "ApprovalPolicy",
        "HistoryReducer",
        "BatchPolicy",
    }
    assert required <= set(kernel.__all__)
    assert {"build_trace", "verify_trace", "RunTrace"} <= set(diagnostics.__all__)
    assert {"encode_checkpoint", "decode_checkpoint", "StartRequest"} <= set(wire.__all__)


def test_only_documented_provider_namespaces_are_public() -> None:
    for namespace in (
        "jharness.providers.openai",
        "jharness.providers.anthropic",
        "jharness.providers.deepseek",
    ):
        module = importlib.import_module(namespace)
        assert module.__all__
        assert all(hasattr(module, name) for name in module.__all__)
    for implementation in (
        "jharness.providers.openai.chat_completions",
        "jharness.providers.anthropic.messages_api",
    ):
        assert importlib.import_module(implementation).__all__ == []
