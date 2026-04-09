# PhotoChemoPapers

PhotoChemoPapers is an automated literature-monitoring bot focused on **organometallic and coordination chemistry applied to anticancer therapies**, especially **photoactivated approaches** such as **PDT** and **PACT**.

The project collects papers from RSS feeds, filters them using configurable domain-specific rules, assigns relevance scores, and distributes selected results through social and messaging platforms.

## Current scope

PhotoChemoPapers is primarily focused on:

- Photodynamic therapy (PDT)
- Photoactivated chemotherapy (PACT)
- Metal-based anticancer agents
- Photoactive coordination compounds
- Related photochemical and bioinorganic approaches

The filtering is intentionally broad enough to avoid missing relevant literature, so some off-topic papers may occasionally appear.

## Features

- RSS-based monitoring of journals and other scientific sources
- Configurable keyword filtering
- Rule-based scoring system to prioritize relevance
- Automatic tagging
- Telegram integration
- Bluesky integration
- GitHub Actions automation
- Extensible publisher/output architecture

## How it works

1. The bot reads RSS feeds from configured sources.
2. Papers are filtered using chemistry- and therapy-related keywords.
3. A rule-based scoring layer prioritizes papers according to positive and negative signals.
4. Selected papers are formatted and sent to the enabled outputs.

## Scoring philosophy

The bot does not rely on generative AI. Instead, it uses transparent, editable rules.

Positive signals may include:

- PDT / PACT / photodynamic / photoactivated
- metal names such as ruthenium, iridium, osmium, platinum, rhenium
- terms like cytotoxicity, phototoxicity, ROS, singlet oxygen
- biomedical context such as in vitro, in vivo, apoptosis, cell lines

Negative signals may include:

- photocatalysis
- environmental remediation
- hydrogen evolution
- water splitting
- CO2 reduction
- surface-heavy materials-science contexts when not clearly therapeutic

This makes the system suitable for semi-curated literature surveillance without requiring paid AI services.

## Outputs

Currently supported or prepared outputs include:

- Telegram
- Bluesky
- Email/newsletter (planned or partial)
- Other channels can be added through the output/publisher architecture

## Automation

The bot is designed to run automatically through GitHub Actions, so it does not depend on a local computer being switched on.

## Limitations

- RSS metadata quality varies across publishers
- Some papers outside the intended scope may still pass the filter
- Some relevant papers may be missed if the feed metadata is poor
- “Curated” in the strongest sense still requires human review for a final newsletter

## Project status

This project is under active refinement. Current priorities include:

- improving relevance scoring
- reducing false positives from photocatalysis and surface/materials papers
- improving formatting and chemical notation
- developing a semi-curated newsletter workflow

## Credits

This project is **based on PapersBot**, originally developed by **François-Xavier Coudert**.

It is also **inspired by the idea behind “Photocatalysis Papers” from the ESC Group**.

## License

This project builds upon software released under the **MIT License**.  
Please keep the original license and attribution when reusing or adapting the code.