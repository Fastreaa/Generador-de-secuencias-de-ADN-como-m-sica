import network
import urequests
import time
from machine import PWM, Pin

SSID     = ""
PASSWORD = ""
GENE_ID  = "NM_000207"

SCALE = [
    131, 147, 165, 175, 196, 220, 247,  # Do3..Si3
    262, 294, 330, 349, 392, 440, 494,  # Do4..Si4
    523, 587, 659, 698, 784, 880, 988,  # Do5..Si5
]

DURATIONS = {
    'A': 300,   
    'T': 150,   
    'G': 75,    
    'C': 225,   
}

STOP_CODONS = {'TAA', 'TAG', 'TGA'}

BASE_OCTAVA = {'A': 0, 'T': 7, 'G': 14, 'C': 14}
BASE_NOTA   = {'A': 0, 'T': 1, 'G': 2, 'C': 3}

BASE2 = {'A': 0, 'T': 2, 'G': 4, 'C': 6}

GAP_MS = 30

buzzer = PWM(Pin(0))

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    print("Conectando", end="")
    while not wlan.isconnected():
        print(".", end="")
        time.sleep(0.5)
    print(" OK →", wlan.ifconfig()[0])

def fetch_sequence(gene_id):
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        f"?db=nuccore&id={gene_id}&rettype=fasta&retmode=text"
    )
    print("Jalando secuencia...")
    r = urequests.get(url)
    raw = r.text
    r.close()
    seq = ''.join(
        l.strip().upper()
        for l in raw.split('\n')
        if not l.startswith('>')
    )
    print(f"Listo: {len(seq)} nt → {len(seq)//3} codones")
    return seq

def codon_to_sound(codon):
    if codon in STOP_CODONS:
        return None, 400  # silencio largo

    b1, b2, b3 = codon[0], codon[1], codon[2]

    # Si alguna base es ambigua (N, R, Y...) saltamos
    if b1 not in BASE_OCTAVE or b2 not in BASE2_OFFSET or b3 not in DURATIONS:
        return None, 0

    octave_start = BASE_OCTAVE[b1]
    note_offset  = BASE2_OFFSET[b2]
    freq_index   = octave_start + note_offset
    freq_index   = min(freq_index, len(SCALE) - 1)

    freq     = SCALE[freq_index]
    duration = DURATIONS[b3]

    return freq, duration

def play_sound(freq, duration_ms):
    if freq is None:
        buzzer.duty_u16(0)
        time.sleep_ms(duration_ms)
    else:
        buzzer.freq(freq)
        buzzer.duty_u16(32768)
        time.sleep_ms(duration_ms)
        buzzer.duty_u16(0)
    time.sleep_ms(GAP_MS)

connect_wifi()
sequence = fetch_sequence(GENE_ID)

codons = [sequence[i:i+3] for i in range(0, len(sequence)-2, 3)]

print(f"Tocando {len(codons)} codones... (Ctrl+C para parar)")
for i, codon in enumerate(codons):
    freq, dur = codon_to_sound(codon)
    play_sound(freq, dur)
    

    if i % 10 == 0:
        info = 'silencio' if freq is None else str(freq) + 'Hz ' + str(dur) + 'ms'
        print('  ' + codon + ' -> ' + info)

buzzer.deinit()
print("Fin de secuencia.")
