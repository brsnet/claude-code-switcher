with open('.env', 'rb') as f:
    for line in f:
        if b'NVIDIA_NIM_BASE_URL' in line:
            print("Raw line:", line)
            print("Decoded:", line.decode('utf-8', errors='replace'))