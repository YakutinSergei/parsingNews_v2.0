import aiohttp
import asyncio
import os

async def download_file(session, url, dest):
    async with session.get(url) as response:
        total = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 1024
        with open(dest, "wb") as f:
            async for chunk in response.content.iter_chunked(chunk_size):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    percent = int(downloaded / total * 100)
                    print(f"[{os.path.basename(dest)}] {percent}%")
        print(f"[{os.path.basename(dest)}] загрузка завершена!")

async def main():
    urls = [
        "https://speed.hetzner.de/10MB.bin",
        "https://speed.hetzner.de/20MB.bin",
        "https://speed.hetzner.de/50MB.bin"
    ]
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i, url in enumerate(urls, start=1):
            dest = f"file_{i}.bin"
            tasks.append(download_file(session, url, dest))
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
