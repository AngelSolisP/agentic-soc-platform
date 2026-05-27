# Contributing to Agentic SOC

Thanks for your interest. This project welcomes contributions in three categories:

## What we want

1. **Research extensions** — new agents, new ICM contracts, evals, interpretability tooling
2. **Bug fixes** — failing tests, broken edge cases, security issues
3. **Documentation** — clarifications, examples, deployment guides for other clouds

## What we don't want (without discussion first)

- Refactors that change the agent topology
- Replacing ADK with another framework
- Adding new LLM providers
- Removing HITL guards or cost guards

Open an issue first if you're unsure.

## Development setup

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cp .mcp.json.example .mcp.json
```

Fill in `.env` and `.mcp.json` with your own GCP project + Chronicle tenant + VirusTotal API key.

## Running tests

```bash
.venv/bin/python -m pytest tests/ -x -q
```

All PRs must keep the test suite green. Add tests for new behavior.

## Running evals

```bash
.venv/bin/python -m pytest evals/ -x -q -m mock      # Tier 1 — mocked MCP, free
.venv/bin/python -m pytest evals/ -x -q -m live      # Tier 2 — live MCP, costs $
```

## Coding standards

- Python 3.11+, type hints required on new public functions
- Format with `ruff format`, lint with `ruff check`
- No `# type: ignore` without a comment explaining why
- New agents must register their tools in `agents/tool_catalog.py` and provide a CONTRACT section in their runbook

## Security

If you find a vulnerability, **do not open a public issue**. Email the maintainer directly. See [SECURITY.md](SECURITY.md).

## Pull request checklist

- [ ] Tests pass: `pytest tests/ -x -q`
- [ ] New behavior is tested
- [ ] If touching agents: ICM contract updated, tool scope updated
- [ ] If touching infra: terraform plan included in PR description
- [ ] If touching MCP Gateway: load tested with `scripts/test_mcp_live.py`

## License

By submitting a PR, you agree your contribution is licensed under Apache 2.0.
