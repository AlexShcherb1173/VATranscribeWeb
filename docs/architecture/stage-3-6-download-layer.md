# Stage 3.6 Download Page + Distribution Layer

Stage 3.6 upgrades the public download pages.

## Routes

- `/download`
- `/ru/download`

## Implemented

- Web app access CTA
- Desktop app roadmap cards
- Windows/macOS/Linux placeholders
- CLI/internal tools placeholder
- System requirements section
- Release notes preview
- Checksum/signature placeholders
- Download FAQ
- EN/RU content
- SEO copy update for download intent

## Current release state

The web dashboard is the current supported access path.

Desktop installers are not published yet.

## Future backend/distribution work

A later stage can add:

- release version model
- public release API
- file storage for installers
- checksum storage
- signature metadata
- release channels: stable/beta/nightly
- automatic update feed for desktop app

## Desktop project note

`apps/desktop` already exists as a project foundation, but Stage 3.6 does not publish real desktop builds.
