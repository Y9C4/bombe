from ioc import index_of_coincidence
from Enigma.machine import Enigma
import random, string
from itertools import permutations

#generating the enigma machine
alphabet = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
random.shuffle(alphabet)

key = ''.join(random.choices(string.ascii_uppercase, k=3))
swaps = [(alphabet[i], alphabet[i+1]) for i in range(0, 6, 2)]
rotors = random.sample(['I', 'II', 'III', 'V'], 3)

Machine = Enigma(key, None, rotors)

with open('Enigma/msg.txt', 'r') as f:
    message = f.read().replace(' ', '').replace('\n', '').upper()
    # Remove numbers and keep only letters
    message = ''.join(char for char in message if char.isalpha())

ciphertext = Machine.encipher(message)

class Bombe:
    def __init__(self):
        self.best_rotor_config = None
        self.best_rotor_ioc = 0
        self.best_key = None
        self.best_key_ioc = 0
        self.best_decoded_text = None

    def rotor_permutations_search(self, ciphertext, best_rotor_ioc):
        print("Starting rotor permutation search...")
        count = 0
        for rotor_permutation in permutations(['I', 'II', 'III', 'V'], 3):
            count += 1
            decode_machine = Enigma('AAA', None, rotor_permutation)
            decoded_text = decode_machine.decipher(ciphertext)
            ioc = index_of_coincidence(decoded_text)
            if ioc > best_rotor_ioc:
                self.best_rotor_config = rotor_permutation
                self.best_rotor_ioc = ioc
                print(f"Better rotor config found: {rotor_permutation}, IoC: {ioc:.4f}")
        print(f"Tested {count} rotor configurations. Best IoC: {self.best_rotor_ioc:.4f}")

    def key_position_search(self, ciphertext):
        print("Starting key position search...")
        count = 0
        for key in permutations('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 3): #17,576 combinations
            count += 1
            decode_machine = Enigma(''.join(key), None, self.best_rotor_config)
            decoded_text = decode_machine.decipher(ciphertext)
            ioc = index_of_coincidence(decoded_text)
            if ioc > self.best_key_ioc:
                self.best_key = ''.join(key)
                self.best_key_ioc = ioc
                self.best_decoded_text = decoded_text
            
            if count % 1000 == 0:
                print(f"Tested {count} keys, best IoC so far: {self.best_key_ioc:.4f}")
            
            if ioc > 0.065:
                print(f"Possible key found: {self.best_key} with IoC: {self.best_key_ioc}")
                print(f"Decoded text: {self.best_decoded_text[:100]}...")
                return self.best_key, self.best_decoded_text
        
        print(f"Key search completed. Tested {count} keys. Best IoC: {self.best_key_ioc:.4f}")
        return None
    
    def crib_attack(self, ciphertext):
        with open("cribs.csv") as f:
            cribs = f.read().splitlines()
            for crib in cribs:
                for position in range(len(ciphertext) - len(crib)):
                    ciphertext_segment = ciphertext[position:position + len(crib)]

                    for rotor_permutation in permutations(['I', 'II', 'III', 'V'], 3):
                        for key in permutations('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 3):
                            decode_machine = Enigma(''.join(key), None, rotor_permutation)
                            decoded_segment = decode_machine.decipher(ciphertext_segment)
                            
                            if decoded_segment == crib:
                                print(f"Crib match found with rotor {rotor_permutation} and key {''.join(key)} at position {position}")
                                return rotor_permutation, ''.join(key), decoded_segment
    
    def validation(self):
        if self.best_key_ioc > 0.065:
            print("High IoC detected, likely success")
            print(f"Best key: {self.best_key}")
            print(f"Decoded text: {self.best_decoded_text[:100]}...")
        else:
            print("No valid key found, manual inspection needed")
                
if __name__ == "__main__":
    bombe = Bombe()
    bombe.rotor_permutations_search(ciphertext, bombe.best_rotor_ioc)
    
    # Only proceed with key search if we found a rotor configuration
    if bombe.best_rotor_config:
        result = bombe.key_position_search(ciphertext)
        if result:  # If key search found a good solution, skip crib attack
            print("Key search successful, skipping crib attack")
        else:
            print("Key search unsuccessful, but skipping crib attack for now...")
            # bombe.crib_attack(ciphertext)
    else:
        print("No rotor configuration found, but skipping crib attack for now...")
        # bombe.crib_attack(ciphertext)
    
    bombe.validation()
    
    print("Bombe process completed.")
    if bombe.best_decoded_text:
        print(f"Deciphered message: {bombe.best_decoded_text[:100]}...")
    else:
        print("No decoded text available.")

    


        


