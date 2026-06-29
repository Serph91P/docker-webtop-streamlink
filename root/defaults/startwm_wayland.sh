#!/usr/bin/env bash

# LinuxServer Selkies Wayland desktop launcher.
# Keep this close to upstream baseimage-selkies. svc-selkies provides the stream,
# svc-de calls this after the Wayland socket exists.

ulimit -c 0
export XCURSOR_THEME=whiteglass
export XCURSOR_SIZE=24
export XKB_DEFAULT_LAYOUT=us
export XKB_DEFAULT_RULES=evdev
export WAYLAND_DISPLAY=wayland-1

# Force the autostart even when /config already contains an old labwc config.
# LinuxServer only copies /defaults/autostart_wayland on first boot, but Sealskin
# can keep /config across uninstall/reinstall.
mkdir -p "$HOME/.config/labwc"
cp /defaults/autostart_wayland "$HOME/.config/labwc/autostart"
chown abc:abc "$HOME/.config/labwc/autostart" 2>/dev/null || true
chmod 755 "$HOME/.config/labwc/autostart"

if [ "${SELKIES_DESKTOP}" == "true" ]; then
    labwc > /tmp/labwc.log 2>&1 &
    sleep 1
    export WAYLAND_DISPLAY=wayland-0
    export DISPLAY=:0
    selkies-desktop
else
    exec labwc > /tmp/labwc.log 2>&1
fi
