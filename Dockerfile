FROM ghcr.io/linuxserver/baseimage-selkies:arch

ARG BUILD_DATE
ARG VERSION
ARG CACHE_BUST
ARG STG_VERSION=2.5.3
ARG STG_SHA256=b9ee44863fdd2ce20934956ad0f77a11b03586454fcf99beddc855bc45da1fa5

LABEL build_version="Custom Arch Streamlink Twitch GUI image - Build-date:- ${BUILD_DATE}"
LABEL maintainer="Serph91P"
LABEL org.opencontainers.image.title="docker-webtop-streamlink"
LABEL org.opencontainers.image.description="Streamlink Twitch GUI with streamlink + mpv in LinuxServer Selkies"
LABEL org.opencontainers.image.source="https://github.com/Serph91P/docker-webtop-streamlink"

ENV TITLE="Streamlink Twitch GUI" \
    PIXELFLUX_WAYLAND=true \
    SELKIES_DESKTOP=false \
    AUTO_GPU=true \
    NO_GAMEPAD=true \
    NO_DECOR=true

RUN set -eux; \
    echo "**** cache bust ${CACHE_BUST} ****"; \
    echo "**** install runtime packages ****"; \
    pacman -Sy --noconfirm --needed \
        alsa-lib \
        ca-certificates \
        curl \
        dbus \
        ffmpeg \
        glib2 \
        gtk3 \
        libevdev \
        libnotify \
        mpv \
        nss \
        streamlink \
        ttf-font \
        xdg-user-dirs \
        xdg-utils; \
    echo "**** install Streamlink Twitch GUI ****"; \
    curl -fsSL -o /tmp/streamlink-twitch-gui.tar.gz \
        "https://github.com/streamlink/streamlink-twitch-gui/releases/download/v${STG_VERSION}/streamlink-twitch-gui-v${STG_VERSION}-linux64.tar.gz"; \
    echo "${STG_SHA256}  /tmp/streamlink-twitch-gui.tar.gz" | sha256sum -c -; \
    mkdir -p /opt/streamlink-twitch-gui; \
    tar -xzf /tmp/streamlink-twitch-gui.tar.gz -C /opt/streamlink-twitch-gui --strip-components=1; \
    chmod +x /opt/streamlink-twitch-gui/streamlink-twitch-gui; \
    echo "**** link streamlink binary ****"; \
    ln -sf /usr/bin/streamlink /opt/streamlink-twitch-gui/streamlink; \
    echo "**** verify nginx config stays compatible with baseimage modules ****"; \
    nginx -t; \
    echo "**** add icon ****"; \
    if [ -f /opt/streamlink-twitch-gui/assets/icons/icon-256.png ]; then \
        cp /opt/streamlink-twitch-gui/assets/icons/icon-256.png /usr/share/selkies/www/icon.png; \
    elif [ -f /opt/streamlink-twitch-gui/assets/icons/icon-128.png ]; then \
        cp /opt/streamlink-twitch-gui/assets/icons/icon-128.png /usr/share/selkies/www/icon.png; \
    fi; \
    echo "**** set bash as default shell ****"; \
    sed -i 's|/bin/sh$|/bin/bash|g' /etc/passwd; \
    echo "**** create user directories ****"; \
    mkdir -p /config/Documents; \
    echo "**** cleanup ****"; \
    rm -rf \
        /config/.cache \
        /tmp/* \
        /var/cache/pacman/pkg/* \
        /var/lib/pacman/sync/*

COPY root/ /

RUN chmod +x /defaults/autostart /defaults/autostart_wayland /defaults/startwm_wayland.sh /usr/local/bin/run-streamlink-twitch-gui && \
    echo "**** verify final image contents ****" && \
    ls -la /opt/streamlink-twitch-gui/streamlink-twitch-gui && \
    streamlink --version && \
    mpv --version 2>/dev/null | head -1 && \
    HOME=/config XDG_CONFIG_HOME=/config/.config xdg-user-dir DOCUMENTS && \
    touch /tmp/streamlink-twitch-gui-ready

EXPOSE 3000

VOLUME /config