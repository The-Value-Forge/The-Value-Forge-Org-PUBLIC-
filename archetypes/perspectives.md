---
title: "{{ replace .Name `-` ` ` | title }}"
date: {{ .Date }}
piece_kind: "Original article"  # or "Guest contribution", "Invited response", etc.
author: ""                  # named byline
author_role: ""            # role or affiliation (optional)
description: ""            # one-sentence standfirst
read_time: ""
linked_month: ""           # e.g. "2026-08" to feature on that Monthly edition (optional)
sources: []
---

Write the article in full prose. Use a pull-quote once, for the line the piece turns on:

{{</* pullquote cite="Author Name" */>}}
The single sentence worth pulling out at display size.
{{</* /pullquote */>}}

Any clinical or factual claim needs a verified entry in `sources:` above.
