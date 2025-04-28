# bombe
Blind implementation of the Turing-Welchman Bombe to crack the enigma machine using turing machines.

Developed using no prior knowledge of the method used by the orignal Turing-Welchman Bombe, using Emily Willson's implementation of an enigma machine.

Turing machines designed in Tuatara and chained using java. No calculations done on higher level languages (i.e. all programming done through turing machines including simple math)

Project by Yajat Charpe 2025

LOGBOOK:
28/04: 

Setting up simulated enigma machine. Using Emily Willson's simulator found on https://github.com/NationalSecurityAgency/enigma-simulator.

The Enigma machine uses scrambles messages by using the plugboard and rotors. there are 4 rotors available: I, II, III, V, these rotors move every time a letter is pressed on a keyboard, ensuring that the same letter does not repeat and create an easily recognisable pattern. The plugboard and lampboard are used to make swaps on indivisual characters, which would be communicated every week. The enigma machine is set up inside /Engima and is historically accurate in its complexity, there are approximatley 1.95*10^8 different combinations.

While I started this project with the goal of implementing the bombe without any further knowledge, I am aware of certain information that is bound to make it easier. As described in a revelation in the Imitation Game, the Bombe tried to decode the message in parts instead of all at once. this meant that it made changes to the positions of the rotors or made swaps and tested the change in the Index of Coincidence. This index is particularly low when you have a message that is complete jibberish and random, and can be calculated by 1/n where N is the number of letters in the alphabet. for german, the IoC is ~0.067.

For today, my first order of business is to set up some code to calculate the Index of Coincidence of a string. I did this by using the formula IC=n(n−1)∑i​fi​(fi​−1)​ (replace in github). 

The approach I've decided upon is to ignore the rotor positions and try swapping the rotors to find the combination and order of rotors with the highest IoC. this will be done over an exponential time complexity over n=8: O(n^2)

Once I believe I have the correct rotor combination, i will being by moving the left most rotor through its entire revolution, then the rightmost, and then the middle until they are all in optimal positions indivisually. without changing these the positions of these rotors, i will repeat this step multiple times noting down the settings of the greatest IoC. 

This should make the message partiailly decrypted and easier to trial swaps on. I am unsure as to how I can trial swaps as there are 25^24 swaps that can be made. brute force likley isn't the solution.