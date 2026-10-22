from pyprojkit import (
    ProjectConfig,
    PythonVersions,
    RequiresPython,
    create_recommended_tools,
)

config = ProjectConfig(
    package="clipsmith",
    requires_python=RequiresPython((3, 12)),
    pinned_python=PythonVersions(3, (12, 14)),
    code_paths=("src", "test"),
    tools=create_recommended_tools(),
)
