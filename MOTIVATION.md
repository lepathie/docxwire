# Motivation

The **[Heilbronner Rudergesellschaft Schwaben e.V.](https://www.ruderschwaben.de/)**, commonly known simply as **Ruderschwaben**, is a rowing club based in Heilbronn, Germany. Like many volunteer-driven sports organizations, the club depends on contributions from its members to document regattas and other aspects of club life.

These contributions serve two important purposes. First, they are published in the club's internal magazine, the *Clubnachrichten* (formerly known as the *Heftle*). Second, many of them are suitable for publication on the club's website, which is powered by Joomla 5.

To keep the barrier for contributors as low as possible, club members submit their articles through an online form as **Microsoft Word documents** (`.docx`). A shared Word template (`.dotx`) provides a recommended structure and set of styles, allowing authors to focus on writing instead of learning how to use the content management system (CMS). This is also a way our small editorial team ensures that articles follow rules important for publishing in the aforementioned magazine, like using every page's space effectively.

This workflow has proven to be accessible and practical for contributors across all age groups. However, it creates a significant editorial overhead. Content that already exists in a Word document must be manually transferred into Joomla, images have to be uploaded separately, captions recreated, formatting checked, and article metadata added before publication.

The process also requires volunteers to be onboarded to the Joomla CMS and its publishing workflows, despite the actual content already being available in a structured document. Beyond the time investment, manual transfer introduces a range of downstream issues: Word formatting can inadvertently be copied into Joomla articles, image metadata may be lost, and large, unoptimized images often accumulate within the root of the media library.

Over time, these small inconsistencies increase maintenance effort, make content management less predictable, and place an unnecessary burden on a limited number of technically experienced club members.

A typical article follows a structure similar to:

```text
[Image]
[Caption]

[Heading]

[Body]

[Optional Image]
[Optional Caption]

[Body]

[Author]
```

In reality, however, submissions are rarely perfect. Contributors may use an outdated template, apply incorrect styles, omit images, or otherwise deviate from the expected format. Since the process is intended for non-technical users, strict validation would create friction and discourage contribution.

**DOCxWIRE** was created to bridge this gap and automate what was previously a manual effort.

It aims to interpret real-world club submissions and transform them into structured Joomla content automatically. The system analyzes document styles, extracts images and captions, identifies article sections, determines authorship information, and handles common deviations from the standard template as gracefully as possible.

The goal is not to replace the existing authoring process, but to preserve its simplicity while eliminating the repetitive work involved in publishing the content online. By automating the transformation from `.docx` documents to Joomla articles, DOCxWIRE allows the club's volunteers to spend less time copying content between systems and more time reviewing, improving, and publishing it.

In short, DOCxWIRE acts as a pragmatic integration layer between a familiar Word-based editorial workflow and a modern content management system. Rather than forcing contributors to adapt to the CMS, it adapts the CMS publishing process to the realities of a volunteer-run organization and the imperfect, real-world documents its members produce.
