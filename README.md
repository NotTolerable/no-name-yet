# Project Name - TBD

## The Enterprise AI-Risk & Governance Pre-Flight Checker

A low-cost, automated system designed to help early-stage B2B startups unblock enterprise sales deals without taking on catastrophic legal liability.

## The Problem

When a small software startup lands a pilot with a highly regulated enterprise, such as a bank, insurance company, or hospital, the deal often stalls at the procurement phase.

The enterprise security team sends the founder a 150-question security and AI-risk assessment.

The startups with limited man-power then face a dilemma:

#### 1. Expensive Solutions

They cannot afford enterprise compliance platforms such as Vanta or Conveyor, which can cost $10,000+ per year, just to close their first few enterprise deals.

#### 2. AI Hallucinations

If they use generic LLM tools to auto-fill the questionnaire, the AI may confidently guess or fabricate answers to make the startup appear compliant.

Examples include falsely claiming that:

- Database fields are encrypted
- Model prompts are scrubbed of PII
- Access controls are fully implemented
- Audit logs are retained according to enterprise policy

Signing an enterprise contract that contains a false security claim can create serious contractual liability for the company.

## The Solution

Instead of acting as a reckless auto-fill bot, this tool functions as a strict, programmatic **Gap Analyzer**.

It maps the startup’s actual technical state, answers only what it can safely prove, and explicitly refuses to make unsupported claims when evidence is missing.

When a required security control is absent, the system outputs a clear **Compliance Deficit** and converts the gap into an actionable engineering ticket so the team knows exactly what to build to save the deal.

## How It Works: The Data Pipeline

```text
[Raw Engineering Docs] ─┐
[Codebase Specs]        ├──▶ ┌───────────────────────────┐ ───▶ [Buyer’s Questionnaire]
[API Configurations] ───┘    │    VERIFICATION ENGINE    │
                             └─────────────┬─────────────┘
                                           │
                          ┌────────────────┴────────────────┐
                          ▼                                 ▼
                  [Verified Claims]               [Compliance Deficits]
                  • Automated Drafts              • Programmatic Refusals
                  • Evidence Citations            • Urgent Engineering Tasks
```

**1. Ingestion**: The user connects their raw, unorganized technical files (architecture docs, API specifications, markdown files, or system specs). The system parses these materials into a structured Technical State Map (a lightweight JSON database of verified engineering facts).

**2. Deterministic Verification (RAG)**: The user uploads the blank questionnaire. The system checks each question against the Technical State Map using a strict policy: No explicit technical evidence = No positive claim.

- **If evidence exists**: The system drafts a professional response and appends a citation pointing directly to the source file that proves the claim.
- **If evidence is missing**: The system blocks the answer and refuses to fabricate compliance.

**3. Gap Export**

The system outputs two key deliverables:

**Completed Compliance Document**

A buyer-ready compliance questionnaire containing only verified answers with supporting evidence citations.

**Compliance Deficit Report**

A structured report detailing:

- Which requirements could not be verified
- Which controls are missing
- Why the system refused to answer
- What technical work is needed
- The exact engineering tasks required to close each gap

#### Tech Stack

This is what I was thinking for the tech-stack, but we can explore other options:

- Next.js
- Python/FastAPI
- Supabase
- Object storage
- Lightweight RAG pipelines (I'm thinking OpenAI or Gemini)
- Structured JSON state mapping

The estimated infrastructure cost to serve a single user should only be a few bucks a month.
