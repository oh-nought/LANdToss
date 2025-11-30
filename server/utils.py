import random
import socket

def generate_nickname():
    adjectives = ['Amused', 'Brave', 'Cloudy', 'Distinct', 'Calm', 'Clumsy', 'Dizzy', 'Eager', 'Happy', 'Funny', 'Kind', 'Lazy', 'Super', 'Wild']
    animals = ['Cat', 'Dog', 'Fish', 'Deer', 'Panda', 'Eagle', 'Fox', 'Tiger', 'Falcon', 'Lion']
    adj = random.choice(adjectives)
    animal = random.choice(animals)
    number = random.randint(10, 99)

    return f'{adj}{animal}{number}'

def get_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect(("8.8.8.8", 80))
    local_ip = sock.getsockname()[0]
    sock.close()
    return local_ip