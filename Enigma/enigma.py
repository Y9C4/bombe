from machine import Enigma

with open("ciphered.txt", "r") as message:
    text = message.read().replace("\n", " ")


key = 'AAA' #AAA
swaps = None
rotor_order = ['I', 'II', 'III']

E = Enigma(key, swaps, rotor_order)

code = E.decipher(text)
print(code)
