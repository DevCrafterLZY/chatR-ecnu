import requests

if __name__ == '__main__':
    try:
        response = requests.post('http://localhost:5000/login')
        print(response.text)
    except Exception as e:
        print("Error:", e)
