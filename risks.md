# Goals and risk levels (file B)
Format: `- goal | risk level`

# Source: https://artificialintelligenceact.eu/high-level-summary/ (page updated 31 Aug 2026). Original entries are kept; new entries follow the AI Act categories: Unacceptable (Art. 5), High (Art. 6, Annex I and III), Limited (Art. 50 transparency), Minimal.

## Demo

- Rank job candidates for recruiters | High
- Reject job applicants automatically on the basis of their CVs | High
- Filter job applicants according to their CVs | High
- Summarize candidate CVs | Limited
- Recognize the emotions of employees | Unacceptable
- Answer customer questions about invoices | Minimal

## Unacceptable (prohibited, Art. 5)

- Recognize the emotions of employees | Unacceptable
- Infer emotions of students in educational institutions | Unacceptable
- Deploy subliminal, manipulative or deceptive techniques that distort behaviour and cause significant harm | Unacceptable
- Exploit vulnerabilities related to age, disability or socio-economic circumstances to distort behaviour | Unacceptable
- Infer sensitive attributes (race, political opinions, trade union membership, religious or philosophical beliefs, sex life, sexual orientation) via biometric categorisation | Unacceptable
- Generate non-consensual intimate imagery | Unacceptable
- Generate child sexual abuse material | Unacceptable
- Score people socially (evaluate or classify individuals or groups by social behaviour or personal traits, leading to unfavourable treatment) | Unacceptable
- Assess the risk of an individual committing a crime solely from profiling or personality traits | Unacceptable
- Compile facial recognition databases by untargeted scraping of internet images or CCTV footage | Unacceptable
- Identify people with real-time remote biometric identification in public spaces for law enforcement | Unacceptable

## High risk (Art. 6)

### Annex I: safety components / products under EU product laws (with third-party conformity assessment)

- Detect tumours in medical images | High
- Act as a safety component of a product covered by Annex I EU laws that requires third-party conformity assessment | High

### Annex III use cases

- Identify people remotely by biometrics (excluding verification that someone is who they claim to be) | High
- Infer sensitive or protected attributes via biometric categorisation (non-banned uses) | High
- Recognize emotions (non-banned uses, e.g. outside workplaces and education) | High
- Manage critical infrastructure as a safety component (critical digital infrastructure, road traffic, supply of water, gas, heating, electricity) | High
- Determine access, admission or assignment to educational and vocational training institutions | High
- Evaluate learning outcomes, including steering a student's learning process | High
- Assess the appropriate level of education an individual will receive | High
- Monitor and detect prohibited student behaviour during tests | High
- Rank job candidates for recruiters | High
- Target job ads, analyse and filter applications, evaluate candidates | High
- Decide on terms of work relationships, promotion or termination of contracts | High
- Allocate tasks based on personality traits, characteristics or behaviour | High
- Monitor and evaluate worker performance | High
- Evaluate eligibility for public benefits and services, including healthcare (granting, reducing, revoking, reclaiming) | High
- Evaluate creditworthiness (except detecting financial fraud) | High
- Classify emergency calls and prioritize dispatch of police, firefighters and medical aid | High
- Prioritize urgent patients in a hospital | High
- Assess risk and set prices for health and life insurance | High
- Assess an individual's risk of becoming a crime victim | High
- Use as a polygraph (law enforcement) | High
- Evaluate reliability of evidence in criminal investigations or prosecutions | High
- Assess an individual's risk of offending or re-offending (not solely based on profiling or personality traits) | High
- Profile individuals during detection, investigation or prosecution of criminal offences | High
- Use as a polygraph (migration, asylum, border control) | High
- Assess risks (security, irregular migration, health) of people entering a country | High
- Assist in examining asylum, visa and residence permit applications and related complaints | High
- Detect, recognise or identify individuals in border control (except verifying travel documents) | High
- Research and interpret facts and law, apply law to concrete facts, or support alternative dispute resolution | High
- Influence the outcome of elections and referenda or voting behaviour (excluding campaign logistics tools people are not directly exposed to) | High

## Limited risk (transparency obligations, Art. 50)

- Answer customer questions | Limited
- Chat with users via a chatbot (users must be told they are interacting with AI) | Limited
- Generate deepfakes (users must be told content is AI-generated or manipulated) | Limited

## Minimal risk (unregulated)

- Summarize documents | Minimal

## Notes from the summary

### Annex III exceptions and profiling rule (Art. 6)
# - An Annex III system is not high-risk if it only performs a narrow procedural task, improves the result of a previously completed human activity, detects decision-making patterns or deviations without replacing or influencing the human assessment (without proper human review), or performs a preparatory task for an assessment.
# - Exception to the exception: an Annex III system that profiles individuals (automated processing of personal data to assess work performance, economic situation, health, preferences, interests, reliability, behaviour, location or movement) is always high-risk.
# - A provider who believes its Annex III system is not high-risk must document that assessment before placing it on the market.

### Exceptions to prohibitions
# - Biometric categorisation: labelling or filtering of lawfully acquired biometric datasets, or law enforcement categorisation of biometric data, is excepted.
# - Crime-risk assessment: allowed to augment human assessments based on objective, verifiable facts directly linked to criminal activity.
# - Emotion inference at work or in education: allowed for medical or safety reasons.
# - Real-time remote biometric identification for law enforcement: allowed only for (a) searching for missing persons, abduction victims, and trafficked or sexually exploited people; (b) preventing a substantial and imminent threat to life or physical safety, or a foreseeable terrorist attack; (c) identifying suspects of serious crimes (e.g. murder, rape, armed robbery, drug and weapons trafficking, organised crime, environmental crime). Requires a fundamental rights impact assessment, EU database registration, and prior judicial or independent administrative authorisation (urgent cases: registration later without undue delay; authorisation requested within 24 hours; if rejected, stop and delete all data and outputs).

### Provider obligations for high-risk systems (Arts. 8-21)
# Risk management system; data governance; technical documentation; record-keeping (logging); instructions for use; human oversight; accuracy, robustness and cybersecurity; quality management system; conformity assessment, EU declaration of conformity and CE marking; registration in the EU database; accessibility requirements. Deployers of high-risk systems have fewer obligations.

### General-purpose AI (GPAI), not a risk level of its own
# - All GPAI model providers: technical documentation, information for downstream providers, Copyright Directive compliance policy, public summary of training content.
# - Free and open-source GPAI models: only copyright policy and training-content summary, unless they pose systemic risk.
# - Systemic risk: cumulative training compute above 10^25 FLOPs (provider must notify the Commission within 2 weeks; the Commission can also designate a model). Additional duties: model evaluations including adversarial testing, systemic risk assessment and mitigation, serious incident reporting, cybersecurity protection.
# - GPAI systems may be used as, or integrated into, high-risk systems; providers must cooperate with high-risk providers.
# - Compliance can be shown via the voluntary General-Purpose Code of Practice (Transparency, Copyright, Safety and Security chapters).

### Key dates
# - Most prohibitions: since 2 Feb 2025; prohibitions on non-consensual intimate imagery and CSAM generation: 2 Dec 2026.
# - GPAI obligations: 2 Aug 2025; AI Office enforcement powers: from 2 Aug 2026.
# - Art. 50 transparency obligations: 2 Aug 2026 (grace period to 2 Dec 2026 for Art. 50(2) for systems already on the market).
# - High-risk under Annex III: 2 Dec 2027. High-risk under Annex I: 2 Aug 2028.
