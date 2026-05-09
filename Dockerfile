FROM python:3.10-slim

# Tizim paketlarini o'rnatish (FFmpeg va Rust compiler Shazam uchun)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    build-essential \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Rust-ni PATH-ga qo'shish
ENV PATH="/root/.cargo/bin:${PATH}"

# Ishchi katalogni belgilash
WORKDIR /app

# Kutubxonalarni o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Loyiha fayllarini ko'chirish
COPY . .

# Botni ishga tushirish
CMD ["python", "main.py"]
