# Contributing to SATOR eXe

Thank you for your interest in contributing to SATOR eXe! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project and everyone participating in it is governed by our commitment to:

- Being respectful and inclusive
- Welcoming newcomers and helping them learn
- Focusing on constructive feedback
- Prioritizing the user experience

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/sator-exe.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`

## How to Contribute

### Reporting Bugs

Before creating a bug report, please check existing issues. When creating a bug report, include:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected vs actual behavior
- Screenshots (if applicable)
- Browser/environment details

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. Include:

- A clear use case
- Detailed description of the proposed feature
- Potential implementation approach
- Mockups or examples (if applicable)

### Pull Requests

1. Ensure your code follows our coding standards
2. Update documentation as needed
3. Add tests for new functionality
4. Ensure all tests pass
5. Update CHANGELOG.md with your changes

## Development Workflow

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

## Coding Standards

### HTML/CSS

- Use semantic HTML5 elements
- Follow BEM naming convention for CSS classes
- Maintain consistent indentation (2 spaces)
- Use CSS custom properties for theming

### JavaScript

- Use ES6+ features
- Follow Airbnb JavaScript Style Guide
- Write modular, reusable code
- Add JSDoc comments for functions

### File Organization

```
radiantx-static/
├── system/          # Core CSS/JS
├── profiles/        # Profile-specific pages
├── assets/          # Images, fonts, etc.
└── docs/            # Documentation
```

## Commit Message Guidelines

Use conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process or auxiliary tool changes

Examples:
```
feat(analytics): add heatmap visualization
fix(launchpad): resolve navigation bug on mobile
docs(readme): update installation instructions
```

## Pull Request Process

1. Update the README.md or relevant documentation with details of changes
2. Ensure your PR description clearly describes the problem and solution
3. Link any relevant issues
4. Request review from maintainers
5. Address review feedback promptly

## Questions?

Feel free to open an issue for questions or join our community discussions.

Thank you for contributing to SATOR eXe!
