from pathlib import Path
from string import Template

PROMPTS_DIR = Path(__file__).parent


class PromptNotFoundError(Exception):
    pass


def render_prompt(name: str, **variables: str) -> str:
    """Loads prompts/<name>.md and substitutes $variable placeholders.
    Template (not str.format) deliberately — every prompt in this directory
    includes a literal JSON example in its instructions, and str.format's
    {braces} would collide with that."""
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise PromptNotFoundError(f"No prompt file named {name}.md in {PROMPTS_DIR}")
    template = Template(path.read_text())
    return template.safe_substitute(**variables)
