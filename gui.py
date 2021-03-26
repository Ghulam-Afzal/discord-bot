import requests
import random

url = 'https://type.fit/api/quotes'

r = requests.get(url)

data = r.json()

# create a list of quotes from the api request and append any new quotes to the list
lst_of_quotes = []

for i in data:
    lst_of_quotes.append(i)

new_item = {
    'text': 'When I first met you, I honestly didnt know you were gonna be this important to me',
    'author': 'Souls'
}

lst_of_quotes.insert(0, new_item)


# generate a random number that is used to as the randomizer for teh quote
def generate_random_num():
    return random.randint(0, (len(lst_of_quotes) - 1))


# generate the quote
def generate_quote():
    random_index = generate_random_num()
    quote = f'"{lst_of_quotes[random_index]["text"]}" - {lst_of_quotes[random_index]["author"]}'
    return quote
