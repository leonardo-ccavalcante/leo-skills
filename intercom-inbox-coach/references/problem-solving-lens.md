# Problem-solving lens

This is the embedded edition of the team's problem-solving coach: McKinsey-style problem structuring and communication, the Structured Analytic Techniques (SATs) from the CIA Tradecraft Primer, and the adaptability mindsets. It carries the same frameworks as the standalone coach. The difference is the order of work. The standalone coach guides one person through one problem in dialogue and avoids solving it for them. Here a teammate arrives with dozens or thousands of tickets and no time to build an issue tree, so you do the structuring legwork first, show your reasoning, and then return to coaching with questions that hand the judgment back.

## Contents

1. What good looks like
2. Define the problem
3. Structure it: the issue tree
4. Prioritize: effort classes
5. Challenge it: SATs and biases
6. Synthesize: the Pyramid Principle
7. Coach: questions and mindsets
8. Using the lens on a single ticket

## 1. What good looks like

All good problem solving shares five traits. Check the review against them before delivering it, and name the gap when one is missing.

1. **A well-defined problem.** One question the analysis answers.
2. **Impact orientation.** Effort goes where it changes outcomes for customers and the team, not where the data happens to be rich.
3. **Stakeholder perspective.** The customer, the teammate, the next shift, the teams we depend on.
4. **Fact base.** Counts from the script, quotes from the conversations, and a clear line between what was read and what was inferred.
5. **Synthesis.** The "so what", not a recital of findings.

Balance divergent and convergent thinking: open up when looking for explanations and options, close down when choosing what to do in the next hour.

## 2. Define the problem

Write one SMART problem question before analyzing: specific, measurable, action-oriented, relevant, time-bound. It keeps the review from turning into a tour of the inbox.

Pattern: *What must happen in [time frame] so that [measurable outcome] for [inbox or teammate], given [constraint]?*

- "What must Ana do in the next four hours so that no customer in her inbox waits more than 24 hours and the three breached conversations move forward, given she is alone on shift?"
- "Which two changes would cut the 400 conversations open for over a week in the Billing inbox by half this month, without adding headcount?"

If the teammate's goal is unclear, propose the question and ask them to correct it. A wrong question answered well is the most expensive mistake in the whole process.

## 3. Structure it: the issue tree

Break the question into parts that are MECE: mutually exclusive (no ticket sits in two branches) and collectively exhaustive (every ticket has a home). Three to five main branches.

For an inbox, the most useful first cut is **what the ticket is waiting on**, because each branch calls for a different kind of action:

```
Why are these conversations not resolved?
├─ 1. Waiting on us            the teammate has the ball: capacity, prioritization, avoidance
├─ 2. Waiting on the customer  missing information, no reply, unclear request
├─ 3. Waiting on another team  engineering bug, product decision, rights or legal review, billing provider
├─ 4. Knowledge or policy gap  no macro, no article, ambiguous policy, teammate unsure what is allowed
├─ 5. Relationship difficulty  frustration, repeat contacts, escalation threats, a no that has to be delivered
└─ 6. Process or routing       misrouted, wrong tier, duplicates, should have been resolved by self-service or the AI agent
```

Rules for building it:

- Put each ticket in the branch of its *binding* constraint, the one thing that, if removed, would let it move. A frustrated customer whose bug is unfixed belongs in branch 3; the frustration is handled in the Carnegie pass.
- Use the team's existing tags and tiers for the second level (branch 3 split by reason tag, for example). Do not invent a parallel taxonomy.
- Attach numbers and two or three example tickets to every branch. A branch without evidence is a guess.
- Adapt the first cut when the question demands it. A lead asking "why is this backlog growing?" may be better served by inflow, throughput and rework. Keep it MECE either way.
- Show the tree as an indented list. It should be readable in ten seconds.

The tree answers the teammate's first request: where the biggest difficulties are. Say which one or two branches hold most of the pain and why that matters.

## 4. Prioritize: effort classes

Sort tickets by impact and effort into four classes. The definitions and the tier rules come from `workspace-config.md` sections 6 and 7; the defaults are:

| Class | Test | What to do |
|---|---|---|
| **Quick win** | Clear policy or macro, no dependency, under 15 minutes, cheap to get wrong | Do now, in order of who has waited longest. |
| **Needs evaluation** | Depends on another team, policy ambiguous or missing, high-value customer, recurring pattern, legal, security or reputation risk, conflicting information | State what is unclear, what to find out, and who can help. Do not rush it. |
| **Batchable** | Several near-identical tickets one decision or fix would resolve | Solve once. Propose the macro, the article or the bug escalation that closes them together. |
| **Park** | Nothing useful to do until a known date or event | Make sure a snooze and a customer expectation are both set. |

Impact first: waiting time against thresholds, priority and SLA status, reopens, customer value, and downside risk. A quick win for a customer who has waited two days beats a quick win that arrived ten minutes ago.

Batchable is where a review pays for itself. Thirty tickets with the same cause are one problem, not thirty, and should be reported that way, with the upstream fix named.

## 5. Challenge it: SATs and biases

SATs externalize thinking so it can be seen and criticized. In an inbox review, use them lightly and visibly: a few lines in the report, not a ceremony. Always run the first two. Reach for the others when the situation calls for them.

| Technique | Family | Use it in the inbox when |
|---|---|---|
| **Key Assumptions Check** | Diagnostic | Always. List the assumptions under your top conclusions: "the tag reflects the real cause", "the sample represents the inbox", "no reply means resolved", "the bug ticket is still open". Mark each as solid, plausible or unsupported. |
| **Quality of Information Check** | Diagnostic | Always. Coverage, sampling, missing tags, stale fields, numbers that are approximate. |
| **Indicators / Signposts** | Diagnostic | Closing the report: what to watch next shift that would confirm or overturn the picture. |
| **Analysis of Competing Hypotheses (ACH)** | Diagnostic | A pattern has several possible causes (spike in refund requests: pricing change, billing bug, or a confusing email?). List hypotheses, weigh evidence against each, and favor the one with the least disconfirming evidence, not the most support. |
| **Devil's Advocacy** | Contrarian | Your main recommendation feels obvious. Argue the opposite for three lines and see what survives. |
| **Team A / Team B** | Contrarian | Two defensible readings of a contested ticket or policy. Lay out both cases before advising. |
| **High-Impact / Low-Probability** | Contrarian | Always scan for the one ticket that could blow up: legal threat, rights holder, press, security or data exposure, a large account. Low odds, high cost. Flag it even if it ranks low. |
| **What If? Analysis** | Contrarian | "What if engineering does not ship the fix this week?" Work backward to what the teammate should tell customers today. |
| **Brainstorming** | Imaginative | A batch needs a new approach and the usual macro is not working. |
| **Outside-In Thinking** | Imaginative | The pattern may come from outside support: a release, a pricing change, a partner, a seasonal event. |
| **Red Team** | Imaginative | Rarely. Abuse, fraud or someone gaming a policy: think as they do. |
| **Alternative Futures** | Imaginative | Rarely. Lead-level planning under real uncertainty, such as staffing around a launch. |

**Biases to watch in yourself and to raise gently with the teammate:**

| Bias | How it shows up here | Counter |
|---|---|---|
| Confirmation bias | Reading the sample to support the first story you formed | ACH; look for disconfirming tickets on purpose |
| Anchoring | The first angry ticket colors the whole review | Let the script's numbers set the frame before reading threads |
| Status quo bias | "This inbox is always like this" | What If?; compare with the lookback window |
| Wishful thinking | Assuming the fix ships or the customer will reply | Key Assumptions Check |
| Mirror imaging | Assuming the customer reasons like a support agent | The Carnegie lens: their point of view, in their words |
| Availability | Overweighting the loudest customers over the silent long-waiters | The attention ranking, which does not care who shouts |
| Sampling bias | Drawing inbox-wide conclusions from the worst cases you chose to read | The random picks in the sample; an honest coverage statement |

## 6. Synthesize: the Pyramid Principle

Lead with the answer. A summary lists facts; a synthesis says what they mean together and what to do about it. Always push from the first to the second.

```
Governing Thought   the one-sentence answer to the problem question
├─ Key Line 1       supported by numbers and tickets
├─ Key Line 2       supported by numbers and tickets
└─ Key Line 3       supported by numbers and tickets
```

Weak (summary): "There are 62 open conversations, 14 waiting over 24 hours, 9 tagged billing."

Strong (synthesis): "Your inbox is healthy except for one cluster: 9 of the 14 conversations past 24 hours are the same double-charge issue, so one refund macro and one note to Billing clears most of your risk before lunch."

Key lines should be parallel, independent and few. Choose the storyline for the audience: a teammate needs "what do I do now", a lead needs "what is the pattern and what fixes it upstream".

## 7. Coach: questions and mindsets

After delivering the structure, facilitate. The teammate knows these customers and this product, and the frameworks are scaffolding for their judgment, not a replacement for it. Ask powerful questions, offer the framework as structure, celebrate iterative progress.

Questions that work after a review:

- "Which of my assumptions is most likely wrong, from where you sit?"
- "If you could only move three tickets today, which three, and what does that tell you about the rest?"
- "What would have to be true for this batch to disappear for good?"
- "What pattern do you see here that the tags are not capturing?"

**Mindsets.** Adaptability is a state, not a trait, so it can be developed. The seven pairs: Fixed and Growth, Expert and Curious, Reactive and Creative, Victim and Agent, Scarcity and Abundance, Certainty and Exploration, Protection and Opportunity. Queue pressure pulls people toward the first of each pair ("this inbox never ends", "engineering never answers", "nothing I can do"). When you hear it, name it with care and offer a reframing question, never an order.

**APR, used lightly:**

1. **Awareness.** Help them name their current state: "It sounds like the queue feels unwinnable right now. Is that fair?"
2. **Pause.** A short reset before deciding. One breath, one glass of water, two minutes away from the inbox. Say it in one sentence, without preaching.
3. **Reframe.** A question that reopens agency: "What part of this is fully in your hands in the next hour?" (Victim to Agent.) "What would you try if this were an experiment?" (Certainty to Exploration.) "Who already solved something like this?" (Scarcity to Abundance.)

**Learning intentions and performance goals.** Someone new to a tier or a product area is building a skill, so focus on the journey: "handle two rights requests with a colleague reviewing". Someone experienced is performing, so focus on the result: "clear the breached conversations by 3 pm". Use the right frame for the person.

Signal when you notice reactive mode and creative mode, and never at the cost of getting the urgent tickets answered first.

## 8. Using the lens on a single ticket

For a Ticket Deep-Dive with an analytical knot:

1. Problem question for this ticket: "What would let us resolve Marta's double charge today?"
2. A small tree: what we know, what we do not know, what we depend on.
3. Key Assumptions Check: the two or three beliefs the plan rests on, and the cheapest way to verify the shakiest.
4. If several explanations compete, a three-line ACH.
5. A recommendation in pyramid form: the answer, the reasons, the next step.
6. One coaching question that hands it back.
