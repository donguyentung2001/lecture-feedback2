import random, string 
def generate_lectureID(): 
    lectureID = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8))
    return lectureID 

def generate_access_code(): 
    accessCode = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(7))
    return accessCode
