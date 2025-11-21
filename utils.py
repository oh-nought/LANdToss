import random

def generate_nickname():
    adjectives = ['Amused', 'Brave', 'Cloudy', 'Distinct', 'Calm', 'Clumsy', 'Dizzy', 'Eager', 'Happy', 'Funny', 'Kind', 'Lazy', 'Super', 'Wild']
    animals = ['Cat', 'Dog', 'Fish', 'Deer', 'Panda', 'Eagle', 'Fox', 'Tiger', 'Falcon', 'Lion']
    adj = random.choice(adjectives)
    animal = random.choice(animals)
    number = random.randint(10, 99)

    return f'{adj}{animal}{number}'