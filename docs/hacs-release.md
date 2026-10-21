# Publish HomeBuddy Access through HACS

The repository is packaged as a **custom integration**, not a Supervisor app.
No generated ZIP is required: HACS downloads `custom_components/homebuddy_access/`
from a release or the default branch. All runtime assets are bundled there.
The repository name is **homebudddy-access** (three d's); the HA domain is
**homebuddy_access**. Keep existing URLs unchanged.

## Maintainer steps before the first public installation

1. Review the working tree in GitHub Desktop, then commit and push when ready.
   Never include `.backups`, `.venv`, credentials or real QR screenshots.
2. Ensure the GitHub repository is public and Issues are enabled.
3. Set its About description to:
   `Connect HomeBuddy to Home Assistant with local/remote QR setup and optional entity filters.`
   Suggested topics: `home-assistant`, `hacs`, `custom-integration`, `homebuddy`, `qr-code`.
   These are GitHub settings and cannot be set by committing files.
4. Enable GitHub Actions and require green **Checks** and **HACS and Hassfest** runs.
   HACS checks GitHub metadata as well as files, so it cannot validate unpublished
   working-tree changes. No checks are ignored in the supplied workflow.
5. Test on HA 2026.10.2 or newer: add this URL as a HACS custom repository of type
   Integration, download, restart HA, add the integration as the owner, generate and
   scan a test QR, then revoke its token. Test both new installation and manual-install
   migration. Confirm compatible iOS/Android app builds before claiming filter support.
6. Publish a GitHub **Release**, not only a tag. Use tag `v1.0.5` for manifest version
   `1.0.5` and copy the release notes from CHANGELOG.md.
   Select the tested commit.
7. Share the README's HACS repository link. Users can install as a custom repository
   without waiting for inclusion in HACS's default catalog.

Future versions must update manifest.json and pyproject.toml, refresh uv.lock and add
release notes. Bump asset query versions when frontend files change. Publish a new
release/tag for each update; don't replace files under an already published release.
No workflow here creates releases, commits, tags or deploys automatically.

## Optional: appear in default HACS search results

Custom-repository installation and default-catalog inclusion are separate.
After successful HACS/Hassfest CI, a full GitHub release and real installation tests,
the owner can submit a PR to `hacs/default`, adding
`FilipposPirpilidis/homebudddy-access` alphabetically to its `integration` list.
All required checks must pass without ignores. Approval is up to HACS maintainers;
custom-repository support does not imply default-catalog acceptance.

## Validation references

- [HACS integration requirements](https://www.hacs.xyz/docs/publish/integration/)
- [Repository metadata and releases](https://www.hacs.xyz/docs/publish/start/)
- [HACS validation action](https://www.hacs.xyz/docs/publish/action/)
- [Default catalog submission](https://www.hacs.xyz/docs/publish/include/)
