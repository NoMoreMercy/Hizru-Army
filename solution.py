#!/usr/bin/env python3
"""
Voyager-X Signal Recovery Pipeline
Team: HIzru Army | IIT ISM Dhanbad
PhysisTechne Symposium 2026
"""

import os
import struct
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, spectrogram
from numpy.fft import fft, fftfreq, fftshift
from PIL import Image

# ============================================================
# CONFIGURATION
# ============================================================
SAMPLE_RATE  = 2e6          # 2.0 MSps
DATA_FOLDER  = r"C:\Users\Lenovo\Downloads\extracted\data"
SYNC_MARKER  = "00011010110011111111110000011101"
SYNC_BYTES   = bytes([0x1A, 0xCF, 0xFC, 0x1D])

# ============================================================
# STAGE 0: DATA RECONSTRUCTION
# ============================================================
def read_iq_file(filepath):
    """
    Parse IQ file - IEEE 754 big-endian hex pairs
    Memory efficient - streams one file at a time
    """
    samples = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.replace("0x","").replace(",","").split()
            if len(parts) < 2:
                continue
            try:
                i_val = struct.unpack(">f", bytes.fromhex(parts[0]))[0]
                q_val = struct.unpack(">f", bytes.fromhex(parts[1]))[0]
                samples.append(complex(i_val, q_val))
            except ValueError:
                continue
    return np.array(samples, dtype=np.complex64)

# ============================================================
# STAGE I: SIGNAL DETECTION
# ============================================================
def find_active_files(data_folder):
    """
    Scan all files and find active signal using power detection
    Signal active in files 2-69 (67 of 300 files)
    """
    files = sorted(os.listdir(data_folder))
    peak_powers = []

    print("Scanning files for signal...")
    for i, fname in enumerate(files):
        fpath = os.path.join(data_folder, fname)
        s = read_iq_file(fpath)
        # Read only 10000 samples for speed
        samples = []
        with open(fpath, "r") as f:
            for j, line in enumerate(f):
                if j >= 10000:
                    break
                line = line.strip()
                if not line:
                    continue
                parts = line.replace("0x","").replace(",","").split()
                if len(parts) < 2:
                    continue
                try:
                    i_val = struct.unpack(">f", bytes.fromhex(parts[0]))[0]
                    q_val = struct.unpack(">f", bytes.fromhex(parts[1]))[0]
                    samples.append(complex(i_val, q_val))
                except ValueError:
                    continue
        s = np.array(samples, dtype=np.complex64)
        peak_powers.append(np.max(np.abs(fft(s))**2))
        print(f"  File {i+1}/{len(files)}", end="\r")

    # Threshold detection
    noise_floor = np.mean(peak_powers[-100:])
    threshold   = noise_floor * 10
    active_idx  = np.where(np.array(peak_powers) > threshold)[0]
    active_files = [files[i] for i in active_idx]

    print(f"\nActive files: {len(active_files)} of {len(files)}")
    return active_files, peak_powers

def find_carrier(s, sample_rate=SAMPLE_RATE):
    """Find carrier frequency using FFT peak detection"""
    N      = len(s)
    freqs  = fftfreq(N, 1/sample_rate)
    spectrum = np.abs(fft(s))**2
    return freqs[np.argmax(spectrum)]

def plot_spectrogram(s, sample_rate=SAMPLE_RATE):
    """Generate waterfall plot showing carrier drift"""
    f_sg, t_sg, Sxx = spectrogram(
        s, fs=sample_rate,
        nperseg=1024, noverlap=512,
        return_onesided=False)
    plt.figure(figsize=(12,5))
    plt.pcolormesh(
        t_sg,
        fftshift(f_sg)/1e3,
        10*np.log10(fftshift(Sxx, axes=0)+1e-10),
        shading="gouraud", cmap="viridis")
    plt.ylabel("Frequency (kHz)")
    plt.xlabel("Time (s)")
    plt.colorbar(label="dB")
    plt.ylim(-200, 200)
    plt.title("Spectrogram - Carrier Drift")
    plt.savefig("plots/spectrogram.png", dpi=150,
                bbox_inches="tight")
    plt.show()

# ============================================================
# STAGE II: CARRIER & TIMING RECOVERY
# ============================================================
def remove_carrier(s, fc, sample_rate=SAMPLE_RATE):
    """Remove carrier frequency - shift to baseband"""
    t = np.arange(len(s)) / sample_rate
    return s * np.exp(-1j * 2 * np.pi * fc * t)

def apply_filter(s, cutoff, sample_rate=SAMPLE_RATE):
    """Low pass filter to isolate signal"""
    b, a = butter(6, cutoff/(sample_rate/2), btype="low")
    return filtfilt(b, a, s.real) + 1j*filtfilt(b, a, s.imag)

def costas_loop(signal, sps, alpha=0.005, beta=0.001):
    """
    Costas loop for BPSK carrier phase recovery
    Tracks residual frequency offset after carrier removal
    """
    n   = len(signal)
    out = np.zeros(n, dtype=np.complex64)
    phase = 0.0
    freq  = 0.0
    for i in range(n):
        corrected = signal[i] * np.exp(-1j * phase)
        out[i]    = corrected
        error = np.sign(corrected.real) * corrected.imag
        freq  += beta  * error
        phase += freq  + alpha * error
    return out

# ============================================================
# STAGE III: DEMODULATION
# ============================================================
def confirm_bpsk(s, sample_rate=SAMPLE_RATE):
    """
    Confirm BPSK using 2nd power test
    BPSK: peak in 2nd power spectrum at 2x carrier
    """
    s2   = s**2
    f2   = fftfreq(len(s2), 1/sample_rate)
    p2   = np.abs(fft(s2))**2
    mask = (f2 > 0.85e6) & (f2 < 0.87e6)
    peak = f2[mask][np.argmax(p2[mask])]
    print(f"2nd power peak: {peak/1e6:.4f} MHz")
    print(f"Implied carrier: {peak/2/1e3:.4f} kHz")
    return peak / 2

def demodulate_bpsk(sc, sps_f=254.0):
    """Hard decision BPSK demodulation"""
    syms = [sc[int(i*sps_f)]
            for i in range(int(len(sc)/sps_f))]
    return "".join("1" if s.real > 0 else "0" for s in syms)

# ============================================================
# STAGE IV: CCSDS PAYLOAD RECOVERY
# ============================================================
def find_sync_marker(bits, max_errors=2):
    """Find CCSDS sync marker with error tolerance"""
    results = []
    for i in range(len(bits)-32):
        e = sum(a!=b for a,b in zip(bits[i:i+32], SYNC_MARKER))
        if e <= max_errors:
            results.append((i, e))
    return results

def parse_ccsds_header(data):
    """Parse CCSDS primary header (6 bytes)"""
    if len(data) < 6:
        return None
    h = data[:6]
    return {
        "version":   (h[0]>>5) & 0x07,
        "type":      (h[0]>>4) & 0x01,
        "sec_hdr":   (h[0]>>3) & 0x01,
        "apid":      ((h[0]&0x07)<<8) | h[1],
        "seq_flag":  (h[2]>>6) & 0x03,
        "seq_count": ((h[2]&0x3F)<<8) | h[3],
        "data_len":  (h[4]<<8) | h[5],
    }

def parse_secondary_header(data):
    """Parse CCSDS secondary header - timestamp"""
    if len(data) < 12:
        return None
    sh = data[6:12]
    return {
        "coarse_time": int.from_bytes(sh[:4], "big"),
        "fine_time":   int.from_bytes(sh[4:6], "big"),
    }

# ============================================================
# MAIN PIPELINE
# ============================================================
def main():
    os.makedirs("plots",  exist_ok=True)
    os.makedirs("output", exist_ok=True)

    print("="*60)
    print("VOYAGER-X SIGNAL RECOVERY PIPELINE")
    print("Team: HIzru Army | IIT ISM Dhanbad")
    print("="*60)

    # Stage 0: Find active files
    print("\nSTAGE 0: Data Reconstruction")
    active_files, peak_powers = find_active_files(DATA_FOLDER)

    # Stage I: Signal detection
    print("\nSTAGE I: Signal Detection")
    fname = active_files[30]
    s = read_iq_file(os.path.join(DATA_FOLDER, fname))
    fc = find_carrier(s)
    print(f"Carrier: {fc/1e3:.3f} kHz")
    plot_spectrogram(s)

    # Carrier drift across files
    carrier_freqs = []
    for f in active_files:
        seg = read_iq_file(os.path.join(DATA_FOLDER, f))
        carrier_freqs.append(find_carrier(seg))
    print(f"Carrier drift: {(max(carrier_freqs)-min(carrier_freqs))/1e3:.2f} kHz")

    # Stage II: Carrier recovery
    print("\nSTAGE II: Carrier & Timing Recovery")
    s_bb = remove_carrier(s, fc)
    sf   = apply_filter(s_bb, 4000)
    sc   = costas_loop(sf, 256)

    # Plot constellation
    fig, axes = plt.subplots(1, 2, figsize=(12,5))
    axes[0].scatter(s_bb.real[::10], s_bb.imag[::10],
                    s=0.5, alpha=0.3)
    axes[0].set_title("Before Costas Loop")
    axes[0].grid(True)
    axes[0].axis("equal")
    axes[1].scatter(sc.real[::10], sc.imag[::10],
                    s=0.5, alpha=0.3)
    axes[1].set_title("After Costas Loop")
    axes[1].grid(True)
    axes[1].axis("equal")
    plt.savefig("plots/constellation.png", dpi=150,
                bbox_inches="tight")
    plt.show()

    # Stage III: Demodulation
    print("\nSTAGE III: Demodulation")
    fc_precise = confirm_bpsk(s)
    print("Modulation: BPSK confirmed")

    # Stage IV: Payload recovery
    print("\nSTAGE IV: Payload Recovery")
    bits = demodulate_bpsk(sc)
    nrz  = "".join("1" if bits[i]!=bits[i-1] else "0"
                   for i in range(1, len(bits)))
    nrz_inv = "".join("1" if b=="0" else "0" for b in nrz)

    results = find_sync_marker(nrz_inv)
    if results:
        pos, err = results[0]
        print(f"Sync marker found at {pos} (errors={err})")

        p_bits = nrz_inv[pos+32:]
        payload = bytes(int(p_bits[i:i+8],2)
                       for i in range(0,len(p_bits)-8,8))

        header = parse_ccsds_header(payload)
        ts     = parse_secondary_header(payload)

        print(f"\nCCSDS Header:")
        for k,v in header.items():
            print(f"  {k}: {v}")

        if ts:
            import datetime
            dt = datetime.datetime.fromtimestamp(
                ts["coarse_time"])
            print(f"  Timestamp: {dt}")

        # Save payload
        with open("output/payload.bin","wb") as f:
            f.write(payload)
        print("\nPayload saved to output/payload.bin")
    else:
        print("Sync marker not found")

    print("\n" + "="*60)
    print("PIPELINE COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()
