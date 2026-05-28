#!/bin/sh
# The j313 convolver filter only honors the stored volume once a stream is
# actively flowing. Without this, the first sound plays at max until swayosd
# is touched. Workaround: play silence to engage the chain, nudge volume to
# apply the restored value, then stop.
LOG=/tmp/audio_wake.log
echo "=== $(date) === audio_wake start" >>"$LOG"

# Wait for default sink
for i in $(seq 1 50); do
    pactl get-sink-volume @DEFAULT_SINK@ >/dev/null 2>&1 && break
    sleep 0.2
done
sleep 1

# 2s of stereo s16le 48k silence = 384000 bytes
head -c 384000 /dev/zero | \
    paplay --raw --format=s16le --rate=48000 --channels=2 &
PID=$!

sleep 0.5
echo "before: $(pactl get-sink-volume @DEFAULT_SINK@ 2>&1)" >>"$LOG"
pactl set-sink-volume @DEFAULT_SINK@ +1% >>"$LOG" 2>&1
pactl set-sink-volume @DEFAULT_SINK@ -1% >>"$LOG" 2>&1
echo "after:  $(pactl get-sink-volume @DEFAULT_SINK@ 2>&1)" >>"$LOG"

wait $PID
echo "=== $(date) === audio_wake end" >>"$LOG"
