from ioc import index_of_coincidence
from Enigma.machine import Enigma
import random, string
from itertools import permutations
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import re

def convert_numbers_to_words(text):
    """Convert numbers in text to spelled out words (e.g. '55' -> 'FIVEFIVE', '340' -> 'THREEFOURZERO')"""
    number_words = {
        '0': 'ZERO', '1': 'ONE', '2': 'TWO', '3': 'THREE', '4': 'FOUR',
        '5': 'FIVE', '6': 'SIX', '7': 'SEVEN', '8': 'EIGHT', '9': 'NINE'
    }
    
    def replace_number(match):
        number = match.group()
        return ''.join(number_words[digit] for digit in number)
    
    # Replace sequences of digits with spelled out words
    return re.sub(r'\d+', replace_number, text)

#generating the enigma machine
alphabet = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
random.shuffle(alphabet)

key = ''.join(random.choices(string.ascii_uppercase, k=3))
swaps = [(alphabet[i], alphabet[i+1]) for i in range(0, 6, 2)]
rotors = random.sample(['I', 'II', 'III', 'V'], 3)

Machine = Enigma(key, None, rotors)

with open('Enigma/msg.txt', 'r') as f:
    message = f.read().replace('\n', ' ').upper()
    # Convert numbers to words first
    message = convert_numbers_to_words(message)
    # Then remove spaces and keep only letters
    message = ''.join(char for char in message if char.isalpha())

# Print the machine configuration for debugging
print(f"=== ENIGMA MACHINE CONFIGURATION ===")
print(f"Key: {key}")
print(f"Rotors: {rotors}")
print(f"Message length: {len(message)} characters")
print(f"=====================================")

ciphertext = Machine.encipher(message)

print(f"=== TESTING CORRECT SETTINGS FIRST ===")
# Test if we can decode with the actual settings used
test_machine = Enigma(key, None, rotors)
test_decode = test_machine.decipher(ciphertext)
test_ioc = index_of_coincidence(test_decode)
print(f"Correct settings IoC: {test_ioc:.4f}")
print(f"Correct decode preview: {test_decode[:100]}...")
print(f"=========================================")

class Bombe:
    def __init__(self):
        self.best_rotor_config = None
        self.best_rotor_ioc = 0
        self.best_key = None
        self.best_key_ioc = 0
        self.best_decoded_text = None
        self.lock = threading.Lock()  # For thread-safe updates

    def test_rotor_config(self, rotor_permutation, ciphertext):
        """Test a single rotor configuration - thread-safe"""
        decode_machine = Enigma('AAA', None, rotor_permutation)
        decoded_text = decode_machine.decipher(ciphertext)
        ioc = index_of_coincidence(decoded_text)
        
        with self.lock:
            if ioc > self.best_rotor_ioc:
                self.best_rotor_config = rotor_permutation
                self.best_rotor_ioc = ioc
                print(f"Better rotor config found: {rotor_permutation}, IoC: {ioc:.4f}")
        
        return rotor_permutation, ioc

    def rotor_permutations_search(self, ciphertext, best_rotor_ioc):
        print("Starting multithreaded rotor permutation search...")
        rotor_configs = list(permutations(['I', 'II', 'III', 'V'], 3))
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(self.test_rotor_config, config, ciphertext) 
                      for config in rotor_configs]
            
            for future in as_completed(futures):
                future.result()  # Just to handle any exceptions
        
        print(f"Tested {len(rotor_configs)} rotor configurations. Best IoC: {self.best_rotor_ioc:.4f}")

    def generate_key_combinations(self):
        """Generate key combinations more efficiently"""
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        for l in alphabet:
            for m in alphabet:
                for r in alphabet:
                    yield l + m + r

    def test_key_chunk(self, key_chunk, ciphertext):
        """Test a chunk of keys - thread-safe"""
        local_best_ioc = 0
        local_best_key = None
        local_best_decoded = None
        
        for key in key_chunk:
            key_str = ''.join(key) if isinstance(key, tuple) else key
            decode_machine = Enigma(key_str, None, self.best_rotor_config)
            decoded_text = decode_machine.decipher(ciphertext)
            ioc = index_of_coincidence(decoded_text)
            
            if ioc > local_best_ioc:
                local_best_ioc = ioc
                local_best_key = key_str
                local_best_decoded = decoded_text
            
            # Early termination for excellent results
            if ioc > 0.065:
                with self.lock:
                    if ioc > self.best_key_ioc:
                        self.best_key = key_str
                        self.best_key_ioc = ioc
                        self.best_decoded_text = decoded_text
                        print(f"Excellent key found: {self.best_key} with IoC: {self.best_key_ioc:.4f}")
                return local_best_key, local_best_decoded, local_best_ioc
        
        # Update global best if this chunk found something better
        with self.lock:
            if local_best_ioc > self.best_key_ioc:
                self.best_key = local_best_key
                self.best_key_ioc = local_best_ioc
                self.best_decoded_text = local_best_decoded
        
        return local_best_key, local_best_decoded, local_best_ioc

    def key_position_search(self, ciphertext):
        print("Starting multithreaded key position search...")
        
        # Use generator instead of creating all permutations at once
        all_keys = list(self.generate_key_combinations())  # 17,576 combinations
        chunk_size = len(all_keys) // 8  # Split into 8 chunks
        key_chunks = [all_keys[i:i + chunk_size] for i in range(0, len(all_keys), chunk_size)]
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(self.test_key_chunk, chunk, ciphertext) 
                      for chunk in key_chunks]
            
            completed = 0
            for future in as_completed(futures):
                result = future.result()
                completed += 1
                print(f"Completed chunk {completed}/{len(key_chunks)}, current best IoC: {self.best_key_ioc:.4f}")
                
                # Early termination if we found a very good result
                if self.best_key_ioc > 0.065:
                    print(f"Excellent solution found early: {self.best_key} with IoC: {self.best_key_ioc:.4f}")
                    # Cancel remaining futures
                    for f in futures:
                        f.cancel()
                    break
        
        print(f"Key search completed. Best IoC: {self.best_key_ioc:.4f}")
        
        if self.best_key_ioc > 0.065:
            print(f"Possible key found: {self.best_key} with IoC: {self.best_key_ioc}")
            print(f"Decoded text: {self.best_decoded_text[:100]}...")
            return self.best_key, self.best_decoded_text
        
        return None

    def comprehensive_search(self, ciphertext):
        """More comprehensive search that tries all rotor-key combinations"""
        print("Starting comprehensive rotor + key search...")
        print(f"Will test all 24 rotor configurations with up to 5000 keys each")
        
        best_overall_ioc = 0
        best_overall_config = None
        
        rotor_configs = list(permutations(['I', 'II', 'III', 'V'], 3))
        
        for i, rotor_config in enumerate(rotor_configs):
            print(f"\nTesting rotor config {i+1}/{len(rotor_configs)}: {rotor_config}")
            
            # Reset for this rotor config
            local_best_ioc = 0
            local_best_key = None
            local_best_decoded = None
            
            # Test a sample of keys for this rotor config
            keys_tested = 0
            for key in self.generate_key_combinations():
                decode_machine = Enigma(key, None, rotor_config)
                decoded_text = decode_machine.decipher(ciphertext)
                ioc = index_of_coincidence(decoded_text)
                
                keys_tested += 1
                
                if ioc > local_best_ioc:
                    local_best_ioc = ioc
                    local_best_key = key
                    local_best_decoded = decoded_text
                    print(f"  New best for this rotor: Key={key}, IoC={ioc:.4f}")
                
                if ioc > best_overall_ioc:
                    best_overall_ioc = ioc
                    best_overall_config = (rotor_config, key, decoded_text)
                    print(f"  *** NEW OVERALL BEST: Rotors={rotor_config}, Key={key}, IoC={ioc:.4f} ***")
                    print(f"      Preview: {decoded_text[:50]}...")
                
                # Early exit for excellent results
                if ioc > 0.065:
                    print(f"  *** EXCELLENT RESULT FOUND! ***")
                    print(f"  Rotors: {rotor_config}, Key: {key}")
                    print(f"  IoC: {ioc:.4f}")
                    print(f"  Decoded: {decoded_text[:100]}...")
                    self.best_rotor_config = rotor_config
                    self.best_key = key
                    self.best_key_ioc = ioc
                    self.best_decoded_text = decoded_text
                    return True
                
                # Progress reporting
                if keys_tested % 1000 == 0:
                    print(f"  Tested {keys_tested} keys, best IoC for this rotor: {local_best_ioc:.4f}")
                
                # Limit keys per rotor to keep runtime reasonable
                if keys_tested >= 5000:
                    print(f"  Reached key limit for rotor {rotor_config}")
                    break
            
            print(f"  Completed {rotor_config}: tested {keys_tested} keys, best IoC={local_best_ioc:.4f}")
        
        if best_overall_config:
            rotor_config, key, decoded_text = best_overall_config
            self.best_rotor_config = rotor_config
            self.best_key = key
            self.best_key_ioc = best_overall_ioc
            self.best_decoded_text = decoded_text
            print(f"\nComprehensive search completed. Best overall IoC: {best_overall_ioc:.4f}")
            print(f"Best configuration: Rotors={rotor_config}, Key={key}")
            return best_overall_ioc > 0.06
        
        print("\nComprehensive search completed with no good results")
        return False
    
    def crib_attack(self, ciphertext):
        """Multithreaded crib attack - very computationally expensive"""
        print("Starting crib attack (this may take a long time)...")
        try:
            with open("cribs.csv") as f:
                cribs = f.read().splitlines()
                print(f"Loaded {len(cribs)} cribs from cribs.csv: {cribs}")
        except FileNotFoundError:
            print("cribs.csv not found, using default cribs")
            cribs = ["WETTER", "NOTHING", "HEIL", "OBERKOMMANDO"]
            print(f"Using default cribs: {cribs}")
        
        def test_crib_position(crib, position, ciphertext):
            print(f"  Testing crib '{crib}' at position {position}")
            ciphertext_segment = ciphertext[position:position + len(crib)]
            print(f"    Cipher segment: {ciphertext_segment}")
            
            rotor_count = 0
            key_count = 0
            
            for rotor_permutation in permutations(['I', 'II', 'III', 'V'], 3):
                rotor_count += 1
                if rotor_count % 8 == 0:  # Print every 8th rotor config
                    print(f"    Tested {rotor_count}/24 rotor configs for crib '{crib}' at pos {position}")
                
                for key in permutations('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 3):
                    key_count += 1
                    key_str = ''.join(key)
                    
                    # Print progress every 5000 keys
                    if key_count % 5000 == 0:
                        print(f"      Tested {key_count} keys for rotor {rotor_permutation}")
                    
                    decode_machine = Enigma(key_str, None, rotor_permutation)
                    decoded_segment = decode_machine.decipher(ciphertext_segment)
                    
                    if decoded_segment == crib:
                        print(f"    *** CRIB MATCH FOUND! ***")
                        print(f"      Crib: '{crib}' at position {position}")
                        print(f"      Rotor config: {rotor_permutation}")
                        print(f"      Key: {key_str}")
                        print(f"      Cipher segment: {ciphertext_segment}")
                        print(f"      Decoded segment: {decoded_segment}")
                        print(f"    Testing full message with these settings...")
                        
                        # Test full message with this configuration
                        full_machine = Enigma(key_str, None, rotor_permutation)
                        full_decoded = full_machine.decipher(ciphertext)
                        full_ioc = index_of_coincidence(full_decoded)
                        
                        print(f"      Full message IoC: {full_ioc:.4f}")
                        print(f"      Full decoded preview: {full_decoded[:50]}...")
                        
                        if full_ioc > 0.06:  # Promising result
                            print(f"    *** PROMISING FULL MESSAGE RESULT! ***")
                            return (rotor_permutation, key_str, crib, position, full_decoded, full_ioc)
                        else:
                            print(f"    Full message IoC too low ({full_ioc:.4f}), continuing search...")
                    
                    # Early exit after testing reasonable number of keys per rotor
                    if key_count >= 10000:  # Limit to prevent infinite loops
                        break
                
                key_count = 0  # Reset for next rotor
            
            print(f"  Completed testing crib '{crib}' at position {position} - no matches")
            return None
        
        print(f"Will test {len(cribs)} cribs across up to 50 positions each")
        total_tasks = 0
        
        # Test cribs with multithreading
        with ThreadPoolExecutor(max_workers=2) as executor:  # Use fewer workers for crib attack
            futures = []
            for crib in cribs:
                max_positions = min(50, len(ciphertext) - len(crib))
                print(f"Scheduling crib '{crib}' for {max_positions} positions")
                
                for position in range(max_positions):
                    future = executor.submit(test_crib_position, crib, position, ciphertext)
                    futures.append(future)
                    total_tasks += 1
            
            print(f"Total tasks scheduled: {total_tasks}")
            completed_tasks = 0
            
            for future in as_completed(futures):
                completed_tasks += 1
                print(f"Completed task {completed_tasks}/{total_tasks}")
                
                result = future.result()
                if result:
                    rotor_config, key, crib, pos, decoded, ioc = result
                    print(f"\n*** FINAL CRIB ATTACK SUCCESS! ***")
                    print(f"Crib match found: '{crib}' at position {pos}")
                    print(f"Rotor config: {rotor_config}, Key: {key}")
                    print(f"Full message IoC: {ioc:.4f}")
                    print(f"Decoded text: {decoded[:100]}...")
                    
                    # Update best results
                    with self.lock:
                        if ioc > self.best_key_ioc:
                            self.best_rotor_config = rotor_config
                            self.best_key = key
                            self.best_key_ioc = ioc
                            self.best_decoded_text = decoded
                    
                    # Cancel remaining futures
                    print("Cancelling remaining crib attack tasks...")
                    for f in futures:
                        f.cancel()
                    return result
                
                # Progress update every 10 completed tasks
                if completed_tasks % 10 == 0:
                    print(f"Progress: {completed_tasks}/{total_tasks} tasks completed, no matches yet...")
        
        print("Crib attack completed - no matches found")
        return None
    
    def validation(self):
        if self.best_key_ioc > 0.065:
            print("High IoC detected, likely success")
            print(f"Best key: {self.best_key}")
            print(f"Decoded text: {self.best_decoded_text[:100]}...")
        else:
            print("No valid key found, manual inspection needed")
                
if __name__ == "__main__":
    bombe = Bombe()
    
    print("\n=== STARTING BOMBE ATTACK ===")
    
    # Try comprehensive search first
    success = bombe.comprehensive_search(ciphertext)
    
    if not success:
        print("\nComprehensive search didn't find excellent results. Trying traditional approach...")
        
        # Fallback to traditional approach
        bombe.rotor_permutations_search(ciphertext, bombe.best_rotor_ioc)
        
        if bombe.best_rotor_config:
            result = bombe.key_position_search(ciphertext)
            if result:
                print("Key search successful!")
                success = True
            else:
                print("Key search unsuccessful, trying crib attack...")
                print("*** STARTING CRIB ATTACK - THIS WILL SHOW DETAILED PROGRESS ***")
                crib_result = bombe.crib_attack(ciphertext)
                if crib_result:
                    success = True
        else:
            print("No rotor configuration found, trying crib attack as last resort...")
            print("*** STARTING CRIB ATTACK - THIS WILL SHOW DETAILED PROGRESS ***")
            crib_result = bombe.crib_attack(ciphertext)
            if crib_result:
                success = True
    
    bombe.validation()
    
    print(f"\n=== FINAL RESULTS ===")
    if success:
        print("SUCCESS: Code appears to be cracked!")
    else:
        print("PARTIAL SUCCESS: Best attempt found")
    
    print(f"Final configuration:")
    print(f"  Rotors: {bombe.best_rotor_config}")
    print(f"  Key: {bombe.best_key}")
    print(f"  IoC: {bombe.best_key_ioc:.4f}")
    
    if bombe.best_decoded_text:
        print(f"\nDeciphered message:")
        print(f"{bombe.best_decoded_text}")
    else:
        print("No decoded text available.")

    


        


