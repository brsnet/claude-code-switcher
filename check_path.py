import os
print("Current file:", os.path.abspath(__file__))
print("Dirname:", os.path.dirname(os.path.abspath(__file__)))
print("Join dirname with '..', '.env':", os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))
print("Exists?", os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')))