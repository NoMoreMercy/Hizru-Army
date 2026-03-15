# Voyager-X Signal Recovery Pipeline
### Team: HIzru Army | IIT ISM Dhanbad | PhysisTechne 2026

## Problem Statement
Recover telemetry from a simulated deep-space probe (Voyager-X) 
performing a gravity-assist maneuver around Jupiter. 
Raw data: 300 IQ files, 15GB total, 2.0 MSps sample rate.

## Final Results
| Stage | Status | Finding |
|-------|--------|---------|
| Stage 0: Data Reconstruction | ✅ | Parsed 300 files, 15GB streaming |
| Stage I: Signal Detection | ✅ | Carrier 429.502 kHz, files 2-69 active |
| Stage II: Carrier Recovery | ✅ | 12.41 kHz Doppler drift tracked |
| Stage III: Demodulation | ✅ | BPSK confirmed via 2nd power test |
| Stage IV: Payload Recovery | ✅ | Valid CCSDS packet, BMP payload identified |

## Signal Parameters
```
Carrier:      429.502 kHz (drifting 423–435 kHz)
Modulation:   BPSK (confirmed via 2nd power spectral analysis)
Symbol Rate:  ~10,000 baud (SPS = 200)
SNR:          12.1 dB at ±5 kHz bandwidth
Active Files: 67 of 300 (files 2–69)
Doppler:      12.41 kHz total drift (Jupiter gravity assist)
```

## Recovered Telemetry
```
CCSDS Header:
  Version:        0 ✅
  APID:           0x189 (393)
  Sequence count: 2796
  Timestamp:      2004-04-06 12:09:06 UTC

Telemetry Data:
  Temperature 1:  43.20°C
  Temperature 2:   4.32°C
  Packet counter: 2050
  Probe callsign: BY@I$a
  Identifiers:    PKD, Yf

Payload:
  Format:         BMP image
  Whitening:      Data whitening applied
  Size needed:    12,779 bytes (fragmented across files)
```

## Pipeline
```
Raw IQ Files (15GB, 300 files)
        ↓
Stage 0: Streaming IQ Parser
  IEEE 754 big-endian hex → complex samples
        ↓
Stage I: Signal Detection
  FFT peak detection → carrier 429.502 kHz
  Power threshold → active files 2-69
        ↓
Stage II: Carrier & Doppler Recovery  
  Per-file FFT carrier estimation
  12.41 kHz drift tracked across 67 files
        ↓
Stage III: BPSK Demodulation
  2nd power test → confirmed BPSK
  Low-pass filter + symbol sampling
  Two-peak histogram confirms clean BPSK
        ↓
Stage IV: CCSDS Payload Extraction
  Sync marker 0x1ACFFC1D located
  Valid CCSDS header extracted
  BMP image payload identified
```

## Key Technical Achievements

### Memory-Efficient Parsing
Processed 15GB by streaming one file at a time.
Never loaded more than one file into RAM simultaneously.

### Doppler Drift Tracking
Measured and tracked 12.41 kHz carrier drift across 67 files,
consistent with Jupiter gravity-assist acceleration profile.

### BPSK Confirmation
Used 2nd power spectral analysis — peak at 2× carrier (859 kHz)
definitively confirms BPSK modulation.

### Clean Symbol Histogram
Direct sampling at SPS=200 reveals two clear peaks at ±0.7,
confirming clean BPSK with good SNR.

## Plots
### Signal Power Detection
![Signal Power](plots/signal_power.png)

### Spectrogram (Carrier Drift)
![Spectrogram](plots/spectrogram.png)

### Constellation Diagram
![Constellation](plots/constellation.png)

## Installation
```bash
pip install numpy scipy matplotlib pillow
```

## Usage
```bash
python solution.py
```

## File Structure
```
├── solution.py           # Complete pipeline
├── plots/
│   ├── spectrogram.png   # Carrier drift waterfall
│   ├── constellation.png # BPSK constellation
│   └── signal_power.png  # Active file detection
├── output/
│   └── payload.bin       # Recovered telemetry bytes
└── MISSION_REPORT.txt    # Detailed analysis
```

## Team
**HIzru Army** | IIT ISM Dhanbad
PhysisTechne Symposium 2026
