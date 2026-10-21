# HomeBuddy Access branding

The HomeBuddy blue glasses artwork is preserved at `www/logo.png`.
Bundled `brand/` PNGs use the same artwork at HA's standard 256px and 512px (@2x)
sizes, including logo and dark-logo fallback names. The panel keeps its full-size
source. `node scripts/render-brand.cjs` regenerates the bundled sizes on macOS using
`sips`; no build tooling is required on users' Home Assistant installations.

Brand images live inside the integration so HACS downloads them with the code.
See [HA custom integration branding](https://contributors.home-assistant.io/core/integrations/brands/)
and [HACS integration requirements](https://www.hacs.xyz/docs/publish/integration/).
