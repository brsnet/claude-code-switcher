#!/usr/bin/env python3
import os
from dotenv import load_dotenv

print("=== Before loading .env ===")
print(f"NVIDIA_NIM_BASE_URL in os.environ: {os.environ.get('NVIDIA_NIM_BASE_URL', 'NOT SET')}")
print(f"NVIDIA_NIM_BASE_URL from os.getenv: {os.getenv('NVIDIA_NIM_BASE_URL', 'NOT SET')}")

print("\n=== Loading .env ===")
load_dotenv("D:/projetos/claude-code-switcher/.env")

print("=== After loading .env ===")
print(f"NVIDIA_NIM_BASE_URL in os.environ: {os.environ.get('NVIDIA_NIM_BASE_URL', 'NOT SET')}")
print(f"NVIDIA_NIM_BASE_URL from os.getenv: {os.getenv('NVIDIA_NIM_BASE_URL', 'NOT SET')}")

print("\n=== Checking .env file directly ===")
with open("D:/projetos/claude-code-switcher/.env", "r") as f:
    for line in f:
        if "NVIDIA_NIM_BASE_URL" in line:
            print(f".env line: {line.strip()}")
