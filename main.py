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

cipher = Enigma( key, None, rotors)

#Create the Bombe Class:
class bombe:

    
    def __init__(self, code):
        self.code = code
        self.rotors = ['I', 'II', 'III']
        self.swaps = None
        self.key = 'AAA'
        self.decoder = Enigma(self.key, self.swaps, self.rotors)
    
    def try_rotors(self): #recursivley swap out each rotor to the unused rotor to see what the best setting is.
        rotor_perm = permutations(['I', 'II', 'III', 'V'], 3)
        max_ioc_config = (0, None)
        for perm in rotor_perm:
            self.decoder = Enigma(self.key, self.swaps, perm)
            ioc = index_of_coincidence(self.decoder.decipher(self.code))
            if ioc > max_ioc_config[0]:
                max_ioc_config = (ioc, perm)
                self.rotors = perm
        return max_ioc_config
    
#example use of this:
with open("Enigma/msg.txt", "r") as message:
    text = message.read().replace('\n', ' ')
    code = cipher.encipher(text)
    cracker = bombe(code)
    rotor_config = cracker.try_rotors()
    print(f"Max rotor config: {rotor_config}, real config: {rotors}")
    print(f"Semi-decoded message: {cracker.decoder.decipher(code)}")
        
        
        

    


        





