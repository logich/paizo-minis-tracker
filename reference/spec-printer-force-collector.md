# Spec: print force and film-life collector for the Elegoo Mars 5 Ultra

Written 2026-11-03 by the ledger session, for a Claude agent that knows Logan's
Home Assistant (HA) setup. The ledger session cannot see the HA config; you can.
Where this spec says "unverified", check it rather than trust it.

## Why

On 2026-11-03 a print paused because the printer's **release film life counter
reached 60000** (Logan: "it is a film life counter"). Logan forced it to carry
on with "mandatory printing". He wants to see the film coming, and to know whether
peel force trends upward as the film ages. Neither is recorded anywhere today.

Two things to capture:

1. **Peel force per layer**, from the printer's load cell, as a long-term series.
2. **The film life counter**, if it can be read at all, so a replacement can be
   planned before the pause rather than found by it.

## The printer

- Elegoo Mars 5 Ultra, tilting vat, protocol SDCP V3.0.0, firmware V1.5.0.
- LAN address `192.168.1.151`. **LAN-only**; nothing here goes off the network.
- MainboardID `0384c72b7e610100`, machine name from UDP 3000 `M99999`.
- Log, plain HTTP, honours `Range:` requests:
  `http://192.168.1.151:3030/media/mmcblk0p2/log`
- File listing: `http://192.168.1.151:3030/media/mmcblk0p3/`
- Control channel: `ws://192.168.1.151:3030/websocket` (SDCP; bare HTTP gets 426).

## What the log holds, and the problem

The log is a **rolling window of about 2.3 MB, which is only ~23 minutes** while a
plate runs at ~7.4 s per layer. Anything older is gone. So a collector must poll
more often than every ~20 minutes, or layers are lost. **Poll every 5 minutes** as
a working value, and fetch only the tail with a `Range:` request (the last
~600 KB is plenty at that cadence).

### The force line (one per layer)

    [cs1237][Info][239][386536254]:layer 550, avg -205, peak -4911, diff 4706

- `cs1237` is the load-cell ADC on the build plate.
- Fields after the tick: `layer N`, `avg`, `peak`, `diff`.
- The first bracketed number group `[386536254]` is a **tick in milliseconds since
  the printer booted**, not wall-clock time. Consecutive layers are ~7425 ms apart
  on the current recipe.
- `diff` is the swing between baseline and peak, so effectively **peel force**.
  `peak` is negative (the pull). `avg` is the sensor baseline and **drifts**; it is
  not a force. **Units are not stated anywhere. Treat values as raw counts.**
- Each layer's recording is bracketed by `cs1237_recoder_start 0/1` and
  `cs1237_recoder_stop 1` lines. Parse only the `layer N, avg, peak, diff` lines.

Observed on the current print, layers 365-550 (186 samples, 2026-11-03):

    layers 365-389   mean diff 6221   max 6963   baseline +470
    layers 440-464   mean diff 4699   max 5291   baseline +266
    layers 540-550   mean diff 4779   max 4899   baseline -221

`diff` falls ~25% across the window, most likely because the models' cross-section
shrinks as the print rises. **That is a confound: a within-print slope says
nothing about film wear.** Only a comparison across prints of similar geometry can.

### Turning a tick into wall-clock time

Log lines carry no date. The SDCP websocket echo lines do:

    [sdcp_v3][Debug][781][386534248]:ws : {... "TimeStamp": 1793735082 ...}

Pair a `[tick]` with its `TimeStamp` (unix seconds) from nearby lines to get an
offset, then convert each layer's tick. Recompute the offset on every poll: the
printer reboots and the tick restarts from zero.

### Other lines worth knowing

- `[printer][Info]...:layer 550:` then `execute: lift_position ... exposure_time ...`
  gives the exposure actually running (exposure here is in the file as 2000 ms etc.).
  The existing `tools/ledger.py runlog` already parses these `execute:` lines.
- There is **no filename in the log**, no plate id, and **no film counter**. Searches
  for film, life, count, usage, total and 60000 found nothing relevant.
- The log has **no warning or error lines**: only Info and Debug. The pause on the
  film counter does not appear in it (it had already rolled out of the window).

## Requirements

### R1. Collect the force series

- Poll the log tail every 5 minutes while a print runs (and cheaply when idle: a
  failed or empty poll is normal).
- Extract every `layer N, avg, peak, diff` line.
- **Deduplicate** on (printer boot epoch, layer, tick), because successive polls
  overlap.
- Store per layer: wall-clock time, layer number, avg, peak, diff, and the print
  it belongs to (R3).
- Do not store the raw log.

### R2. Keep it long enough to see a trend

The point is comparison across plates and weeks. Whatever sink you choose must keep
**per-layer rows for months** and let Logan chart `diff` against layer for one print
and overlay several prints. HA's default recorder is poor at per-layer streams
(one value per entity per update), so consider InfluxDB, a CSV or SQLite file on
the HA host, or the long-term statistics tables with a summary entity. Your call; you
know what is installed. Say what you chose and why.

### R3. Tag each series with its print

The log gives no filename. Options, in order of preference (all unverified):

1. SDCP status over the websocket (Cmd 0 / Cmd 320 report) may name the file and
   current layer. Probe it read-only and record what you find.
2. Fall back to the **printer file listing**
   (`http://192.168.1.151:3030/media/mmcblk0p3/`), taking the newest file by
   modification time as the likely current job.
3. Otherwise leave the print untagged and let Logan label a run by hand.

Slicer filenames end in a timestamp such as `..._202611031303.goo`; the ledger
repository keys its plates by that file, so passing the filename through lets the
two be joined later.

### R4. Summaries

Per print, derive and keep:

- mean, median and max `diff`,
- `diff` mean in blocks of 25 layers, which is what we used by hand,
- layer count seen, and whether the series has gaps.

Flag a gap: a stretch of layers with no samples means a poll was missed.

### R5. The film life counter

Find out whether the printer exposes it. It is **not in the log**. Try, read-only:

- SDCP `Cmd 1` (attributes) and `Cmd 0` (status) over the websocket,
- the printer's web endpoints on port 3030.

If it can be read, expose it as an HA sensor with an alert at, say, 90% of 60000.
If it cannot, **say so plainly** and fall back to an estimate:

- `estimated layers since film change = sum of layers of every print since the film
  was fitted`, using layer counts from the sliced files' headers (the ledger
  repository can supply these).
- Needs one input from Logan: the **date and counter reading when the film was
  last replaced**.
- Cancelled and failed prints still count on the printer, so the estimate will run
  low; one real reading off the screen calibrates it.

### R6. Alerts (optional, only after R1-R5 work)

- Film counter at 90% (R5).
- Rising `diff` across comparable prints. Do not alert on a within-print slope; see
  the confound above.

## Hard constraints

- **Read-only toward the printer.** Never send `Cmd 128` (start print) or any other
  control command. Never upload files. Status reads only.
- Poll gently. The printer's web server is small; the log is ~2.3 MB, so request a
  tail range, not the whole file, and not more than once a minute.
- **Do not touch git or the `paizo-minis` repository.** It has other writers. If
  you produce something the ledger should hold (a force summary, a film estimate),
  write it to a path HA owns and tell Logan; the ledger session will pull it in.
- No credentials are needed for the printer. Do not add any.

## Acceptance

1. After one full print, the sink holds one row per layer with no duplicates and no
   gaps, and the count matches the print's layer total.
2. Logan can plot `diff` against layer for that print.
3. A second print is stored without corrupting the first, and can be overlaid.
4. A printer reboot (tick restart) does not collide with earlier rows.
5. The film counter is either readable as a sensor, or the spec's R5 fallback is
   running and clearly labelled as an estimate.
6. Nothing sent to the printer other than HTTP GETs and read-only SDCP status.

## Not known, to be found out

- Units of the `cs1237` readings.
- Whether `diff` or `peak` is the quantity Elegoo compares against its force
  thresholds, if it has any.
- Whether the printer exposes the film counter anywhere.
- How SDCP status names the current file.
- What HA tooling is available on Logan's host (you have the answer; the ledger
  session does not).

## Where the numbers came from

The parsing above was done on 2026-11-03
against the live log with `grep` and a small Python script; the parser can be
lifted into `tools/` and shared with `runlog` if useful.
