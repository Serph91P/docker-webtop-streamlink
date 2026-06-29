# docker-webtop-streamlink

Streamlink Twitch GUI with streamlink and mpv running in a LinuxServer Selkies container for Sealskin.

## Image

```bash
docker pull ghcr.io/serph91p/docker-webtop-streamlink:latest
```

Stable store entries should use the generated release tag, for example `2.5.3-ls1`, not `latest`.

## Store automation

This repo sends a `repository_dispatch` event to `Serph91P/sealskin-store` after a successful image build when the `STORE_DISPATCH_TOKEN` secret is configured.
