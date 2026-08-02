---
title: "{{ replace .Name `-` ` ` | title }}"
date: {{ .Date }}
edition_label: ""            # e.g. "Second Edition" (optional display label)
linked_month: ""            # e.g. "2026-08" to attach as the preface on that Monthly edition; leave blank for a standalone note
signature: "— The Editor"
description: ""             # one-sentence standfirst
preface: |
  # Short signed note shown on the linked Monthly edition (2–3 sentences).
  # The full piece is the body below. Delete if this editorial is standalone.
sources: []
---

Write the editorial in the first person, in your own voice.
