from collections import Counter

def index_of_coincidence(text):
    text = ''.join(filter(str.isalpha, text)).upper()
    
    n = len(text)
    
    if n < 2:
        return 0
    
    freqs = Counter(text)
    
    ic = sum(f * (f - 1) for f in freqs.values()) / (n * (n - 1))
    
    return ic

#example use
with open("Enigma/ciphered.txt", "r") as cipher:
    text = cipher.read()
ic = index_of_coincidence(text)
print(f"IoC: {ic}")
