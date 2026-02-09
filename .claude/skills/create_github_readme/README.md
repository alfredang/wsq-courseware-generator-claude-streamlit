# Create GitHub README

[![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-blueviolet)](https://docs.anthropic.com/en/docs/claude-code)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Generate professional GitHub README.md files following open standards with tech badges, architecture diagrams, setup instructions, and acknowledgements.

## Installation

Install this skill using the Claude Code CLI:

```bash
npx @anthropic-ai/claude-code skills add /path/to/create_github_readme
```

Or install from a GitHub repository:

```bash
npx @anthropic-ai/claude-code skills add https://github.com/username/create_github_readme
```

## Usage

Once installed, trigger the skill in Claude Code using:

```
/create_github_readme
```

Or use natural language:
- "create a readme for my project"
- "generate github readme"
- "write project documentation"

## Features

The generated README includes:

| Section | Description |
|---------|-------------|
| **Header** | Project name, badges, tagline, quick links |
| **About** | Project description and key features |
| **Tech Stack** | Technologies with shields.io badges |
| **Architecture** | System diagram in ASCII art |
| **Project Structure** | File/folder organization tree |
| **Getting Started** | Prerequisites, installation, running |
| **Deployment** | Docker and cloud platform instructions |
| **Contributing** | Fork and PR workflow guide |
| **Acknowledgements** | Credits and attribution |

## Skill Structure

```
create_github_readme/
├── SKILL.md        # Skill definition and instructions
├── README.md       # This file
├── examples.md     # Example prompts and outputs
└── scripts/        # Automation scripts (optional)
```

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) with an active subscription
- Node.js 18+ (for npx installation)

## Keywords

`readme` `github readme` `create readme` `generate readme` `project readme` `documentation` `readme.md` `update readme` `write readme` `project documentation`

## License

MIT
