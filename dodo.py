import re
import subprocess
from pathlib import Path

from doit.task import Task
from doit.tools import create_folder

PACKAGE = "clipsmith"

BADGES_PATH = Path("badges")
PYTEST_BADGE = BADGES_PATH / "tests.svg"
COV_BADGE = BADGES_PATH / "cov.svg"

OUT_PATH = Path("__out__")

TESTS_PATH = OUT_PATH / "tests"
JUNIT_PATH = TESTS_PATH / "junit.xml"
COV_PATH = TESTS_PATH / "cov"

COV_HTML_PATH = COV_PATH / "html"
COV_XML_PATH = COV_PATH / "coverage.xml"


def task_pytest():
    """
    Run pytest and generate coverage reports.
    """

    args = [
        "pytest",
        f"--cov={PACKAGE}",
        f"--cov-report=html:{COV_HTML_PATH}",
        f"--cov-report=xml:{COV_XML_PATH}",
        f"--junitxml={JUNIT_PATH}",
    ]

    return Task(
        "pytest",
        actions=[
            (create_folder, [COV_PATH]),
            # run pytest
            " ".join(args),
        ],
        targets=[
            f"{COV_HTML_PATH}/index.html",
            COV_XML_PATH,
            JUNIT_PATH,
        ],
        file_dep=[],
        clean=True,
    )


def task_badges():
    """
    Generate badges from coverage results.
    """

    gen_tests = [
        "genbadge",
        "tests",
        f"-i {JUNIT_PATH}",
        f"-o {PYTEST_BADGE}",
    ]

    gen_cov = [
        "genbadge",
        "coverage",
        f"-i {COV_XML_PATH}",
        f"-o {COV_BADGE}",
    ]

    return Task(
        "badges",
        actions=[
            (create_folder, [BADGES_PATH]),
            " ".join(gen_tests),
            " ".join(gen_cov),
        ],
        targets=[
            PYTEST_BADGE,
            COV_BADGE,
        ],
        file_dep=[
            JUNIT_PATH,
            COV_XML_PATH,
        ],
    )


def task_format() -> Task:
    """
    Run formatters.
    """

    autoflake_args = [
        "autoflake",
        "--remove-all-unused-imports",
        "--remove-unused-variables",
        "-i",
        "-r",
        ".",
    ]

    isort_args = [
        "isort",
        ".",
    ]

    black_args = [
        "black",
        ".",
    ]

    toml_sort_args = [
        "toml-sort",
        "-i",
        "pyproject.toml",
    ]

    return Task(
        "format",
        actions=[
            " ".join(autoflake_args),
            " ".join(isort_args),
            " ".join(black_args),
            " ".join(toml_sort_args),
        ],
        targets=[],
        file_dep=[],
    )


def task_doc() -> Task:
    """
    Generate CLI documentation in .md format.
    """

    def include(md_path: Path):
        """
        Include this md file in <README.md>.
        """
        assert md_path.exists()

        readme_path = Path("README.md")
        match_start = f"<!-- include {md_path} -->"
        match_end = "<!-- include end -->"

        # read the content to include
        content = md_path.read_text()

        # read README.md
        readme = readme_path.read_text()

        # find and replace between the markers
        pattern = f"{re.escape(match_start)}.*?{re.escape(match_end)}"
        replacement = f"{match_start}\n{content}\n{match_end}"
        new_readme = re.sub(pattern, replacement, readme, flags=re.DOTALL)

        # write back
        readme_path.write_text(new_readme)

    def gen_cli():
        # list of commands for which to generate help docs
        CMDS = [
            ["forge"],
        ]

        doc_path = Path("doc/cli")
        doc_path.mkdir(parents=True, exist_ok=True)

        # generate .md for each command
        for cmd in CMDS:
            args = ["clipsmith"] + cmd + ["--help"]
            filename = f"{'-'.join(cmd) or 'main'}.md"

            stdout = subprocess.check_output(args, text=True)
            markdown = f"```\n{stdout}\n```"

            md_path = doc_path / filename

            with md_path.open("w") as fh:
                fh.write(markdown)

            # replace in readme
            include(md_path)

    return Task(
        "doc",
        actions=[gen_cli],
        targets=[],
        file_dep=[],
    )
