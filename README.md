# Project Name - TBD

## The Enterprise AI-Risk & Governance Pre-Flight Checker

A low-cost, automated system designed to help early-stage B2B startups unblock enterprise sales deals without taking on catastrophic legal liability.

## The Problem

When a small software startup lands a pilot with a highly regulated enterprise, such as a bank, insurance company, or hospital, the deal often stalls at the procurement phase.

The enterprise security team sends the founder a 150-question security and AI-risk assessment.

Startups then face a dilemma:

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

#### 1. Ingestion

The user connects their raw, unorganized technical materials, including:

- Architecture documents
- API specifications
- Markdown files
- System design notes
- Security policies
- Codebase documentation
- Configuration references

The system parses these materials into a structured **Technical State Map**, a lightweight JSON database of verified engineering facts.

#### 2. Deterministic Verification

The user uploads the blank enterprise questionnaire.

The system checks each question against the Technical State Map using a strict policy:

> **No explicit technical evidence = no positive claim.**

**If evidence exists**

The system drafts a professional response and appends a citation pointing directly to the source file that proves the claim.

**If evidence is missing**

The system blocks the answer and refuses to fabricate compliance.

---

#### 3. Gap Export

The system outputs two key deliverables:

**A. Completed Compliance Document**

A buyer-ready compliance questionnaire containing only verified answers with supporting evidence citations.

**B. Compliance Deficit Report**

A structured report detailing:

- Which requirements could not be verified
- Which controls are missing
- Why the system refused to answer
- What technical work is needed
- The exact engineering tasks required to close each gap

### What should set us apart / makes this unique

This product captures early-stage founders at their moment of highest pain: a blocked enterprise revenue deal.

These startups are not yet mature enough to purchase expensive compliance platforms, but they urgently need a credible way to respond to enterprise security reviews.

#### Tech Stack

The system can be built using standard web and database components, such as:

- Next.js
- Python/FastAPI
- Supabase
- Object storage
- Lightweight RAG pipelines (I'm thinking OpenAI 
- Structured JSON state mapping

The estimated infrastructure cost to serve a single user should only be a few bucks a month.

#### TLDR

This is not an AI compliance writer.

It is a **truth-preserving enterprise security pre-flight checker** for startups that need to pass procurement without lying, guessing, or exposing themselves to catastrophic liability.
