from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

from ci.validate_agent_workflow import validate_agent_workflow


SIGNATURE_ERROR = "build_graph must use: def build_graph(*, middleware=())"
TOP_LEVEL_ERROR = "agent.py must define exactly one top-level build_graph function"
GRAPH_EXPORT_ERROR = "agent.py must define exactly: graph = build_graph()"


def write_agent(root: Path, source: str) -> None:
    """Write an agent module without importing or executing it."""
    (root / "agent.py").write_text(dedent(source), encoding="utf-8")


class ValidateAgentWorkflowTests(unittest.TestCase):
    def test_accepts_annotated_build_graph_without_importing_agent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_agent(
                root,
                """
                raise AssertionError("agent.py must not be imported")

                def build_graph(
                    *,
                    middleware: Sequence[AgentMiddleware[Any, Any]] = (),
                ) -> object:
                    return middleware

                graph = build_graph()
                """,
            )

            validate_agent_workflow(root)

    def test_rejects_invalid_build_graph_signatures(self) -> None:
        invalid_signatures = {
            "async-function": "async def build_graph(*, middleware=()): pass",
            "positional-only-argument": (
                "def build_graph(value, /, *, middleware=()): pass"
            ),
            "positional-middleware": "def build_graph(middleware=()): pass",
            "varargs": "def build_graph(*args, middleware=()): pass",
            "missing-middleware": "def build_graph(): pass",
            "extra-keyword-only-argument": (
                "def build_graph(*, middleware=(), extra=None): pass"
            ),
            "missing-default": "def build_graph(*, middleware): pass",
            "none-default": "def build_graph(*, middleware=None): pass",
            "nonempty-tuple-default": (
                "def build_graph(*, middleware=(None,)): pass"
            ),
            "constructed-tuple-default": (
                "def build_graph(*, middleware=tuple()): pass"
            ),
            "kwargs": "def build_graph(*, middleware=(), **kwargs): pass",
        }

        for name, source in invalid_signatures.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                write_agent(root, source)

                with self.assertRaises(TypeError) as raised:
                    validate_agent_workflow(root)

                self.assertEqual(str(raised.exception), SIGNATURE_ERROR)

    def test_requires_exactly_one_top_level_build_graph(self) -> None:
        invalid_definitions = {
            "missing": "graph = None",
            "nested-only": """
                def factory():
                    def build_graph(*, middleware=()):
                        pass
                """,
            "duplicate": """
                def build_graph(*, middleware=()):
                    pass

                def build_graph(*, middleware=()):
                    pass
                """,
        }

        for name, source in invalid_definitions.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                write_agent(root, source)

                with self.assertRaises(ValueError) as raised:
                    validate_agent_workflow(root)

                self.assertEqual(str(raised.exception), TOP_LEVEL_ERROR)

    def test_requires_exact_graph_export(self) -> None:
        invalid_exports = {
            "missing": """
                def build_graph(*, middleware=()):
                    pass
            """,
            "arguments": """
                def build_graph(*, middleware=()):
                    pass

                graph = build_graph(middleware=())
            """,
        }

        for name, source in invalid_exports.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                write_agent(root, source)

                with self.assertRaises(ValueError) as raised:
                    validate_agent_workflow(root)

                self.assertEqual(str(raised.exception), GRAPH_EXPORT_ERROR)

    def test_requires_agent_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            with self.assertRaises(FileNotFoundError) as raised:
                validate_agent_workflow(root)

            self.assertEqual(
                str(raised.exception),
                f"agent.py not found at {root / 'agent.py'}",
            )

    def test_rejects_invalid_python(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_agent(root, "def build_graph(:\n")

            with self.assertRaises(SyntaxError):
                validate_agent_workflow(root)


if __name__ == "__main__":
    unittest.main()
