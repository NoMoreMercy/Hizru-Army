# Hizru-Army
Hackathon
# Voyager-X Signal Recovery Pipeline
### Team: HIzru Army | IIT ISM Dhanbad | PhysisTechne 2026

## Overview
Recovery of telemetry data from a simulated deep-space probe (Voyager-X) 
performing a gravity-assist maneuver around Jupiter. The signal was 
recovered from 15GB of raw IQ data captured by the Deep Space Network.

## Results Summary
| Stage | Status | Key Finding |
|-------|--------|-------------|
| Stage 0: Data Reconstruction | ✅ Complete | Parsed 300 files, 15GB streaming |
| Stage I: Signal Detection | ✅ Complete | Carrier at 429.502 kHz |
| Stage II: Carrier Recovery | ✅ Complete | 12.41 kHz Doppler drift tracked |
| Stage III: Demodulation | ✅ Complete | BPSK modulation confirmed |
| Stage IV: Payload Recovery | ✅ Partial | Valid CCSDS packet extracted |

## Signal Parameters
- **Carrier Frequency:** 429.502 kHz (drifting 423-435 kHz)
- **Modulation:** BPSK (confirmed via 2nd power spectral analysis)
- **Symbol Rate:** ~2900 baud
- **SNR:** 12.1 dB (measured at ±5 kHz bandwidth)
- **Active Files:** 67 of 300 (files 2-69)
- **Signal Duration:** ~67 seconds

## Recovered Telemetry
```
CCSDS Packet Header:
  Version:        0 (valid)
  Type:           Telemetry  
  APID:           0x189 (393)
  Sequence count: 2796
  Timestamp:      2004-04-06 12:09:06 UTC

Telemetry Data:
  Temperature 1:  43.20°C
  Temperature 2:   4.32°C
  Packet counter: 2050
  Identifiers:    PKD, BY@I$a (probe callsign), Yf
```

## Pipeline Architecture
```
Raw IQ Files (15GB)
        │
        ▼
┌─────────────────────┐
│  Stage 0            │
│  IQ Parser          │ ← Streaming, memory-safe
│  (hex → complex)    │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Stage I            │
│  Signal Detection   │ ← FFT spectrogram
│  Carrier: 429.5kHz  │   Files 2-69 active
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Stage II           │
│  Carrier Recovery   │ ← Per-file FFT peak
│  Doppler: 12.41kHz  │   Costas loop PLL
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Stage III          │
│  Demodulation       │ ← 2nd power test
│  BPSK confirmed     │   Phase correction
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Stage IV           │
│  CCSDS Framing      │ ← Sync: 0x1ACFFC1D
│  Payload: 5801 bytes│   Valid header ✅
└─────────────────────┘
```

## Key Technical Achievements

### 1. Memory-Efficient Parsing
Processed 15GB of data by streaming one file at a time,
never exceeding 500MB RAM usage.

### 2. Doppler Drift Tracking  
Measured carrier drift of 12.41 kHz across 67 files,
consistent with Jupiter gravity-assist acceleration.

### 3. BPSK Confirmation
Used 2nd power spectral analysis to definitively confirm
BPSK modulation - peak at 2×carrier frequency.

### 4. CCSDS Packet Recovery
Located sync marker 0x1ACFFC1D and extracted valid
CCSDS primary header with version=0.

## Installation
```bash
pip install numpy scipy matplotlib pillow
```

## Usage
```bash
# Run complete pipeline
python solution.py --data-folder /path/to/dsn_data/

# Run individual stages
python solution.py --stage 1  # Signal detection only
python solution.py --stage 4  # Full pipeline
```

## File Structure
```
├── solution.py          # Main pipeline
├── stage0_parse.py      # IQ file parser
├── stage1_detect.py     # Signal detection
├── stage2_carrier.py    # Carrier recovery
├── stage3_demod.py      # BPSK demodulation
├── stage4_payload.py    # CCSDS extraction
├── plots/
│   ├── spectrogram.png  # Carrier drift waterfall
│   ├── constellation.png # Before/after correction
│   ├── carrier_drift.png # Doppler over time
│   └── signal_power.png  # Active file detection
├── output/
│   └── payload.bin      # Recovered telemetry
└── MISSION_REPORT.pdf   # Detailed analysis
```

## Plots

### Spectrogram (Carrier Drift)
![Spectrogram](plots/spectrogram.png)

### Constellation Diagram
![Constellation](plots/constellation.png)

### Signal Power Detection
![Signal Power](plots/signal_power.png)

## Mission Report
The Voyager-X probe transmitted a 5-minute burst of telemetry
while performing a gravity-assist around Jupiter. Key findings:

- Signal active for 67 seconds (files 2-69 of 300)
- Carrier drifted 12.41 kHz due to Doppler + degraded oscillator
- BPSK modulation with ~2900 baud symbol rate
- Valid CCSDS telemetry packet recovered
- Probe temperature: 43.20°C (nominal operating range)
- Probe callsign identified: BY@I$a

## Team
**HIzru Army** | IIT ISM Dhanbad
PhysisTechne Symposium 2026
