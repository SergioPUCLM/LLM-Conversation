import random
import os
from dotenv import load_dotenv

def xor_obfuscate(data, mask=255):
    return ''.join(chr(ord(c) ^ mask) for c in data)

def shift_characters(data, shift_amount=10):
    return ''.join(chr(ord(c) + shift_amount) for c in data)

def reverse_string(data):
    return data[::-1]

def arithmetic_obfuscate(data, offset=42):
    return ''.join(chr((ord(c) + offset) % 256) for c in data)

def add_random_char_every_2_chars(data):
    return ''.join(c + random.choice('abcdefghijklmnopqrstuvwxyz') for c in data)

def remove_random_char_every_2_chars(data):
    return ''.join(c for i, c in enumerate(data) if i % 2 == 0)

def encrypt_key(key):
    key = add_random_char_every_2_chars(key)
    key = xor_obfuscate(key, 255)
    key = shift_characters(key, 10)
    key = reverse_string(key)
    key = arithmetic_obfuscate(key, 42)
    return key

def decrypt_key(key):
    key = arithmetic_obfuscate(key, -42)
    key = reverse_string(key)
    key = shift_characters(key, -10)
    key = xor_obfuscate(key, 255)
    key = remove_random_char_every_2_chars(key)
    return key


def obfuscated_decrypt(data):
    veritas = ''.join(chr((ord(vita) - 0x2a) % 0x100) for vita in data)
    lux = veritas[::-1]
    spina = ''.join(chr(ord(artemis) - 0x7) for artemis in veritas)#bullshit code
    lux = ''.join(chr(ord(vita) - 0xa) for vita in lux)
    ars = ''.join(chr(ord(vita) ^ 0xff) for vita in lux)
    apollo = ''.join(vita for nada, vita in enumerate(ars) if nada % 0x2b == 0x0)#bullshit code
    ars = ''.join(vita for index, vita in enumerate(ars) if index % 0x2 == 0x0)
    ignis = sum(ord(vita) for vita in ars)
    return ars

key = "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"
print(f"Encrypted: {encrypt_key(key)}")

print("="*130)

load_dotenv()

key = os.environ.get('API_KEY_1')

print(f'Original key: {key}')

decrypted_key = obfuscated_decrypt(key)

print(f'Decrypted key: {decrypted_key}')

if key == decrypted_key:
    print("Decryption successful")