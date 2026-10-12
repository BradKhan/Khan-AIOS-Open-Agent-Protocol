<p align="center">
  <img src="assets/open-ass-donkey.png" alt="A grinning gold pixel-art donkey, looking back over its shoulder" width="210">
</p>

# Open ASS

### Open Agent Software System

**Get your ASS together.**

AI agents can write an entire application in minutes. Getting them to build the *right* thing, make it look good, write like a human, work together, catch their mistakes, and ship something worth using?

**Still a pain in the ass.**

Every new project seems to start the same way. Configure your agents. Install your favorite skills. Write another set of instructions. Explain your architecture for the fifth time. Then spend hours fixing ugly interfaces, rewriting robotic copy, and debugging code that was supposedly finished.

Switch models, lose context, add another agent, and repeat.

I built Open ASS because I got tired of rebuilding the development process every time I wanted to build something.

**It's a ready-made, open-source development system that brings the tools, skills, and practices of good software engineering into one GitHub repository.**

You bring the idea and your preferred AI agents. Open ASS gives them a common way to work, from figuring out what to build through design, implementation, testing, and release.

The aim is simple: spend more time building useful software and less time managing the machinery around it.

## Good software takes more than good code

An application can compile perfectly and still be terrible.

The requirements were misunderstood. The interface looks like every other AI-generated dashboard. The copy reads like a cyborg having an identity crisis. Something important breaks the moment a user does anything unexpected.

Open ASS addresses the whole development process.

### Engineering

Clear requirements, sensible architecture, structured development, systematic debugging, testing, and code review.

The framework draws on GitHub Spec Kit, Superpowers, Sentry, and established engineering practices. Small changes can move quickly. Riskier work gets more scrutiny.

There's a process for getting things done, without making every bug fix feel like a government procurement exercise.

### Design

Nobody wants another dashboard full of purple gradients, meaningless cards, and buttons that look pretty but don't do anything useful.

Open ASS brings together Taste, Impeccable, Vercel's Web Interface Guidelines, React best practices, and frontend design skills.

These give agents better guidance for visual identity, usability, accessibility, performance, and the details that separate a working interface from a damn good one.

### Writing

Your landing page shouldn't sound like a press release written by a committee of chatbots.

Humanizer and writing practices help cut the buzzword soup, fake enthusiasm, corporate filler, and the relentlessly predictable phrasing that makes AI-generated copy so easy to spot.

That applies to marketing pages, documentation, onboarding, interface text, and everything else users actually read.

### Context and coordination

An agent shouldn't need your entire chat history explained every time it picks up a task.

Open ASS uses Interpretable Context Methodology (ICM) to organize project knowledge, route agents to relevant instructions, and make handoffs inspectable.

Requirements, decisions, and accepted changes live in GitHub. You can change models or involve another developer without losing the project's direction.

### Testing and verification

An agent saying "Done!" doesn't mean the work is done.

Open ASS includes task contracts, automated checks, security review procedures, and GitHub CI. Changes can be evaluated against the original requirements and actual test results.

Agents can propose work and report what happened. Independent checks and authorized reviewers determine whether it's ready.

## What's already in the ASS?

The repository currently includes:

- A GitHub-native development framework with specifications, policies, and risk-based workflows.
- Five curated skill profiles covering engineering, web/design, security, writing, and skill creation.
- 17 pinned external skills with an installer that verifies downloaded files and records their provenance.
- ICM context routing to organize instructions and task handoffs.
- Verification scripts, automated tests, and CI workflows.
- A foundation for adding specialist agents, orchestration, and persistent memory as projects grow.

You don't need to install everything. Pick the capabilities relevant to your project.

The core works with GitHub and Python, without requiring a paid AI service or dedicated orchestration platform. Some external skills need additional tools to unlock their full functionality.

And your workflow stays in your repository, where it won't disappear when the next model comes along.

## Get your ASS up and running

Copy or fork the repository into a project.

Install the development requirements and verify the foundation:

`python3 -m pip install -r requirements-dev.txt`

`python3 scripts/verify.py`

See which skills are available:

`python3 scripts/skills.py list`

Install the core engineering and web/design profiles:

`python3 scripts/skills.py install --profile core --profile web`

Configure your project's actual application tests before relying on the framework to verify its behavior.

[Quickstart](docs/quickstart.md) · [Skills and profiles](docs/skills.md) · [Architecture](docs/architecture.md)

## Built in the open

Open ASS is free, MIT licensed, and under active development.

The framework, skill installer, context routing, and verification system are working. Full integration with different agent runtimes, broader automation, and comparative performance benchmarks are still being developed.

There's plenty to improve. If you find a better engineering practice, a useful skill, or a problem the framework fails to catch, bring it in. Working examples and reproducible tests are especially welcome.

I want this to become the kind of repository you reach for whenever you're starting a software project, because it saves you from setting up and fixing the same things over and over.

**AI can already generate the code. Let's make it better at everything else it takes to ship a damn good product.**

[Contribute](CONTRIBUTING.md) · [Report an issue](https://github.com/BradKhan/open-ASS/issues)

Created by [Brad Khan](https://github.com/BradKhan). MIT licensed.
