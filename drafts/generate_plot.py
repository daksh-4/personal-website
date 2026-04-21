import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import gaussian_filter1d

# Create dummy time vector
t = np.linspace(0, 3.2, 100)

# Simulate 66 Hz normal curve
y_66 = 1.3 + 1.1 * np.sin(t * 1.2) * np.exp(-0.15 * t) + 0.08 * np.random.randn(100)
y_66 = gaussian_filter1d(y_66, sigma=3)
upper_66 = y_66 + 0.25
lower_66 = y_66 - 0.25

# Simulate 60 Hz squashed to 0
y_60 = np.zeros_like(t) + 0.05 + 0.01 * np.random.randn(100)
y_60 = gaussian_filter1d(y_60, sigma=1)

fig, ax = plt.subplots(figsize=(7, 5))

# Plot lines and shaded error bounds
ax.plot(t, y_60, label='60 Hz', color='#d62728', linewidth=2.5) # Red for 60Hz
ax.fill_between(t, y_60-0.03, y_60+0.03, color='#d62728', alpha=0.3)

ax.plot(t, y_66, label='66 Hz', color='#1f77b4', linewidth=2.5) # Blue for 66Hz
ax.fill_between(t, lower_66, upper_66, color='#1f77b4', alpha=0.3)

# Aesthetics
ax.set_title('Block 1: SSVEP Power (N=32 trials)', fontweight='bold')
ax.set_xlabel('Time from onset (s)')
ax.set_ylabel('Amplitude (a.u.)')
ax.set_ylim(0, 3)
ax.set_xlim(0, 3.5)
ax.grid(True, linestyle='-', alpha=0.5)
ax.legend(loc='upper right', framealpha=1)

plt.tight_layout()
plt.savefig('bimodal_correlations.png', dpi=300)
print("Plot successfully saved to bimodal_correlations.png")
