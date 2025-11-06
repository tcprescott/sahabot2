---
# Fill in the fields below to create a basic custom agent for your repository.
# The Copilot CLI can be used for local testing: https://gh.io/customagents/cli
# To make this agent available, merge this file into the default repository branch.
# For format details, see: https://gh.io/customagents/config

name: default
description: The default agent with some baseline instructions for all changes made.
---

# Default Agent

You are my default agent.  Beyond what you'd normally do, there are a few extra rules we want to follow that take precidence over the copilot instructions file:

1. Do not generate database migrations.  The maintainer will do this when they merge your pull requests.
